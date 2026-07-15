"""Terminal decisions with resumable atomic archive promotion."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from contextlib import suppress
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.archives import (
    AbandonmentRecord,
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
from forge.core.transitions import INITIATIVE_ABANDONED, INITIATIVE_CLOSED
from forge.errors import (
    ConfigurationError,
    ConflictError,
    IntegrityError,
    SecurityError,
)
from forge.storage.atomic import sync_directory
from forge.storage.configuration import load_configuration
from forge.storage.idempotency import IDEMPOTENCY_METADATA_KEY, active_idempotency_request
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
_STAGING_NAME = re.compile(
    r"^\.(?P<initiative>[0-9a-f-]{36})\.(?P<event>[0-9a-f-]{36})\.staging$"
)
_ACTIVE_TOP_LEVEL = {
    "acceptance",
    "abandonment",
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
    "recovery-records",
    "recovery-snapshots",
    "runs",
    "state.json",
    "workflow.lock.json",
}


@dataclass(frozen=True)
class ArchiveView:
    layout: RepositoryLayout
    active: ActiveInitiative
    closure: ClosureRecord | None
    abandonment: AbandonmentRecord | None
    manifest: ArchiveManifest
    events: tuple[AuditEvent, ...]

    @property
    def terminal_record(self) -> TerminalRecord:
        record = self.closure if self.closure is not None else self.abandonment
        if record is None:
            raise IntegrityError("Archive has no terminal record")
        return record


@dataclass(frozen=True)
class ClosureResult:
    closure: ClosureRecord
    event: AuditEvent
    archive: ArchiveView


@dataclass(frozen=True)
class AbandonmentResult:
    abandonment: AbandonmentRecord
    event: AuditEvent
    archive: ArchiveView


TerminalRecord = ClosureRecord | AbandonmentRecord


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _archive_path(layout: RepositoryLayout, initiative_id: UUID) -> Path:
    return layout.archive_directory / str(initiative_id)


def _staging_path(layout: RepositoryLayout, initiative_id: UUID, event_id: UUID) -> Path:
    return layout.archive_directory / f".{initiative_id}.{event_id}.staging"


def _retired_path(
    layout: RepositoryLayout,
    initiative_id: UUID,
    terminal_state: InitiativeLifecycleState,
) -> Path:
    return layout.local_directory / f"{terminal_state.value}-active-{initiative_id}"


def _archive_layout(layout: RepositoryLayout, path: Path) -> RepositoryLayout:
    return replace(layout, active_directory=path)


def _closure_path(layout: RepositoryLayout, closure_id: UUID) -> Path:
    return layout.closure_directory / f"{closure_id}.json"


def _abandonment_path(layout: RepositoryLayout, abandonment_id: UUID) -> Path:
    return layout.abandonment_directory / f"{abandonment_id}.json"


def _terminal_event_id(record: TerminalRecord) -> UUID:
    if isinstance(record, ClosureRecord):
        return record.closure_event_id
    return record.abandonment_event_id


def _terminal_label(record: TerminalRecord) -> str:
    return "closure" if isinstance(record, ClosureRecord) else "abandonment"


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
            with target.open("r+b") as stream:
                os.fsync(stream.fileno())
        else:
            raise IntegrityError(f"Active governance entry is not a regular file: {candidate}")
    directories = sorted(
        (candidate for candidate in destination.rglob("*") if candidate.is_dir()),
        key=lambda item: len(item.parts),
        reverse=True,
    )
    for directory in (*directories, destination):
        sync_directory(directory)


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
    record: TerminalRecord,
    path: Path,
) -> ArchiveManifest:
    revisions = tuple(
        load_artifact_revision(active.layout, revision_id)
        for revision_id in record.current_artifact_revision_ids
    )
    accepted_ids: set[UUID] = (
        set(record.accepted_artifact_revision_ids)
        if isinstance(record, ClosureRecord)
        else set()
    )
    manifest = ArchiveManifest(
        initiative_id=active.initiative.id,
        terminal_state=record.terminal_state,
        closure_record_id=record.id if isinstance(record, ClosureRecord) else None,
        closure_event_id=(
            record.closure_event_id if isinstance(record, ClosureRecord) else None
        ),
        abandonment_record_id=(
            record.id if isinstance(record, AbandonmentRecord) else None
        ),
        abandonment_event_id=(
            record.abandonment_event_id
            if isinstance(record, AbandonmentRecord)
            else None
        ),
        created_at=utc_now(),
        files=_inventory(path),
        object_references=_object_references(revisions, accepted_ids),
        archive_digest=_ZERO_DIGEST,
        preliminary=False,
        limitations=(),
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
        or active.state.lifecycle_state is not manifest.terminal_state
        or manifest.initiative_id != initiative_id
        or manifest.terminal_state
        not in {InitiativeLifecycleState.CLOSED, InitiativeLifecycleState.ABANDONED}
    ):
        raise IntegrityError(f"Archive identity or terminal state is invalid: {path}")
    closure: ClosureRecord | None = None
    abandonment: AbandonmentRecord | None = None
    if manifest.terminal_state is InitiativeLifecycleState.CLOSED:
        assert manifest.closure_record_id is not None
        closure = load_record(
            archived_layout.closure_directory / f"{manifest.closure_record_id}.json",
            ClosureRecord,
        )
        record: TerminalRecord = closure
        if closure.closure_event_id != manifest.closure_event_id:
            raise IntegrityError(f"Archive manifest does not match its closure record: {path}")
        accepted_ids = set(closure.accepted_artifact_revision_ids)
    else:
        assert manifest.abandonment_record_id is not None
        abandonment = load_record(
            archived_layout.abandonment_directory
            / f"{manifest.abandonment_record_id}.json",
            AbandonmentRecord,
        )
        record = abandonment
        if abandonment.abandonment_event_id != manifest.abandonment_event_id:
            raise IntegrityError(
                f"Archive manifest does not match its abandonment record: {path}"
            )
        accepted_ids = set[UUID]()
    if (
        record.id
        not in {manifest.closure_record_id, manifest.abandonment_record_id}
        or record.archive_reference != f".forge/archive/{initiative_id}"
    ):
        raise IntegrityError(f"Archive manifest does not match its terminal record: {path}")
    expected_references = _object_references(
        tuple(
            load_artifact_revision(archived_layout, revision_id)
            for revision_id in record.current_artifact_revision_ids
        ),
        accepted_ids,
    )
    if manifest.object_references != expected_references:
        raise IntegrityError(f"Archive object references do not match terminal records: {path}")
    for reference in manifest.object_references:
        verify_preserved_object(
            layout,
            repository_path=reference.preserved_object_path,
            expected_digest=reference.content_digest,
            expected_size=reference.byte_size,
        )
    events = read_journal(archived_layout.event_journal_file)
    if not events or events[-1].id != _terminal_event_id(record):
        raise IntegrityError(f"Archive journal does not end at its terminal event: {path}")
    return ArchiveView(archived_layout, active, closure, abandonment, manifest, events)


def list_archive_ids(layout: RepositoryLayout) -> tuple[UUID, ...]:
    if layout.archive_directory.is_symlink() or not layout.archive_directory.is_dir():
        raise SecurityError(f"Archive directory is missing or unsafe: {layout.archive_directory}")
    identifiers: list[UUID] = []
    for candidate in layout.archive_directory.iterdir():
        if _STAGING_NAME.fullmatch(candidate.name):
            if candidate.is_symlink() or not candidate.is_dir():
                raise IntegrityError(f"Closure staging entry is unsafe: {candidate}")
            continue
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


def _validate_committed_closure(
    active: ActiveInitiative,
    closure: ClosureRecord,
    event: AuditEvent,
    *,
    closing_summary: str,
    actor: Actor,
) -> None:
    if (
        event.event_type != INITIATIVE_CLOSED
        or event.id != closure.closure_event_id
        or event.initiative_id != closure.initiative_id
        or event.sequence != closure.event_sequence
        or event.actor != actor
        or closure.owner_actor != actor
        or closure.closing_summary != closing_summary
        or closure.initiative_id != active.initiative.id
    ):
        raise IntegrityError("Committed closure does not match the requested owner decision")


def _closure_from_terminal_active(
    active: ActiveInitiative,
    *,
    closing_summary: str,
    actor: Actor,
) -> tuple[ClosureRecord, AuditEvent]:
    events = read_journal(active.layout.event_journal_file)
    if not events or events[-1].event_type != INITIATIVE_CLOSED:
        raise IntegrityError("Terminal active state does not end at a closure event")
    event = events[-1]
    raw_closure_id = event.metadata.get("closure_record_id")
    if not isinstance(raw_closure_id, str):
        raise IntegrityError("Closure event does not identify its closure record")
    try:
        closure_id = UUID(raw_closure_id)
    except ValueError as error:
        raise IntegrityError("Closure event has an invalid closure record ID") from error
    closure = load_record(_closure_path(active.layout, closure_id), ClosureRecord)
    _validate_committed_closure(
        active,
        closure,
        event,
        closing_summary=closing_summary,
        actor=actor,
    )
    return closure, event


def _archive_matches_active_request(archive: ArchiveView) -> bool:
    request = active_idempotency_request()
    if request is None:
        return _retired_path(
            archive.layout,
            archive.active.initiative.id,
            archive.manifest.terminal_state,
        ).exists()
    raw = archive.events[-1].metadata.get(IDEMPOTENCY_METADATA_KEY)
    return raw == request.model_dump(mode="json")


def _closure_from_interrupted_retirement(
    layout: RepositoryLayout,
    *,
    closing_summary: str,
    actor: Actor,
) -> tuple[ClosureRecord, AuditEvent] | None:
    matches: list[tuple[ClosureRecord, AuditEvent]] = []
    for initiative_id in list_archive_ids(layout):
        archive = load_archive(layout, initiative_id)
        if not _archive_matches_active_request(archive):
            continue
        closure = archive.closure
        if closure is None:
            continue
        event = archive.events[-1]
        if (
            closure.closing_summary == closing_summary
            and closure.owner_actor == actor
            and event.actor == actor
        ):
            matches.append((closure, event))
    if len(matches) > 1:
        raise IntegrityError("Closure retry matches more than one archived initiative")
    return matches[0] if matches else None


def _validate_committed_abandonment(
    active: ActiveInitiative,
    abandonment: AbandonmentRecord,
    event: AuditEvent,
    *,
    reason: str,
    unfinished_work_summary: str,
    unresolved_risks: tuple[str, ...],
    actor: Actor,
) -> None:
    if (
        event.event_type != INITIATIVE_ABANDONED
        or event.id != abandonment.abandonment_event_id
        or event.initiative_id != abandonment.initiative_id
        or event.sequence != abandonment.event_sequence
        or event.actor != actor
        or abandonment.owner_actor != actor
        or abandonment.reason != reason
        or abandonment.unfinished_work_summary != unfinished_work_summary
        or abandonment.unresolved_risks != unresolved_risks
        or abandonment.initiative_id != active.initiative.id
    ):
        raise IntegrityError("Committed abandonment does not match the requested owner decision")


def _abandonment_from_terminal_active(
    active: ActiveInitiative,
    *,
    reason: str,
    unfinished_work_summary: str,
    unresolved_risks: tuple[str, ...],
    actor: Actor,
) -> tuple[AbandonmentRecord, AuditEvent]:
    events = read_journal(active.layout.event_journal_file)
    if not events or events[-1].event_type != INITIATIVE_ABANDONED:
        raise IntegrityError("Terminal active state does not end at an abandonment event")
    event = events[-1]
    raw_record_id = event.metadata.get("abandonment_record_id")
    if not isinstance(raw_record_id, str):
        raise IntegrityError("Abandonment event does not identify its record")
    try:
        record_id = UUID(raw_record_id)
    except ValueError as error:
        raise IntegrityError("Abandonment event has an invalid record ID") from error
    abandonment = load_record(
        _abandonment_path(active.layout, record_id), AbandonmentRecord
    )
    _validate_committed_abandonment(
        active,
        abandonment,
        event,
        reason=reason,
        unfinished_work_summary=unfinished_work_summary,
        unresolved_risks=unresolved_risks,
        actor=actor,
    )
    return abandonment, event


def _abandonment_from_interrupted_retirement(
    layout: RepositoryLayout,
    *,
    reason: str,
    unfinished_work_summary: str,
    unresolved_risks: tuple[str, ...],
    actor: Actor,
) -> tuple[AbandonmentRecord, AuditEvent] | None:
    matches: list[tuple[AbandonmentRecord, AuditEvent]] = []
    for initiative_id in list_archive_ids(layout):
        archive = load_archive(layout, initiative_id)
        if not _archive_matches_active_request(archive):
            continue
        abandonment = archive.abandonment
        if abandonment is None:
            continue
        event = archive.events[-1]
        if (
            abandonment.reason == reason
            and abandonment.unfinished_work_summary == unfinished_work_summary
            and abandonment.unresolved_risks == unresolved_risks
            and abandonment.owner_actor == actor
            and event.actor == actor
        ):
            matches.append((abandonment, event))
    if len(matches) > 1:
        raise IntegrityError("Abandonment retry matches more than one archived initiative")
    return matches[0] if matches else None


def _remove_staging(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise SecurityError(f"Closure staging path is unsafe: {path}")
    try:
        shutil.rmtree(path)
    except OSError as error:
        raise IntegrityError(f"Cannot clear interrupted closure staging: {error}") from error


def _promote_archive(
    layout: RepositoryLayout,
    active: ActiveInitiative | None,
    record: TerminalRecord,
    event: AuditEvent,
) -> ArchiveView:
    label = _terminal_label(record)
    destination = _archive_path(layout, record.initiative_id)
    staging = _staging_path(layout, record.initiative_id, event.id)
    if destination.exists() or destination.is_symlink():
        archive = load_archive(layout, record.initiative_id)
        if (
            archive.terminal_record != record
            or archive.events[-1].id != event.id
            or archive.manifest.preliminary
        ):
            raise IntegrityError(
                f"Existing archive does not match the hardened {label} transaction"
            )
        if staging.exists() or staging.is_symlink():
            _remove_staging(staging)
        return archive
    if active is None:
        raise IntegrityError(
            f"{label.title()} event is committed but neither its archive nor terminal active "
            "state exists"
        )
    if staging.exists() or staging.is_symlink():
        _remove_staging(staging)
    try:
        _copy_active_tree(active.layout.active_directory, staging)
        manifest = _build_manifest(active, record, staging)
        write_record(staging / _MANIFEST_NAME, manifest)
        candidate = _validate_archive_directory(layout, staging, record.initiative_id)
        if candidate.terminal_record != record or candidate.events[-1].id != event.id:
            raise IntegrityError(f"{label.title()} staging does not match the committed decision")
        sync_directory(staging)
        os.replace(staging, destination)
        sync_directory(layout.archive_directory)
    except OSError as error:
        raise IntegrityError(
            f"Atomic archive promotion was interrupted; retry 'forge {label}' with the same "
            f"idempotency key: {error}"
        ) from error
    archive = load_archive(layout, record.initiative_id)
    if archive.manifest.preliminary:
        raise IntegrityError(f"New {label} unexpectedly produced a preliminary archive")
    return archive


def _validate_terminal_tree(
    layout: RepositoryLayout,
    path: Path,
    record: TerminalRecord,
    event: AuditEvent,
) -> None:
    if path.is_symlink() or not path.is_dir():
        raise SecurityError(f"Terminal active-state path is unsafe: {path}")
    terminal_layout = _archive_layout(layout, path)
    terminal = load_active_initiative(terminal_layout, allow_terminal=True)
    events = read_journal(terminal_layout.event_journal_file)
    if (
        terminal.initiative.id != record.initiative_id
        or terminal.state.lifecycle_state is not record.terminal_state
        or not events
        or events[-1].id != event.id
    ):
        raise IntegrityError("Retired active state does not match the committed terminal decision")


def _retire_active_state(
    layout: RepositoryLayout,
    record: TerminalRecord,
    event: AuditEvent,
) -> None:
    label = _terminal_label(record)
    active = layout.active_directory
    retired = _retired_path(layout, record.initiative_id, record.terminal_state)
    if retired.exists() or retired.is_symlink():
        _validate_terminal_tree(layout, retired, record, event)
    if active.exists() or active.is_symlink():
        if active.is_symlink() or not active.is_dir():
            raise SecurityError(f"Active governance path is unsafe: {active}")
        contents = tuple(active.iterdir())
        if contents:
            _validate_terminal_tree(layout, active, record, event)
            if retired.exists() or retired.is_symlink():
                raise IntegrityError("Both active and retired terminal state contain records")
            try:
                os.replace(active, retired)
                sync_directory(layout.forge_directory)
                sync_directory(layout.local_directory)
            except OSError as error:
                raise IntegrityError(
                    f"Active-state retirement was interrupted; retry 'forge {label}' with the "
                    f"same idempotency key: {error}"
                ) from error
        elif not retired.exists():
            return
    if retired.exists() or retired.is_symlink():
        _validate_terminal_tree(layout, retired, record, event)
    try:
        if not active.exists():
            active.mkdir()
            sync_directory(layout.forge_directory)
        if retired.exists():
            shutil.rmtree(retired)
            sync_directory(layout.local_directory)
    except OSError as error:
        raise IntegrityError(
            f"Active-state retirement was interrupted; retry 'forge {label}' with the same "
            f"idempotency key: {error}"
        ) from error


def _finalize_committed_closure(
    layout: RepositoryLayout,
    active: ActiveInitiative | None,
    closure: ClosureRecord,
    event: AuditEvent,
) -> ClosureResult:
    archive = _promote_archive(layout, active, closure, event)
    _retire_active_state(layout, closure, event)
    return ClosureResult(closure, event, archive)


def _finalize_committed_abandonment(
    layout: RepositoryLayout,
    active: ActiveInitiative | None,
    abandonment: AbandonmentRecord,
    event: AuditEvent,
) -> AbandonmentResult:
    archive = _promote_archive(layout, active, abandonment, event)
    _retire_active_state(layout, abandonment, event)
    return AbandonmentResult(abandonment, event, archive)


def close_initiative(
    layout: RepositoryLayout,
    *,
    closing_summary: str,
    actor: Actor,
) -> ClosureResult:
    closing_summary = _require_text("Closing summary", closing_summary)
    active: ActiveInitiative | None = None
    if layout.initiative_file.exists():
        active = load_active_initiative(
            layout,
            allow_terminal=True,
            allow_paused=True,
        )
        if active.state.lifecycle_state is InitiativeLifecycleState.CLOSED:
            require_owner(actor, active.initiative.owner_identity_id, "recover closure")
            closure, event = _closure_from_terminal_active(
                active,
                closing_summary=closing_summary,
                actor=actor,
            )
            return _finalize_committed_closure(layout, active, closure, event)
    else:
        interrupted = _closure_from_interrupted_retirement(
            layout,
            closing_summary=closing_summary,
            actor=actor,
        )
        if interrupted is not None:
            closure, event = interrupted
            return _finalize_committed_closure(layout, None, closure, event)
        raise ConflictError("No active initiative exists; run 'forge create' first")
    require_owner(actor, active.initiative.owner_identity_id, "close an initiative")
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
    basis = "configured owner closed fully accepted work for atomic M2 archival"
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
            "archive_guarantee": "atomic-m2-resumable",
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
    return _finalize_committed_closure(layout, closed, closure, event)


def abandon_initiative(
    layout: RepositoryLayout,
    *,
    reason: str,
    unfinished_work_summary: str,
    unresolved_risks: tuple[str, ...],
    actor: Actor,
) -> AbandonmentResult:
    reason = _require_text("Abandonment reason", reason)
    unfinished_work_summary = _require_text(
        "Unfinished work summary", unfinished_work_summary
    )
    unresolved_risks = tuple(
        _require_text("Unresolved risk", item) for item in unresolved_risks
    )
    if not unresolved_risks:
        raise ConfigurationError("At least one unresolved risk statement is required")

    active: ActiveInitiative | None = None
    if layout.initiative_file.exists():
        active = load_active_initiative(layout, allow_terminal=True, allow_paused=True)
        if active.state.lifecycle_state is InitiativeLifecycleState.ABANDONED:
            require_owner(actor, active.initiative.owner_identity_id, "recover abandonment")
            abandonment, event = _abandonment_from_terminal_active(
                active,
                reason=reason,
                unfinished_work_summary=unfinished_work_summary,
                unresolved_risks=unresolved_risks,
                actor=actor,
            )
            return _finalize_committed_abandonment(layout, active, abandonment, event)
    else:
        interrupted = _abandonment_from_interrupted_retirement(
            layout,
            reason=reason,
            unfinished_work_summary=unfinished_work_summary,
            unresolved_risks=unresolved_risks,
            actor=actor,
        )
        if interrupted is not None:
            abandonment, event = interrupted
            return _finalize_committed_abandonment(layout, None, abandonment, event)
        raise ConflictError("No active initiative exists; run 'forge create' first")

    require_owner(actor, active.initiative.owner_identity_id, "abandon an initiative")
    if active.state.lifecycle_state not in {
        InitiativeLifecycleState.ACTIVE,
        InitiativeLifecycleState.PAUSED,
    }:
        raise ConflictError("Only an active or paused initiative may be abandoned")
    if active.state.active_run_ids:
        raise ConflictError(
            "Abandonment requires every governed run to be inactive; cancel active runs first"
        )
    destination = _archive_path(layout, active.initiative.id)
    if destination.exists() or destination.is_symlink():
        raise ConflictError(f"Archive destination already exists: {destination}")

    revisions = tuple(
        sorted(
            (item.current_revision for item in list_artifacts(active.layout)),
            key=lambda item: str(item.id),
        )
    )
    unfinished_step_ids = tuple(
        step.id
        for step in active.workflow.steps
        if active.state.step_states[step.id] is not StepState.COMPLETED
    )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    abandonment_id = uuid4()
    event_id = uuid4()
    current_revision_ids = tuple(item.id for item in revisions)
    archive_reference = f".forge/archive/{active.initiative.id}"
    affected_ids = (abandonment_id, *current_revision_ids)
    basis = "configured owner abandoned unfinished work for atomic M2 archival"
    abandonment = AbandonmentRecord(
        id=abandonment_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=current_revision_ids,
        affected_digests=tuple(item.content_digest for item in revisions),
        owner_actor=actor,
        terminal_state=InitiativeLifecycleState.ABANDONED,
        abandonment_event_id=event_id,
        reason=reason,
        unfinished_work_summary=unfinished_work_summary,
        unresolved_risks=unresolved_risks,
        unfinished_step_ids=unfinished_step_ids,
        current_artifact_revision_ids=current_revision_ids,
        archive_reference=archive_reference,
    )
    record_digest = canonical_json_digest(abandonment.model_dump(mode="json"))
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=INITIATIVE_ABANDONED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=affected_ids,
        affected_digests=tuple(
            dict.fromkeys((*abandonment.affected_digests, record_digest))
        ),
        metadata={
            "abandonment_record_id": str(abandonment_id),
            "archive_reference": archive_reference,
            "reason": reason,
            "unfinished_work_summary": unfinished_work_summary,
            "unresolved_risks": list(unresolved_risks),
            "unfinished_step_ids": list(unfinished_step_ids),
            "current_artifact_revision_ids": [str(item) for item in current_revision_ids],
            "archive_guarantee": "atomic-m2-resumable",
        },
    )
    created_directory = False
    if not layout.abandonment_directory.exists():
        try:
            layout.abandonment_directory.mkdir()
        except OSError as error:
            raise IntegrityError(
                f"Cannot create abandonment record directory: {error}"
            ) from error
        created_directory = True
    record_path = _abandonment_path(layout, abandonment_id)
    try:
        write_record(record_path, abandonment)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event_id):
            record_path.unlink(missing_ok=True)
            if created_directory:
                with suppress(OSError):
                    layout.abandonment_directory.rmdir()
        raise

    abandoned = load_active_initiative(layout, allow_terminal=True)
    return _finalize_committed_abandonment(layout, abandoned, abandonment, event)
