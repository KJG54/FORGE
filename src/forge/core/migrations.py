"""Owner-authorized, provenance-preserving active-state migrations."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.migrations import MigrationRecord
from forge.contracts.state import MaterializedState
from forge.core.archival import list_archive_summaries
from forge.core.authorization import migration_actor, require_owner
from forge.core.lifecycle import load_active_initiative, load_replayed_active_initiative
from forge.core.record_validation import validate_governed_records
from forge.core.transitions import SCHEMA_MIGRATED
from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.canonical import canonical_json_digest, sha256_digest
from forge.storage.idempotency import (
    IDEMPOTENCY_METADATA_KEY,
    current_idempotency_request,
    stamp_event_for_current_mutation,
)
from forge.storage.journal import read_journal
from forge.storage.migrations import (
    MAX_MIGRATION_SOURCE_BYTES,
    MigrationPlan,
    plan_event_journal_migration,
    render_migrated_journal,
)
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import inspect_snapshot_integrity, replay_events, write_snapshot


@dataclass(frozen=True)
class MigrationInspection:
    initiative_id: UUID
    plan: MigrationPlan


@dataclass(frozen=True)
class MigrationResult:
    record: MigrationRecord
    event: AuditEvent
    state: MaterializedState
    resumed: bool


def _ensure_directory(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise SecurityError(f"Migration directory is unsafe: {path}")
        return
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create migration directory {path}: {error}") from error


def _record_path(layout: RepositoryLayout, migration_id: UUID) -> Path:
    return layout.migration_record_directory / f"{migration_id}.json"


def _source_path(layout: RepositoryLayout, migration_id: UUID) -> Path:
    return layout.migration_source_directory / f"{migration_id}.events.jsonl"


def _relative(layout: RepositoryLayout, path: Path) -> str:
    return path.relative_to(layout.root).as_posix()


def _resume_event(events: tuple[AuditEvent, ...]) -> AuditEvent | None:
    request = current_idempotency_request()
    expected = {
        "key": request.key,
        "command": request.command,
        "request_digest": request.request_digest,
    }
    matches = [
        event
        for event in events
        if event.metadata.get(IDEMPOTENCY_METADATA_KEY) == expected
    ]
    if not matches:
        return None
    if (
        len(matches) != 1
        or matches[0].event_type != SCHEMA_MIGRATED
        or matches[0] != events[-1]
    ):
        raise IntegrityError("Incomplete schema migration history is ambiguous")
    return matches[0]


def _load_migration_record(
    layout: RepositoryLayout, event: AuditEvent
) -> MigrationRecord:
    raw_id = event.metadata.get("migration_record_id")
    if not isinstance(raw_id, str):
        raise IntegrityError(f"Migration event {event.id} lacks a migration record ID")
    try:
        migration_id = UUID(raw_id)
    except ValueError as error:
        raise IntegrityError(f"Migration event {event.id} has an invalid record ID") from error
    return load_record(_record_path(layout, migration_id), MigrationRecord)


def inspect_active_migration(layout: RepositoryLayout) -> MigrationInspection:
    """Validate active state and report the one supported next migration, if any."""
    active = load_active_initiative(layout, allow_paused=True)
    events = read_journal(layout.event_journal_file)
    return MigrationInspection(active.initiative.id, plan_event_journal_migration(events))


def migrate_active_repository(
    layout: RepositoryLayout,
    *,
    actor: Actor,
) -> MigrationResult:
    """Atomically migrate one valid legacy active journal and rebuild its snapshot."""
    active, events = load_replayed_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "migrate active FORGE state")
    list_archive_summaries(layout)

    resume_event = _resume_event(events)
    if resume_event is not None:
        record = _load_migration_record(layout, resume_event)
        validate_governed_records(layout, events, active.state, active.workflow)
        write_snapshot(layout.state_file, active.state)
        report = inspect_snapshot_integrity(
            layout.event_journal_file, layout.state_file, active.reducer
        )
        if not report.is_healthy:
            raise IntegrityError("Migration resume did not restore a healthy snapshot")
        return MigrationResult(record, resume_event, active.state, True)

    plan = plan_event_journal_migration(events)
    if not plan.required or plan.definition is None:
        raise ConflictError("Active FORGE state already uses the current schema format")
    # The ordinary loader proves legacy snapshot agreement and all governed records before bytes
    # that participate in authoritative history are replaced.
    active = load_active_initiative(layout, allow_paused=True)
    try:
        source_bytes = layout.event_journal_file.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read legacy migration source: {error}") from error
    if not source_bytes or len(source_bytes) > MAX_MIGRATION_SOURCE_BYTES:
        raise IntegrityError(
            "Legacy journal migration source is empty or exceeds "
            f"{MAX_MIGRATION_SOURCE_BYTES} bytes"
        )

    service_actor = migration_actor()
    record_id = uuid4()
    event_id = uuid4()
    now = utc_now()
    source_path = _source_path(layout, record_id)
    source_digest = sha256_digest(source_bytes)
    authorization_basis = "configured owner explicitly applied a registered schema migration"
    definition = plan.definition
    record = MigrationRecord(
        id=record_id,
        initiative_id=active.initiative.id,
        actor_id=service_actor.id,
        recorded_at=now,
        event_sequence=len(events) + 1,
        authorization_basis=authorization_basis,
        tool_version=__version__,
        affected_digests=(source_digest,),
        migration_event_id=event_id,
        migration_id=definition.id,
        owner_actor=actor,
        migration_actor=service_actor,
        source_schema_version=definition.source_schema_version,
        target_schema_version=definition.target_schema_version,
        source_format=definition.source_format,
        target_format=definition.target_format,
        source_event_count=len(events),
        preserved_source_path=_relative(layout, source_path),
        preserved_source_digest=source_digest,
        preserved_source_size=len(source_bytes),
    )
    record_digest = canonical_json_digest(record.model_dump(mode="json"))
    event = stamp_event_for_current_mutation(
        AuditEvent(
            id=event_id,
            initiative_id=active.initiative.id,
            sequence=len(events) + 1,
            timestamp=now,
            event_type=SCHEMA_MIGRATED,
            actor=service_actor,
            authorization_basis=authorization_basis,
            affected_record_ids=(record_id,),
            affected_digests=(record_digest, source_digest),
            metadata={
                "migration_record_id": str(record_id),
                "migration_id": definition.id,
                "owner_actor_id": str(actor.id),
                "source_schema_version": definition.source_schema_version,
                "target_schema_version": definition.target_schema_version,
                "source_format": definition.source_format,
                "target_format": definition.target_format,
                "source_event_count": len(events),
                "preserved_source_path": record.preserved_source_path,
                "preserved_source_digest": source_digest,
                "preserved_source_size": len(source_bytes),
            },
        )
    )
    rendered, migrated_events = render_migrated_journal(events, event)

    created: list[Path] = []
    try:
        _ensure_directory(layout.migration_record_directory)
        _ensure_directory(layout.migration_source_directory)
        atomic_write_bytes(source_path, source_bytes)
        created.append(source_path)
        write_record(_record_path(layout, record_id), record)
        created.append(_record_path(layout, record_id))

        def validate_journal(temporary: Path) -> None:
            if read_journal(temporary) != migrated_events:
                raise IntegrityError("Temporary migrated journal did not reproduce its plan")

        atomic_write_bytes(
            layout.event_journal_file,
            rendered,
            validator=validate_journal,
        )
        state = replay_events(migrated_events, active.reducer)
        if state is None:
            raise IntegrityError("Migrated journal did not produce materialized state")
        validate_governed_records(layout, migrated_events, state, active.workflow)
        write_snapshot(layout.state_file, state)
        after = inspect_snapshot_integrity(
            layout.event_journal_file, layout.state_file, active.reducer
        )
        if not after.is_healthy:
            raise IntegrityError("Schema migration did not restore a healthy snapshot")
        return MigrationResult(record, migrated_events[-1], state, False)
    except BaseException:
        committed_ids: set[UUID] = set()
        with suppress(Exception):
            committed_ids = {item.id for item in read_journal(layout.event_journal_file)}
        if event_id not in committed_ids:
            for path in reversed(created):
                path.unlink(missing_ok=True)
            with suppress(OSError):
                layout.migration_source_directory.rmdir()
            with suppress(OSError):
                layout.migration_record_directory.rmdir()
        raise
