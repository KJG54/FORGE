"""Conservative, owner-authorized active-snapshot recovery."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.recovery import RecoveryRecord, SnapshotCondition
from forge.contracts.state import InitiativeLifecycleState, MaterializedState
from forge.core.authorization import require_owner
from forge.core.lifecycle import load_replayed_active_initiative
from forge.core.record_validation import validate_governed_records
from forge.core.transitions import INTEGRITY_RECOVERED
from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.canonical import canonical_json_digest, sha256_digest
from forge.storage.idempotency import (
    IDEMPOTENCY_METADATA_KEY,
    current_idempotency_request,
)
from forge.storage.journal import append_event, read_journal
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import (
    MAX_SNAPSHOT_BYTES,
    inspect_snapshot_integrity,
    replay_events,
    write_snapshot,
)


@dataclass(frozen=True)
class RecoveryResult:
    record: RecoveryRecord
    event: AuditEvent
    state: MaterializedState
    resumed: bool


def _ensure_directory(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise SecurityError(f"Recovery directory is unsafe: {path}")
        return
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create recovery directory {path}: {error}") from error


def _recovery_path(layout: RepositoryLayout, recovery_id: UUID) -> Path:
    return layout.recovery_record_directory / f"{recovery_id}.json"


def _snapshot_path(layout: RepositoryLayout, recovery_id: UUID) -> Path:
    return layout.recovery_snapshot_directory / f"{recovery_id}.bin"


def _relative(layout: RepositoryLayout, path: Path) -> str:
    return path.relative_to(layout.root).as_posix()


def _resume_event(
    events: tuple[AuditEvent, ...],
    *,
    key: str,
    command: str,
    request_digest: str,
) -> AuditEvent | None:
    matches: list[AuditEvent] = []
    expected = {"key": key, "command": command, "request_digest": request_digest}
    for event in events:
        if event.metadata.get(IDEMPOTENCY_METADATA_KEY) == expected:
            matches.append(event)
    if not matches:
        return None
    if (
        len(matches) != 1
        or matches[0].event_type != INTEGRITY_RECOVERED
        or matches[0] != events[-1]
    ):
        raise IntegrityError("Incomplete recovery history is ambiguous")
    return matches[0]


def _load_recovery_record(layout: RepositoryLayout, event: AuditEvent) -> RecoveryRecord:
    raw_id = event.metadata.get("recovery_record_id")
    if not isinstance(raw_id, str):
        raise IntegrityError(f"Recovery event {event.id} lacks a recovery record ID")
    try:
        recovery_id = UUID(raw_id)
    except ValueError as error:
        raise IntegrityError(f"Recovery event {event.id} has an invalid record ID") from error
    return load_record(_recovery_path(layout, recovery_id), RecoveryRecord)


def _validate_resume_observation(
    layout: RepositoryLayout,
    record: RecoveryRecord,
    *,
    snapshot_is_healthy: bool,
) -> None:
    """Refuse to overwrite snapshot changes made after the recovery event."""
    if snapshot_is_healthy:
        return
    if record.snapshot_condition is SnapshotCondition.MISSING:
        if layout.state_file.exists():
            raise IntegrityError(
                "Snapshot changed after the recovery event; automatic resume is unsafe"
            )
        return
    if not layout.state_file.is_file() or layout.state_file.is_symlink():
        raise IntegrityError(
            "Snapshot changed after the recovery event; automatic resume is unsafe"
        )
    assert record.preserved_snapshot_path is not None
    preserved_path = layout.root / record.preserved_snapshot_path
    try:
        current = layout.state_file.read_bytes()
        preserved = preserved_path.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot compare interrupted recovery snapshot: {error}") from error
    if current != preserved:
        raise IntegrityError(
            "Snapshot changed after the recovery event; automatic resume is unsafe"
        )


def recover_active_snapshot(
    layout: RepositoryLayout,
    *,
    actor: Actor,
    reason: str,
) -> RecoveryResult:
    """Reconstruct ``state.json`` only from a complete, unambiguous journal."""
    if not reason.strip():
        raise ConflictError("Recovery requires a non-empty owner reason")
    request = current_idempotency_request()
    active, events = load_replayed_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "recover materialized state")
    if active.state.lifecycle_state in {
        InitiativeLifecycleState.CLOSED,
        InitiativeLifecycleState.ABANDONED,
    }:
        raise ConflictError("Active-snapshot recovery does not operate on terminal initiatives")
    if not events or events[-1].event_hash is None:
        raise ConflictError(
            "Recovery requires a fully hash-chained M2 journal; legacy history needs migration"
        )

    resume_event = _resume_event(
        events,
        key=request.key,
        command=request.command,
        request_digest=request.request_digest,
    )
    if resume_event is not None:
        record = _load_recovery_record(layout, resume_event)
        validate_governed_records(layout, events, active.state, active.workflow)
        before = inspect_snapshot_integrity(
            layout.event_journal_file, layout.state_file, active.reducer
        )
        _validate_resume_observation(
            layout,
            record,
            snapshot_is_healthy=before.is_healthy,
        )
        write_snapshot(layout.state_file, active.state)
        report = inspect_snapshot_integrity(
            layout.event_journal_file, layout.state_file, active.reducer
        )
        if not report.is_healthy:
            raise IntegrityError("Recovery resume did not restore a healthy snapshot")
        return RecoveryResult(record, resume_event, active.state, True)

    validate_governed_records(layout, events, active.state, active.workflow)
    report = inspect_snapshot_integrity(
        layout.event_journal_file, layout.state_file, active.reducer
    )
    if report.is_healthy:
        raise ConflictError("Materialized state is already healthy; recovery is unnecessary")

    snapshot_bytes: bytes | None = None
    if not layout.state_file.exists():
        condition = SnapshotCondition.MISSING
    else:
        if layout.state_file.is_symlink() or not layout.state_file.is_file():
            raise SecurityError(f"Refusing to preserve unsafe snapshot: {layout.state_file}")
        try:
            snapshot_bytes = layout.state_file.read_bytes()
        except OSError as error:
            raise IntegrityError(f"Cannot preserve materialized snapshot: {error}") from error
        if len(snapshot_bytes) > MAX_SNAPSHOT_BYTES:
            raise IntegrityError(
                f"Cannot safely preserve snapshot larger than {MAX_SNAPSHOT_BYTES} bytes"
            )
        condition = (
            SnapshotCondition.INVALID
            if report.snapshot is None
            else SnapshotCondition.MISMATCHED
        )

    recovery_id = uuid4()
    recovery_event_id = uuid4()
    record_path = _recovery_path(layout, recovery_id)
    preserved_path = _snapshot_path(layout, recovery_id)
    preserved_digest = sha256_digest(snapshot_bytes) if snapshot_bytes is not None else None
    preserved_relative = (
        _relative(layout, preserved_path) if snapshot_bytes is not None else None
    )
    authorization_basis = "configured owner explicitly requested snapshot recovery"
    record = RecoveryRecord(
        id=recovery_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        actor=actor,
        recorded_at=utc_now(),
        event_sequence=len(events) + 1,
        authorization_basis=authorization_basis,
        tool_version=__version__,
        affected_digests=(preserved_digest,) if preserved_digest is not None else (),
        recovery_event_id=recovery_event_id,
        reason=reason,
        source_journal_head_sequence=events[-1].sequence,
        source_journal_head_hash=events[-1].event_hash,
        snapshot_condition=condition,
        preserved_snapshot_path=preserved_relative,
        preserved_snapshot_digest=preserved_digest,
        preserved_snapshot_size=len(snapshot_bytes) if snapshot_bytes is not None else None,
    )
    record_digest = canonical_json_digest(record.model_dump(mode="json"))
    affected_digests = (record_digest,) + (
        (preserved_digest,) if preserved_digest is not None else ()
    )
    event = AuditEvent(
        id=recovery_event_id,
        initiative_id=active.initiative.id,
        sequence=len(events) + 1,
        timestamp=record.recorded_at,
        event_type=INTEGRITY_RECOVERED,
        actor=actor,
        authorization_basis=authorization_basis,
        affected_record_ids=(recovery_id,),
        affected_digests=affected_digests,
        metadata={
            "recovery_record_id": str(recovery_id),
            "reason": record.reason,
            "snapshot_condition": condition.value,
            "source_journal_head_sequence": events[-1].sequence,
            "source_journal_head_hash": events[-1].event_hash,
            "preserved_snapshot_path": preserved_relative,
            "preserved_snapshot_digest": preserved_digest,
            "preserved_snapshot_size": (
                len(snapshot_bytes) if snapshot_bytes is not None else None
            ),
        },
    )

    created: list[Path] = []
    try:
        _ensure_directory(layout.recovery_record_directory)
        if snapshot_bytes is not None:
            _ensure_directory(layout.recovery_snapshot_directory)
            atomic_write_bytes(preserved_path, snapshot_bytes)
            created.append(preserved_path)
        write_record(record_path, record)
        created.append(record_path)
        committed = append_event(layout.event_journal_file, event)
        state = replay_events(committed, active.reducer)
        if state is None:
            raise IntegrityError("Recovery event journal did not produce materialized state")
        validate_governed_records(layout, committed, state, active.workflow)
        write_snapshot(layout.state_file, state)
        after = inspect_snapshot_integrity(
            layout.event_journal_file, layout.state_file, active.reducer
        )
        if not after.is_healthy:
            raise IntegrityError("Recovery did not restore a healthy snapshot")
        return RecoveryResult(record, committed[-1], state, False)
    except BaseException:
        committed_ids: set[UUID] = set()
        with suppress(Exception):
            committed_ids = {item.id for item in read_journal(layout.event_journal_file)}
        if recovery_event_id not in committed_ids:
            for path in reversed(created):
                path.unlink(missing_ok=True)
            with suppress(OSError):
                layout.recovery_snapshot_directory.rmdir()
            with suppress(OSError):
                layout.recovery_record_directory.rmdir()
        raise
