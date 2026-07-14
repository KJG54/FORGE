"""Preliminary M1 successful closure and read-only archive inspection."""

from __future__ import annotations

import os
import shutil
import subprocess
from contextlib import suppress
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.archives import (
    ArchivedFile,
    ArchivedObjectReference,
    ArchiveManifest,
    ClosureRecord,
)
from forge.contracts.artifacts import ArtifactRevision
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.state import InitiativeLifecycleState, StepState
from forge.core.acceptance import AcceptanceView, list_acceptances
from forge.core.artifacts import list_artifacts, load_artifact_revision
from forge.core.authorization import require_owner
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.transitions import INITIATIVE_CLOSED
from forge.errors import (
    ConfigurationError,
    ConflictError,
    IntegrityError,
    SecurityError,
)
from forge.storage.configuration import load_configuration
from forge.storage.journal import read_journal
from forge.storage.objects import (
    canonical_json_digest,
    sha256_digest,
    verify_preserved_object,
)
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot

_MANIFEST_NAME = "archive-manifest.json"
_ZERO_DIGEST = f"sha256:{'0' * 64}"
_ACTIVE_TOP_LEVEL = {
    "acceptance",
    "artifacts",
    "checks",
    "claims",
    "closure",
    "decision-supersessions",
    "decisions",
    "events.jsonl",
    "evidence",
    "imported-results",
    "initiative.json",
    "pack-trust.json",
    "pack.lock.json",
    "revocations",
    "runs",
    "state.json",
    "workflow.lock.json",
}


@dataclass(frozen=True)
class ArchiveView:
    layout: RepositoryLayout
    active: ActiveInitiative
    closure: ClosureRecord
    manifest: ArchiveManifest
    events: tuple[AuditEvent, ...]


@dataclass(frozen=True)
class ClosureResult:
    closure: ClosureRecord
    event: AuditEvent
    archive: ArchiveView


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _archive_path(layout: RepositoryLayout, initiative_id: UUID) -> Path:
    return layout.archive_directory / str(initiative_id)


def _archive_layout(layout: RepositoryLayout, path: Path) -> RepositoryLayout:
    return replace(layout, active_directory=path)


def _closure_path(layout: RepositoryLayout, closure_id: UUID) -> Path:
    return layout.closure_directory / f"{closure_id}.json"


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def _require_clean_git(layout: RepositoryLayout) -> None:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=layout.root,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ConflictError(
            f"Cannot verify the configured clean-Git close policy: {error}"
        ) from error
    if completed.returncode != 0:
        diagnostic = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ConflictError(
            "Closure requires a clean Git worktree, but Git status failed"
            + (f": {diagnostic}" if diagnostic else "")
        )
    if completed.stdout.strip():
        raise ConflictError("Closure requires a clean Git worktree by project configuration")


def _final_acceptances(active: ActiveInitiative) -> tuple[AcceptanceView, ...]:
    available = list_acceptances(active.layout)
    selected: list[AcceptanceView] = []
    for step in active.workflow.steps:
        matches = [
            item
            for item in available
            if item.step_id == step.id and item.revocation is None and not item.stale
        ]
        if not matches:
            raise ConflictError(
                f"Workflow step {step.id!r} has no current owner acceptance for closure"
            )
        selected.append(max(matches, key=lambda item: item.acceptance.event_sequence))
    return tuple(selected)


def _preflight_closure(
    active: ActiveInitiative,
) -> tuple[tuple[AcceptanceView, ...], tuple[ArtifactRevision, ...]]:
    if active.state.lifecycle_state is not InitiativeLifecycleState.ACTIVE:
        raise ConflictError("Only an active initiative may close")
    incomplete = [
        step_id
        for step_id, state in active.state.step_states.items()
        if state is not StepState.COMPLETED
    ]
    if incomplete:
        raise ConflictError(
            f"Closure requires every workflow step to be completed: {sorted(incomplete)}"
        )
    if active.state.active_run_ids:
        raise ConflictError("Closure requires every governed run to be inactive")
    views = list_artifacts(active.layout)
    drifted = [str(item.current_revision.path) for item in views if not item.working_copy_matches]
    if drifted:
        raise ConflictError(
            "Closure requires exact current working bytes; register revisions for: "
            f"{sorted(drifted)}"
        )
    acceptances = _final_acceptances(active)
    revisions = tuple(
        sorted((item.current_revision for item in views), key=lambda item: str(item.id))
    )
    accepted_ids = {
        revision_id
        for view in acceptances
        for revision_id in view.acceptance.accepted_artifact_revision_ids
    }
    current_ids = {item.id for item in revisions}
    if not accepted_ids.issubset(current_ids):
        raise IntegrityError("Current closure acceptance references superseded artifact bytes")
    return acceptances, revisions


def _manifest_payload(manifest: ArchiveManifest) -> dict[str, object]:
    return manifest.model_dump(mode="json", exclude={"archive_digest"})


def _inventory(path: Path) -> tuple[ArchivedFile, ...]:
    if path.is_symlink() or not path.is_dir():
        raise SecurityError(f"Archive root is missing or is a symbolic link: {path}")
    files: list[ArchivedFile] = []
    for candidate in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
        if candidate.is_symlink():
            raise SecurityError(f"Archive contains a symbolic link: {candidate}")
        if candidate.is_dir():
            continue
        if not candidate.is_file():
            raise IntegrityError(f"Archive contains a non-regular entry: {candidate}")
        relative = candidate.relative_to(path).as_posix()
        if relative == _MANIFEST_NAME:
            continue
        try:
            content = candidate.read_bytes()
        except OSError as error:
            raise IntegrityError(f"Cannot read archived file {candidate}: {error}") from error
        files.append(
            ArchivedFile(
                path=relative,
                content_digest=sha256_digest(content),
                byte_size=len(content),
            )
        )
    return tuple(files)


def _copy_active_tree(source: Path, destination: Path) -> None:
    unexpected = {item.name for item in source.iterdir()} - _ACTIVE_TOP_LEVEL
    if unexpected:
        raise IntegrityError(
            f"Active governance directory contains unexpected closure content: {sorted(unexpected)}"
        )
    destination.mkdir()
    for candidate in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        if candidate.is_symlink():
            raise SecurityError(f"Refusing to archive a symbolic link: {candidate}")
        relative = candidate.relative_to(source)
        target = destination / relative
        if candidate.is_dir():
            target.mkdir()
        elif candidate.is_file():
            shutil.copyfile(candidate, target)
        else:
            raise IntegrityError(f"Active governance entry is not a regular file: {candidate}")


def _object_references(
    revisions: tuple[ArtifactRevision, ...],
    accepted_ids: set[UUID],
) -> tuple[ArchivedObjectReference, ...]:
    references: list[ArchivedObjectReference] = []
    for revision in revisions:
        if revision.preserved_object_path is None:
            raise IntegrityError(f"Artifact revision {revision.id} is not preserved")
        references.append(
            ArchivedObjectReference(
                artifact_revision_id=revision.id,
                content_digest=revision.content_digest,
                byte_size=revision.byte_size,
                preserved_object_path=revision.preserved_object_path,
                accepted=revision.id in accepted_ids,
            )
        )
    return tuple(sorted(references, key=lambda item: str(item.artifact_revision_id)))


def _build_manifest(
    active: ActiveInitiative,
    closure: ClosureRecord,
    path: Path,
) -> ArchiveManifest:
    revisions = tuple(
        load_artifact_revision(active.layout, revision_id)
        for revision_id in closure.current_artifact_revision_ids
    )
    manifest = ArchiveManifest(
        initiative_id=active.initiative.id,
        terminal_state=InitiativeLifecycleState.CLOSED,
        closure_record_id=closure.id,
        closure_event_id=closure.closure_event_id,
        created_at=utc_now(),
        files=_inventory(path),
        object_references=_object_references(
            revisions, set(closure.accepted_artifact_revision_ids)
        ),
        archive_digest=_ZERO_DIGEST,
    )
    return manifest.model_copy(
        update={"archive_digest": canonical_json_digest(_manifest_payload(manifest))}
    )


def _validate_archive_directory(
    layout: RepositoryLayout,
    path: Path,
    initiative_id: UUID,
) -> ArchiveView:
    manifest = load_record(path / _MANIFEST_NAME, ArchiveManifest)
    if canonical_json_digest(_manifest_payload(manifest)) != manifest.archive_digest:
        raise IntegrityError(f"Archive manifest digest is invalid: {path}")
    if manifest.files != _inventory(path):
        raise IntegrityError(f"Archive file inventory does not match its manifest: {path}")
    archived_layout = _archive_layout(layout, path)
    active = load_active_initiative(archived_layout, allow_terminal=True)
    if (
        active.initiative.id != initiative_id
        or active.state.lifecycle_state is not InitiativeLifecycleState.CLOSED
        or manifest.initiative_id != initiative_id
        or manifest.terminal_state is not InitiativeLifecycleState.CLOSED
    ):
        raise IntegrityError(f"Archive identity or terminal state is invalid: {path}")
    closure = load_record(
        archived_layout.closure_directory / f"{manifest.closure_record_id}.json",
        ClosureRecord,
    )
    if (
        closure.id != manifest.closure_record_id
        or closure.closure_event_id != manifest.closure_event_id
        or closure.archive_reference != f".forge/archive/{initiative_id}"
    ):
        raise IntegrityError(f"Archive manifest does not match its closure record: {path}")
    expected_references = _object_references(
        tuple(
            load_artifact_revision(archived_layout, revision_id)
            for revision_id in closure.current_artifact_revision_ids
        ),
        set(closure.accepted_artifact_revision_ids),
    )
    if manifest.object_references != expected_references:
        raise IntegrityError(f"Archive object references do not match closure records: {path}")
    for reference in manifest.object_references:
        verify_preserved_object(
            layout,
            repository_path=reference.preserved_object_path,
            expected_digest=reference.content_digest,
            expected_size=reference.byte_size,
        )
    events = read_journal(archived_layout.event_journal_file)
    if not events or events[-1].id != closure.closure_event_id:
        raise IntegrityError(f"Archive journal does not end at its closure event: {path}")
    return ArchiveView(archived_layout, active, closure, manifest, events)


def list_archive_ids(layout: RepositoryLayout) -> tuple[UUID, ...]:
    if layout.archive_directory.is_symlink() or not layout.archive_directory.is_dir():
        raise SecurityError(f"Archive directory is missing or unsafe: {layout.archive_directory}")
    identifiers: list[UUID] = []
    for candidate in layout.archive_directory.iterdir():
        if candidate.is_symlink() or not candidate.is_dir():
            raise IntegrityError(f"Archive root contains an unsafe entry: {candidate}")
        try:
            identifier = UUID(candidate.name)
        except ValueError as error:
            raise IntegrityError(
                f"Archive root contains an unrecognized directory: {candidate.name}"
            ) from error
        if str(identifier) != candidate.name:
            raise IntegrityError(f"Archive directory is not canonically named: {candidate.name}")
        identifiers.append(identifier)
    return tuple(sorted(identifiers, key=str))


def load_archive(layout: RepositoryLayout, initiative_id: UUID) -> ArchiveView:
    path = _archive_path(layout, initiative_id)
    if not path.exists():
        raise ConflictError(f"Unknown archived initiative {initiative_id}")
    return _validate_archive_directory(layout, path, initiative_id)


def close_initiative(
    layout: RepositoryLayout,
    *,
    closing_summary: str,
    actor: Actor,
) -> ClosureResult:
    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "close an initiative")
    closing_summary = _require_text("Closing summary", closing_summary)
    configuration = load_configuration(layout.configuration_file)
    if configuration.behavior.require_clean_git_for_close:
        _require_clean_git(layout)
    acceptances, revisions = _preflight_closure(active)
    destination = _archive_path(layout, active.initiative.id)
    if destination.exists() or destination.is_symlink():
        raise ConflictError(f"Archive destination already exists: {destination}")

    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    closure_id = uuid4()
    event_id = uuid4()
    final_acceptance_ids = tuple(item.acceptance.id for item in acceptances)
    current_revision_ids = tuple(item.id for item in revisions)
    accepted_revision_ids = tuple(
        sorted(
            {
                revision_id
                for item in acceptances
                for revision_id in item.acceptance.accepted_artifact_revision_ids
            },
            key=str,
        )
    )
    archive_reference = f".forge/archive/{active.initiative.id}"
    affected_ids = tuple(
        dict.fromkeys(
            (closure_id, *final_acceptance_ids, *current_revision_ids, *accepted_revision_ids)
        )
    )
    basis = "configured owner closed fully accepted work for preliminary M1 archival"
    closure = ClosureRecord(
        id=closure_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=affected_ids[1:],
        affected_digests=tuple(item.content_digest for item in revisions),
        owner_actor=actor,
        terminal_state=InitiativeLifecycleState.CLOSED,
        closure_event_id=event_id,
        closing_summary=closing_summary,
        final_acceptance_ids=final_acceptance_ids,
        current_artifact_revision_ids=current_revision_ids,
        accepted_artifact_revision_ids=accepted_revision_ids,
        archive_reference=archive_reference,
    )
    closure_digest = canonical_json_digest(closure.model_dump(mode="json"))
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=INITIATIVE_CLOSED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=affected_ids,
        affected_digests=tuple(
            dict.fromkeys((*closure.affected_digests, closure_digest))
        ),
        metadata={
            "closure_record_id": str(closure_id),
            "archive_reference": archive_reference,
            "final_acceptance_ids": [str(item) for item in final_acceptance_ids],
            "current_artifact_revision_ids": [str(item) for item in current_revision_ids],
            "accepted_artifact_revision_ids": [str(item) for item in accepted_revision_ids],
        },
    )
    created_closure_directory = False
    if not layout.closure_directory.exists():
        try:
            layout.closure_directory.mkdir()
        except OSError as error:
            raise IntegrityError(
                f"Cannot create closure record directory: {error}"
            ) from error
        created_closure_directory = True
    closure_path = _closure_path(layout, closure_id)
    try:
        write_record(closure_path, closure)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event_id):
            closure_path.unlink(missing_ok=True)
            if created_closure_directory:
                with suppress(OSError):
                    layout.closure_directory.rmdir()
        raise

    closed = load_active_initiative(layout, allow_terminal=True)
    staging = layout.archive_directory / f".{active.initiative.id}.{uuid4()}.staging"
    finalized = False
    try:
        _copy_active_tree(layout.active_directory, staging)
        manifest = _build_manifest(closed, closure, staging)
        write_record(staging / _MANIFEST_NAME, manifest)
        _validate_archive_directory(layout, staging, active.initiative.id)
        os.replace(staging, destination)
        finalized = True
        archive = load_archive(layout, active.initiative.id)
    except OSError as error:
        if not finalized and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise IntegrityError(
            f"Preliminary archive creation failed before active-state retirement: {error}"
        ) from error
    except Exception:
        if not finalized and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise

    retired = layout.local_directory / f"closed-active-{active.initiative.id}"
    if retired.exists():
        raise IntegrityError(f"Preliminary closure cleanup path already exists: {retired}")
    try:
        os.replace(layout.active_directory, retired)
        layout.active_directory.mkdir()
        shutil.rmtree(retired)
    except OSError as error:
        raise IntegrityError(
            "Archive was created but active-state retirement was interrupted; "
            "M2 recovery is required"
        ) from error
    return ClosureResult(closure, event, archive)
