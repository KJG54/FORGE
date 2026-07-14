"""Previewed, collision-explicit registration of staged untrusted results."""

from __future__ import annotations

import re
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision, ProvenanceRecord
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.runs import RunRecord
from forge.contracts.state import StepState
from forge.core.artifacts import ArtifactView, list_artifacts
from forge.core.handoffs import load_handoff
from forge.core.invalidation import DependencyInvalidation, calculate_artifact_revision_invalidation
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.transitions import RESULT_IMPORTED
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.security.imports import StagedResult, resolve_import_target, stage_result
from forge.security.paths import normalize_repository_path
from forge.storage.atomic import atomic_write_bytes
from forge.storage.configuration import load_configuration
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest, preserve_bytes, sha256_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot

_SYMBOLIC_ID = re.compile(r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$")


@dataclass(frozen=True)
class ImportAction:
    source_path: str
    target_path: str
    action: str
    role: str | None
    artifact_id: UUID | None
    digest: str
    byte_size: int
    media_type: str
    prior_target_digest: str | None
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImportPreview:
    staged: StagedResult
    step_id: str
    source_run_id: UUID | None
    journal_sequence: int
    actions: tuple[ImportAction, ...]
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ImportedResult:
    preview: ImportPreview
    event: AuditEvent
    artifacts: tuple[ArtifactRecord, ...]
    revisions: tuple[ArtifactRevision, ...]


def _normalize_assignments(values: dict[str, str], label: str) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for raw_path, raw_value in values.items():
        path = normalize_repository_path(raw_path)
        value = raw_value.strip()
        if not value:
            raise ConfigurationError(f"{label} value for {path!r} must not be empty")
        if path in normalized:
            raise ConfigurationError(f"Duplicate {label} assignment for {path!r}")
        normalized[path] = value
    return normalized


def _source_step(
    active: ActiveInitiative,
    source_id: UUID,
) -> tuple[str, UUID | None]:
    run_path = active.layout.governed_run_directory / f"{source_id}.json"
    if run_path.exists():
        run = load_record(run_path, RunRecord)
        if run.initiative_id != active.initiative.id:
            raise IntegrityError(f"Source run {source_id} belongs to another initiative")
        return run.step_id, run.id
    handoff_path = active.layout.handoff_directory / str(source_id) / "handoff.json"
    if handoff_path.exists():
        handoff = load_handoff(active.layout, source_id)
        if handoff.initiative_id != active.initiative.id:
            raise IntegrityError(f"Source handoff {source_id} belongs to another initiative")
        return handoff.step_id, None
    raise ConflictError(
        f"Result source {source_id} is neither a governed run nor a current manual handoff"
    )


def _target_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_symlink():
        raise SecurityError(f"Import target is a symbolic link: {path}")
    if not path.is_file():
        raise ConflictError(f"Import target is not a regular file: {path}")
    try:
        return sha256_digest(path.read_bytes())
    except OSError as error:
        raise IntegrityError(f"Cannot read import target {path}: {error}") from error


def preview_result_import(
    layout: RepositoryLayout,
    *,
    manifest_path: Path,
    role_assignments: dict[str, str] | None = None,
    collision_actions: dict[str, str] | None = None,
) -> ImportPreview:
    """Stage a result and derive every registration action without mutating project files."""

    active = load_active_initiative(layout)
    staged = stage_result(layout, manifest_path)
    if (layout.imported_result_directory / f"{staged.result.id}.json").exists():
        raise ConflictError(f"Result {staged.result.id} is already imported")
    if staged.result.id == staged.result.source_run_or_handoff_id:
        raise ConflictError("Result ID must differ from its source run or handoff ID")
    if any(
        staged.result.id in event.affected_record_ids
        for event in read_journal(layout.event_journal_file)
    ):
        raise ConflictError(f"Result ID {staged.result.id} is already a governed record ID")
    if not staged.files:
        raise ConflictError("A result import must declare at least one returned file")
    step_id, source_run_id = _source_step(active, staged.result.source_run_or_handoff_id)
    step = next(item for item in active.workflow.steps if item.id == step_id)
    step_state = active.state.step_states[step_id]
    if step_state is StepState.SKIPPED:
        raise ConflictError(
            f"Result source step {step_id} cannot import files from state {step_state.value}"
        )
    roles = _normalize_assignments(role_assignments or {}, "role")
    collisions = _normalize_assignments(collision_actions or {}, "collision")
    invalid_collision_values = {
        value for value in collisions.values() if value not in {"replace", "revise"}
    }
    if invalid_collision_values:
        raise ConfigurationError(
            f"Unsupported collision actions: {sorted(invalid_collision_values)}"
        )
    views = list_artifacts(layout)
    governed_by_path: dict[str, ArtifactView] = {
        view.current_revision.path: view for view in views
    }
    declared_targets = {item.declaration.proposed_target_path for item in staged.files}
    extra_roles = set(roles) - declared_targets
    extra_collisions = set(collisions) - declared_targets
    if extra_roles or extra_collisions:
        raise ConfigurationError(
            f"Assignments reference undeclared targets: "
            f"roles={sorted(extra_roles)}, collisions={sorted(extra_collisions)}"
        )
    actions: list[ImportAction] = []
    all_blockers: list[str] = []
    for item in staged.files:
        target = normalize_repository_path(item.declaration.proposed_target_path)
        destination = resolve_import_target(layout, target)
        prior_digest = _target_digest(destination)
        governed = governed_by_path.get(target)
        assigned_role = roles.get(target)
        collision = collisions.get(target)
        blockers: list[str] = []
        if governed is not None:
            action = "revise-artifact"
            role = governed.artifact.role
            artifact_id = governed.artifact.id
            if collision != "revise":
                blockers.append(
                    f"{target}: governed collision requires --collision {target}=revise"
                )
            if assigned_role is not None and assigned_role != role:
                blockers.append(
                    f"{target}: role {assigned_role!r} conflicts with governed role {role!r}"
                )
            if governed.current_revision.content_digest == item.digest:
                blockers.append(f"{target}: returned bytes match the current artifact revision")
        elif prior_digest is not None:
            action = "replace-and-register"
            role = assigned_role
            artifact_id = None
            if collision != "replace":
                blockers.append(
                    f"{target}: ungoverned collision requires --collision {target}=replace"
                )
        else:
            action = "create-artifact"
            role = assigned_role
            artifact_id = None
            if collision is not None:
                blockers.append(f"{target}: collision action is unnecessary for a new target")
        if role is None:
            blockers.append(f"{target}: new artifact registration requires --role {target}=ROLE")
        elif not _SYMBOLIC_ID.fullmatch(role):
            blockers.append(f"{target}: invalid symbolic artifact role {role!r}")
        elif role not in step.required_outputs:
            blockers.append(
                f"{target}: role {role!r} is not a required output of source step {step_id}"
            )
        if step_state is StepState.COMPLETED and governed is None:
            blockers.append(
                f"{target}: a completed source step permits only an explicit governed revision"
            )
        media_type = item.declaration.media_type or "application/octet-stream"
        action_record = ImportAction(
            item.declaration.source_path,
            target,
            action,
            role,
            artifact_id,
            item.digest,
            item.byte_size,
            media_type,
            prior_digest,
            tuple(blockers),
        )
        actions.append(action_record)
        all_blockers.extend(blockers)
    return ImportPreview(
        staged,
        step_id,
        source_run_id,
        active.state.journal_head_sequence,
        tuple(actions),
        tuple(all_blockers),
    )


def _combine_invalidations(
    active: ActiveInitiative,
    values: tuple[DependencyInvalidation, ...],
) -> DependencyInvalidation:
    stale = {item for value in values for item in value.stale_record_ids}
    invalidated = {item for value in values for item in value.invalidated_step_ids}
    reset = {item for value in values for item in value.reset_step_ids} - invalidated
    runs = {item for value in values for item in value.invalidated_run_ids}
    return DependencyInvalidation(
        tuple(sorted(stale, key=str)),
        tuple(step.id for step in active.workflow.steps if step.id in invalidated),
        tuple(step.id for step in active.workflow.steps if step.id in reset),
        tuple(sorted(runs, key=str)),
    )


def _ensure_directory(path: Path, created: list[Path]) -> None:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Expected a governed directory at {path}")
        return
    path.mkdir()
    created.append(path)


def _ensure_target_parent(layout: RepositoryLayout, target: str, created: list[Path]) -> Path:
    destination = resolve_import_target(layout, target)
    parent = destination.parent
    missing: list[Path] = []
    cursor = parent
    while cursor != layout.root and not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    if cursor.is_symlink() or not cursor.is_dir():
        raise SecurityError(f"Import target parent is unsafe: {cursor}")
    for directory in reversed(missing):
        if directory.is_symlink():
            raise SecurityError(f"Import target parent is a symbolic link: {directory}")
        directory.mkdir()
        created.append(directory)
    return destination


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def apply_result_import(
    layout: RepositoryLayout,
    *,
    manifest_path: Path,
    actor: Actor,
    role_assignments: dict[str, str] | None = None,
    collision_actions: dict[str, str] | None = None,
) -> ImportedResult:
    """Apply one fully previewed result as a single append-only import event."""

    preview = preview_result_import(
        layout,
        manifest_path=manifest_path,
        role_assignments=role_assignments,
        collision_actions=collision_actions,
    )
    if preview.blockers:
        raise ConflictError("Import preview is blocked: " + "; ".join(preview.blockers))
    active = load_active_initiative(layout)
    if active.state.journal_head_sequence != preview.journal_sequence:
        raise ConflictError("Initiative changed during import preview; preview again")
    step = next(item for item in active.workflow.steps if item.id == preview.step_id)
    if actor.actor_type not in step.allowed_actors:
        raise ConflictError(
            f"Actor type {actor.actor_type.value} is not allowed for source step {step.id}"
        )
    views = {view.artifact.id: view for view in list_artifacts(layout)}
    for action in preview.actions:
        staged_path = preview.staged.directory / "files" / action.source_path
        if sha256_digest(staged_path.read_bytes()) != action.digest:
            raise IntegrityError(f"Staged file changed after preview: {action.source_path}")
        destination = resolve_import_target(layout, action.target_path)
        if _target_digest(destination) != action.prior_target_digest:
            raise ConflictError(f"Import target changed after preview: {action.target_path}")

    invalidation_values: list[DependencyInvalidation] = []
    prior_views: dict[str, ArtifactView] = {}
    for action in preview.actions:
        if action.artifact_id is None:
            continue
        view = views[action.artifact_id]
        prior_views[action.target_path] = view
        invalidation_values.append(
            calculate_artifact_revision_invalidation(active, view.current_revision)
        )
    invalidation = _combine_invalidations(active, tuple(invalidation_values))
    configuration = load_configuration(layout.configuration_file)
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    event_id = uuid4()
    basis = (
        "participant explicitly applied a previewed untrusted result with collision-safe "
        "artifact registration"
    )
    artifacts: list[ArtifactRecord] = []
    revisions: list[ArtifactRevision] = []
    preserved_objects = []
    updates: list[dict[str, object]] = []
    for action in preview.actions:
        content = (preview.staged.directory / "files" / action.source_path).read_bytes()
        preserved = preserve_bytes(
            layout,
            content,
            max_bytes=configuration.artifacts.max_preserved_object_bytes,
        )
        preserved_objects.append(preserved)
        prior = prior_views.get(action.target_path)
        artifact_id = prior.artifact.id if prior is not None else uuid4()
        revision_number = prior.current_revision.revision_number + 1 if prior else 1
        revision_id = uuid4()
        own_invalidation = (
            calculate_artifact_revision_invalidation(active, prior.current_revision)
            if prior is not None
            else DependencyInvalidation((), (), (), ())
        )
        role = action.role
        if role is None:
            raise IntegrityError("Validated import action lost its artifact role")
        artifact = ArtifactRecord(
            id=artifact_id,
            initiative_id=active.initiative.id,
            actor_id=actor.id,
            recorded_at=now,
            event_sequence=sequence,
            run_id=preview.source_run_id,
            authorization_basis=basis,
            tool_version=__version__,
            affected_record_ids=tuple(
                dict.fromkeys(
                    (
                        revision_id,
                        preview.staged.result.id,
                        *(own_invalidation.stale_record_ids),
                    )
                )
            ),
            affected_digests=(preserved.digest,),
            role=role,
            title=prior.artifact.title if prior else Path(action.target_path).name,
            created_by=prior.artifact.created_by if prior else actor,
            current_revision=revision_number,
        )
        provenance = ProvenanceRecord(
            id=uuid4(),
            source_type="import-result",
            source_reference=(
                f"result:{preview.staged.result.id}:{action.source_path}"
            ),
            actor_id=actor.id,
            run_id=preview.source_run_id,
            recorded_at=now,
            metadata={"untrusted": True},
        )
        revision = ArtifactRevision(
            id=revision_id,
            initiative_id=active.initiative.id,
            actor_id=actor.id,
            recorded_at=now,
            event_sequence=sequence,
            run_id=preview.source_run_id,
            authorization_basis=basis,
            tool_version=__version__,
            affected_record_ids=tuple(
                dict.fromkeys(
                    (
                        artifact_id,
                        preview.staged.result.id,
                        *((prior.current_revision.id,) if prior else ()),
                        *own_invalidation.stale_record_ids,
                    )
                )
            ),
            affected_digests=(preserved.digest,),
            artifact_id=artifact_id,
            revision_number=revision_number,
            path=action.target_path,
            content_digest=preserved.digest,
            byte_size=len(content),
            media_type=action.media_type,
            provenance=provenance,
            registration_event_id=event_id,
            preserved_object_path=preserved.repository_path,
            preservation_status="preserved",
            superseded_revision_number=(
                prior.current_revision.revision_number if prior else None
            ),
            stale_dependency_effects=own_invalidation.stale_record_ids,
        )
        artifacts.append(artifact)
        revisions.append(revision)
        updates.append(
            {
                "action": "revise" if prior else "create",
                "artifact_id": str(artifact_id),
                "artifact_role": role,
                "byte_size": len(content),
                "content_digest": preserved.digest,
                "media_type": action.media_type,
                "revision_id": str(revision_id),
                "revision_number": revision_number,
                "source_path": action.source_path,
                "target_path": action.target_path,
                **(
                    {"superseded_revision_id": str(prior.current_revision.id)}
                    if prior
                    else {}
                ),
            }
        )
    result_digest = canonical_json_digest(preview.staged.result.model_dump(mode="json"))
    affected_ids = tuple(
        dict.fromkeys(
            (
                preview.staged.result.id,
                *(item.id for pair in zip(artifacts, revisions, strict=True) for item in pair),
                *invalidation.stale_record_ids,
            )
        )
    )
    affected_digests = tuple(
        dict.fromkeys(
            (
                result_digest,
                preview.staged.manifest_digest,
                *(item.content_digest for item in revisions),
            )
        )
    )
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=RESULT_IMPORTED,
        actor=actor,
        run_id=preview.source_run_id,
        authorization_basis=basis,
        affected_record_ids=affected_ids,
        affected_digests=affected_digests,
        metadata={
            "artifact_updates": updates,
            "manifest_digest": preview.staged.manifest_digest,
            "result_digest": result_digest,
            "result_id": str(preview.staged.result.id),
            "source_id": str(preview.staged.result.source_run_or_handoff_id),
            "source_kind": "run" if preview.source_run_id is not None else "handoff",
            "step_id": preview.step_id,
            **invalidation.event_metadata(),
        },
    )

    created_directories: list[Path] = []
    record_paths: list[Path] = []
    backups: dict[Path, bytes | None] = {}
    try:
        _ensure_directory(layout.artifact_directory, created_directories)
        _ensure_directory(layout.artifact_record_directory, created_directories)
        _ensure_directory(layout.artifact_revision_directory, created_directories)
        _ensure_directory(layout.imported_result_directory, created_directories)
        for action in preview.actions:
            destination = _ensure_target_parent(
                layout, action.target_path, created_directories
            )
            backups[destination] = destination.read_bytes() if destination.exists() else None
            content = (preview.staged.directory / "files" / action.source_path).read_bytes()
            atomic_write_bytes(destination, content)
        for artifact, revision in zip(artifacts, revisions, strict=True):
            artifact_path = (
                layout.artifact_record_directory
                / f"{artifact.id}.{artifact.current_revision}.json"
            )
            revision_path = layout.artifact_revision_directory / f"{revision.id}.json"
            write_record(artifact_path, artifact)
            record_paths.append(artifact_path)
            write_record(revision_path, revision)
            record_paths.append(revision_path)
        result_path = (
            layout.imported_result_directory / f"{preview.staged.result.id}.json"
        )
        write_record(result_path, preview.staged.result)
        record_paths.append(result_path)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event.id):
            for path in reversed(record_paths):
                path.unlink(missing_ok=True)
            for destination, previous in backups.items():
                if previous is None:
                    destination.unlink(missing_ok=True)
                else:
                    atomic_write_bytes(destination, previous)
            for preserved in preserved_objects:
                if preserved.created:
                    preserved.filesystem_path.unlink(missing_ok=True)
            for directory in reversed(created_directories):
                with suppress(OSError):
                    directory.rmdir()
        raise
    load_active_initiative(layout)
    return ImportedResult(preview, event, tuple(artifacts), tuple(revisions))
