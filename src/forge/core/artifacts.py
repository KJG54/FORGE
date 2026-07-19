"""Immutable artifact revisions and exact-byte preservation."""

from __future__ import annotations

import re
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision, ProvenanceRecord
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.successors import (
    load_predecessor_artifact_revision,
    predecessor_artifact_source_reference,
)
from forge.core.transitions import ARTIFACT_REGISTERED, ARTIFACT_REVISED, RESULT_IMPORTED
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.security.paths import normalize_repository_path, resolve_repository_path
from forge.security.secrets import screen_governed_content
from forge.storage.configuration import load_configuration
from forge.storage.journal import read_journal
from forge.storage.objects import PreservedObject, preserve_bytes, sha256_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class ArtifactMutationResult:
    artifact: ArtifactRecord
    revision: ArtifactRevision
    event: AuditEvent


@dataclass(frozen=True)
class ArtifactView:
    artifact: ArtifactRecord
    revisions: tuple[ArtifactRevision, ...]
    current_revision: ArtifactRevision
    working_copy_matches: bool


_SYMBOLIC_ID = re.compile(r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$")


def _validate_artifact_metadata(
    *,
    title: str,
    media_type: str | None,
    source_type: str,
    source_reference: str | None,
) -> None:
    if not title.strip():
        raise ConfigurationError("Artifact title must not be empty")
    if media_type is not None and not media_type.strip():
        raise ConfigurationError("Artifact media type must not be empty")
    if not _SYMBOLIC_ID.fullmatch(source_type.strip()):
        raise ConfigurationError(f"Invalid artifact provenance source type: {source_type!r}")
    if source_reference is not None and not source_reference.strip():
        raise ConfigurationError("Artifact provenance source reference must not be empty")


def _record_path(layout: RepositoryLayout, artifact_id: UUID, revision_number: int) -> Path:
    return layout.artifact_record_directory / f"{artifact_id}.{revision_number}.json"


def _revision_path(layout: RepositoryLayout, revision_id: UUID) -> Path:
    return layout.artifact_revision_directory / f"{revision_id}.json"


def _ensure_directory(path: Path, created: list[Path]) -> None:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Expected a governed directory at {path}")
        return
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create governed directory {path}: {error}") from error
    created.append(path)


def _ensure_artifact_directories(layout: RepositoryLayout) -> list[Path]:
    created: list[Path] = []
    try:
        _ensure_directory(layout.artifact_directory, created)
        _ensure_directory(layout.artifact_record_directory, created)
        _ensure_directory(layout.artifact_revision_directory, created)
    except Exception:
        _remove_empty_directories(created)
        raise
    return created


def _remove_empty_directories(paths: list[Path]) -> None:
    for path in reversed(paths):
        with suppress(OSError):
            path.rmdir()


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    if not layout.event_journal_file.exists():
        return False
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def _read_project_file(
    layout: RepositoryLayout,
    relative_path: str,
    *,
    max_bytes: int | None = None,
) -> tuple[str, bytes]:
    normalized = normalize_repository_path(relative_path)
    lexical = layout.root.joinpath(*normalized.split("/"))
    cursor = layout.root
    for part in normalized.split("/"):
        cursor /= part
        if cursor.is_symlink():
            raise SecurityError(f"Artifact path contains a symbolic link: {normalized}")
    resolved = resolve_repository_path(layout.root, normalized, must_exist=True)
    if lexical != resolved and lexical.resolve(strict=True) != resolved:
        raise SecurityError(f"Artifact path resolves through an unexpected alias: {normalized}")
    if not resolved.is_file():
        raise ConflictError(f"Artifact path is not a regular file: {normalized}")
    try:
        byte_size = resolved.stat().st_size
        if max_bytes is not None and byte_size > max_bytes:
            raise ConflictError(
                f"Artifact is {byte_size} bytes, exceeding the allowed preserved-object "
                f"limit of {max_bytes} bytes; split or reduce it before registration"
            )
        return normalized, resolved.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read artifact {normalized}: {error}") from error


def _preserve_project_file(
    layout: RepositoryLayout,
    relative_path: str,
) -> tuple[str, bytes, PreservedObject]:
    configuration = load_configuration(layout.configuration_file)
    normalized, content = _read_project_file(
        layout,
        relative_path,
        max_bytes=configuration.artifacts.max_preserved_object_bytes,
    )
    screen_governed_content(
        normalized,
        content,
        secret_path_patterns=configuration.security.secret_path_patterns,
    )
    preserved = preserve_bytes(
        layout,
        content,
        max_bytes=configuration.artifacts.max_preserved_object_bytes,
    )
    return normalized, content, preserved


def _current_record(active: ActiveInitiative, artifact_id: UUID) -> ArtifactRecord:
    revision_number = active.state.current_artifact_revisions.get(artifact_id)
    if revision_number is None:
        raise ConflictError(f"Unknown artifact {artifact_id}")
    return load_record(_record_path(active.layout, artifact_id, revision_number), ArtifactRecord)


def load_artifact_revision(layout: RepositoryLayout, revision_id: UUID) -> ArtifactRevision:
    return load_record(_revision_path(layout, revision_id), ArtifactRevision)


def _revisions_for_artifact(
    layout: RepositoryLayout,
    artifact_id: UUID,
    current_revision: int,
) -> tuple[ArtifactRevision, ...]:
    revisions: list[ArtifactRevision] = []
    for event in read_journal(layout.event_journal_file):
        if event.event_type == RESULT_IMPORTED:
            raw_updates = event.metadata.get("artifact_updates")
            if not isinstance(raw_updates, list):
                raise IntegrityError(f"Import event {event.id} lacks artifact updates")
            for raw_update in cast("list[object]", raw_updates):
                if not isinstance(raw_update, dict):
                    raise IntegrityError(f"Import event {event.id} has invalid artifact updates")
                update = cast("dict[object, object]", raw_update)
                if update.get("artifact_id") != str(artifact_id):
                    continue
                revision_value = update.get("revision_id")
                if not isinstance(revision_value, str):
                    raise IntegrityError(f"Import event {event.id} lacks a revision ID")
                try:
                    revisions.append(load_artifact_revision(layout, UUID(revision_value)))
                except ValueError as error:
                    raise IntegrityError(
                        f"Import event {event.id} has an invalid revision ID"
                    ) from error
            continue
        if event.event_type not in {ARTIFACT_REGISTERED, ARTIFACT_REVISED}:
            continue
        if event.metadata.get("artifact_id") != str(artifact_id):
            continue
        revision_value = event.metadata.get("revision_id")
        if not isinstance(revision_value, str):
            raise IntegrityError(f"Artifact event {event.id} lacks a revision ID")
        try:
            revision_id = UUID(revision_value)
        except ValueError as error:
            raise IntegrityError(f"Artifact event {event.id} has an invalid revision ID") from error
        revisions.append(load_artifact_revision(layout, revision_id))
    revisions.sort(key=lambda item: item.revision_number)
    expected = list(range(1, current_revision + 1))
    if [item.revision_number for item in revisions] != expected:
        raise IntegrityError(f"Artifact {artifact_id} revision history is not contiguous")
    return tuple(revisions)


def _working_copy_matches(layout: RepositoryLayout, revision: ArtifactRevision) -> bool:
    try:
        _, content = _read_project_file(
            layout,
            revision.path,
            max_bytes=revision.byte_size,
        )
    except (ConflictError, IntegrityError, SecurityError):
        return False
    return len(content) == revision.byte_size and sha256_digest(content) == revision.content_digest


def assert_working_revision_current(
    layout: RepositoryLayout,
    revision: ArtifactRevision,
) -> None:
    if not _working_copy_matches(layout, revision):
        raise ConflictError(
            f"Working file {revision.path!r} no longer matches artifact revision "
            f"{revision.artifact_id}@{revision.revision_number}; register an explicit revision"
        )


def list_artifacts(layout: RepositoryLayout) -> tuple[ArtifactView, ...]:
    active = load_active_initiative(
        layout,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    views: list[ArtifactView] = []
    for artifact_id, revision_number in sorted(
        active.state.current_artifact_revisions.items(), key=lambda item: str(item[0])
    ):
        record = _current_record(active, artifact_id)
        revisions = _revisions_for_artifact(layout, artifact_id, revision_number)
        views.append(
            ArtifactView(
                record,
                revisions,
                revisions[-1],
                _working_copy_matches(layout, revisions[-1]),
            )
        )
    return tuple(views)


def show_artifact(layout: RepositoryLayout, artifact_id: UUID) -> ArtifactView:
    views = list_artifacts(layout)
    view = next((item for item in views if item.artifact.id == artifact_id), None)
    if view is None:
        raise ConflictError(f"Unknown artifact {artifact_id}")
    return view


def current_revisions_for_roles(
    active: ActiveInitiative,
    roles: tuple[str, ...],
) -> tuple[ArtifactRevision, ...]:
    records = {
        artifact_id: _current_record(active, artifact_id)
        for artifact_id in active.state.current_artifact_revisions
    }
    missing = [
        role
        for role in roles
        if not any(record.role == role for record in records.values())
    ]
    if missing:
        raise ConflictError(f"Required artifact roles are not registered: {sorted(missing)}")
    revisions: list[ArtifactRevision] = []
    for artifact_id, record in records.items():
        if record.role not in roles:
            continue
        revision_number = active.state.current_artifact_revisions[artifact_id]
        revision = _revisions_for_artifact(active.layout, artifact_id, revision_number)[-1]
        assert_working_revision_current(active.layout, revision)
        revisions.append(revision)
    revisions.sort(key=lambda item: str(item.id))
    return tuple(revisions)


def add_artifact(
    layout: RepositoryLayout,
    *,
    path: str,
    role: str,
    title: str,
    actor: Actor,
    media_type: str = "application/octet-stream",
    source_type: str = "local-file",
    source_reference: str | None = None,
    predecessor_revision_id: UUID | None = None,
) -> ArtifactMutationResult:
    active = load_active_initiative(layout)
    _validate_artifact_metadata(
        title=title,
        media_type=media_type,
        source_type=source_type,
        source_reference=source_reference,
    )
    declared_roles = {
        output for step in active.workflow.steps for output in step.required_outputs
    } | set(active.workflow.required_artifact_classes)
    if role not in declared_roles:
        raise ConflictError(
            f"Artifact role {role!r} is not declared by the locked workflow"
        )
    predecessor_id: UUID | None = None
    predecessor_revision: ArtifactRevision | None = None
    if predecessor_revision_id is not None:
        predecessor_id, predecessor_revision = load_predecessor_artifact_revision(
            layout,
            active.initiative,
            predecessor_revision_id,
        )
        source_type = "predecessor-artifact"
        source_reference = predecessor_artifact_source_reference(
            predecessor_id,
            predecessor_revision_id,
        )
    normalized, content, preserved = _preserve_project_file(layout, path)
    if predecessor_revision is not None and (
        predecessor_revision.content_digest != preserved.digest
        or predecessor_revision.byte_size != len(content)
    ):
        if preserved.created:
            preserved.filesystem_path.unlink(missing_ok=True)
        raise ConflictError(
            "Working bytes do not match the selected predecessor artifact revision"
        )
    for view in list_artifacts(layout):
        if view.current_revision.path == normalized:
            if preserved.created:
                preserved.filesystem_path.unlink(missing_ok=True)
            raise ConflictError(
                f"Path {normalized!r} is already governed by artifact {view.artifact.id}"
            )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    artifact_id = uuid4()
    revision_id = uuid4()
    event_id = uuid4()
    provenance = ProvenanceRecord(
        id=uuid4(),
        source_type=source_type,
        source_reference=source_reference or normalized,
        actor_id=actor.id,
        recorded_at=now,
        metadata=(
            {
                "predecessor_initiative_id": str(predecessor_id),
                "predecessor_revision_id": str(predecessor_revision_id),
                "predecessor_content_digest": predecessor_revision.content_digest,
            }
            if predecessor_revision is not None
            else {}
        ),
    )
    basis = (
        "participant explicitly reused exact predecessor bytes as a new governed artifact"
        if predecessor_revision is not None
        else "participant registered an exact preserved project artifact revision"
    )
    predecessor_affected_ids = (
        (predecessor_revision_id,) if predecessor_revision_id is not None else ()
    )
    artifact = ArtifactRecord(
        id=artifact_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=(revision_id, *predecessor_affected_ids),
        affected_digests=(preserved.digest,),
        role=role,
        title=title,
        created_by=actor,
        current_revision=1,
    )
    revision = ArtifactRevision(
        id=revision_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=(artifact_id, *predecessor_affected_ids),
        affected_digests=(preserved.digest,),
        artifact_id=artifact_id,
        revision_number=1,
        path=normalized,
        content_digest=preserved.digest,
        byte_size=len(content),
        media_type=media_type,
        provenance=provenance,
        registration_event_id=event_id,
        preserved_object_path=preserved.repository_path,
        preservation_status="preserved",
    )
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=ARTIFACT_REGISTERED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(artifact_id, revision_id, *predecessor_affected_ids),
        affected_digests=(preserved.digest,),
        metadata={
            "artifact_id": str(artifact_id),
            "artifact_role": role,
            "revision_id": str(revision_id),
            "revision_number": 1,
            "predecessor_revision_id": (
                str(predecessor_revision_id)
                if predecessor_revision_id is not None
                else None
            ),
        },
    )
    created_directories: list[Path] = []
    paths = (_record_path(layout, artifact_id, 1), _revision_path(layout, revision_id))
    try:
        created_directories = _ensure_artifact_directories(layout)
        write_record(paths[0], artifact)
        write_record(paths[1], revision)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event_id):
            for record_path in reversed(paths):
                record_path.unlink(missing_ok=True)
            if preserved.created:
                preserved.filesystem_path.unlink(missing_ok=True)
            _remove_empty_directories(created_directories)
        raise
    return ArtifactMutationResult(artifact, revision, event)


def revise_artifact(
    layout: RepositoryLayout,
    *,
    artifact_id: UUID,
    path: str,
    actor: Actor,
    media_type: str | None = None,
    source_type: str = "local-file",
    source_reference: str | None = None,
) -> ArtifactMutationResult:
    active = load_active_initiative(layout)
    previous_record = _current_record(active, artifact_id)
    _validate_artifact_metadata(
        title=previous_record.title,
        media_type=media_type,
        source_type=source_type,
        source_reference=source_reference,
    )
    previous_number = active.state.current_artifact_revisions[artifact_id]
    previous_revision = _revisions_for_artifact(layout, artifact_id, previous_number)[-1]
    from forge.core.invalidation import calculate_artifact_revision_invalidation

    invalidation = calculate_artifact_revision_invalidation(active, previous_revision)
    normalized, content, preserved = _preserve_project_file(layout, path)
    for view in list_artifacts(layout):
        if view.artifact.id != artifact_id and view.current_revision.path == normalized:
            if preserved.created:
                preserved.filesystem_path.unlink(missing_ok=True)
            raise ConflictError(
                f"Path {normalized!r} is already governed by artifact {view.artifact.id}"
            )
    if preserved.digest == previous_revision.content_digest:
        if preserved.created:
            preserved.filesystem_path.unlink(missing_ok=True)
        raise ConflictError(
            "New artifact revision has the same content digest as the current revision"
        )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    revision_number = previous_number + 1
    revision_id = uuid4()
    event_id = uuid4()
    provenance = ProvenanceRecord(
        id=uuid4(),
        source_type=source_type,
        source_reference=source_reference or normalized,
        actor_id=actor.id,
        recorded_at=now,
    )
    basis = (
        "participant registered a new immutable artifact revision and FORGE propagated "
        "dependency staleness"
    )
    governed_effects = tuple(
        dict.fromkeys((previous_revision.id, revision_id, *invalidation.stale_record_ids))
    )
    artifact = ArtifactRecord(
        id=artifact_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=governed_effects,
        affected_digests=(previous_revision.content_digest, preserved.digest),
        role=previous_record.role,
        title=previous_record.title,
        created_by=previous_record.created_by,
        current_revision=revision_number,
    )
    revision = ArtifactRevision(
        id=revision_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=tuple(
            dict.fromkeys((artifact_id, previous_revision.id, *invalidation.stale_record_ids))
        ),
        affected_digests=(previous_revision.content_digest, preserved.digest),
        artifact_id=artifact_id,
        revision_number=revision_number,
        path=normalized,
        content_digest=preserved.digest,
        byte_size=len(content),
        media_type=media_type or previous_revision.media_type,
        provenance=provenance,
        registration_event_id=event_id,
        preserved_object_path=preserved.repository_path,
        preservation_status="preserved",
        superseded_revision_number=previous_number,
        stale_dependency_effects=invalidation.stale_record_ids,
    )
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=ARTIFACT_REVISED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=tuple(dict.fromkeys((artifact_id, *governed_effects))),
        affected_digests=(previous_revision.content_digest, preserved.digest),
        metadata={
            "artifact_id": str(artifact_id),
            "artifact_role": artifact.role,
            "revision_id": str(revision_id),
            "revision_number": revision_number,
            "superseded_revision_id": str(previous_revision.id),
            **invalidation.event_metadata(),
        },
    )
    created_directories: list[Path] = []
    paths = (
        _record_path(layout, artifact_id, revision_number),
        _revision_path(layout, revision_id),
    )
    try:
        created_directories = _ensure_artifact_directories(layout)
        write_record(paths[0], artifact)
        write_record(paths[1], revision)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event_id):
            for record_path in reversed(paths):
                record_path.unlink(missing_ok=True)
            if preserved.created:
                preserved.filesystem_path.unlink(missing_ok=True)
            _remove_empty_directories(created_directories)
        raise
    return ArtifactMutationResult(artifact, revision, event)
