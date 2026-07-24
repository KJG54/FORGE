"""Conservative, owner-authorized recovery of one missing command receipt."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.idempotency import (
    CommandRecoveryRecord,
    IdempotencyEventReference,
    IdempotencyReceipt,
)
from forge.contracts.state import InitiativeLifecycleState, MaterializedState
from forge.core.authorization import require_owner
from forge.core.lifecycle import load_replayed_active_initiative
from forge.core.record_validation import validate_governed_records
from forge.core.transitions import COMMAND_RECOVERED
from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.canonical import canonical_json_digest
from forge.storage.idempotency import (
    IDEMPOTENCY_METADATA_KEY,
    current_idempotency_request,
    inspect_incomplete_command,
    write_recovered_receipt,
)
from forge.storage.journal import append_event, read_journal
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import (
    StateReducer,
    inspect_snapshot_integrity,
    replay_events,
    write_snapshot,
)

EXPECTED_EVENT_PATTERNS: dict[str, tuple[tuple[str, ...], ...]] = {
    "acceptance_record": (("acceptance-recorded", "step-transitioned"),),
    "acceptance_revoke": (("acceptance-revoked",),),
    "artifact_add": (("artifact-registered",),),
    "artifact_revise": (("artifact-revised",),),
    "begin": (("step-transitioned",),),
    "check_record": (("check-recorded",),),
    "check_run": (("validator-run-started", "check-recorded"),),
    "complete": (("claim-recorded", "step-transitioned"),),
    "create": (("initiative-created",),),
    "decide": (("decision-recorded",), ("decision-superseded",)),
    "evidence_add": (("evidence-registered",),),
    "import_result": (("result-imported",),),
    "pause": (("initiative-paused",),),
    "resume": (("initiative-resumed",),),
    "run_cancel": (("run-cancelled",),),
    "trust_pack": (("pack-trust-changed",),),
    "untrust_pack": (("pack-trust-changed",),),
    "verify": (("step-transitioned",),),
}


@dataclass(frozen=True)
class CommandRecoveryResult:
    record: CommandRecoveryRecord
    event: AuditEvent
    receipt: IdempotencyReceipt
    state: MaterializedState
    resumed: bool


def _ensure_directory(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise SecurityError(f"Command recovery directory is unsafe: {path}")
        return
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create command recovery directory {path}: {error}") from error


def _record_path(layout: RepositoryLayout, record_id: UUID) -> Path:
    return layout.command_recovery_record_directory / f"{record_id}.json"


def _event_reference(event: AuditEvent) -> IdempotencyEventReference:
    if event.event_hash is None:
        raise IntegrityError("Command recovery requires hash-chained journal events")
    return IdempotencyEventReference(
        event_id=event.id,
        initiative_id=event.initiative_id,
        sequence=event.sequence,
        event_hash=event.event_hash,
    )


def _receipt_from_record(record: CommandRecoveryRecord) -> IdempotencyReceipt:
    receipt = IdempotencyReceipt(
        key=record.interrupted_key,
        command=record.interrupted_command,
        request_digest=record.interrupted_request_digest,
        completed_at=record.receipt_completed_at,
        events=record.recovered_events,
    )
    if canonical_json_digest(receipt.model_dump(mode="json")) != record.recovered_receipt_digest:
        raise IntegrityError("Command recovery record does not reproduce its completion receipt")
    return receipt


def _matching_recovery_event(
    events: tuple[AuditEvent, ...],
    *,
    key: str,
    command: str,
    request_digest: str,
) -> AuditEvent | None:
    expected = {"key": key, "command": command, "request_digest": request_digest}
    matches = [
        event for event in events if event.metadata.get(IDEMPOTENCY_METADATA_KEY) == expected
    ]
    if not matches:
        return None
    if len(matches) != 1 or matches[0].event_type != COMMAND_RECOVERED or matches[0] != events[-1]:
        raise IntegrityError("Incomplete command-recovery history is ambiguous")
    return matches[0]


def _load_resume_record(
    layout: RepositoryLayout,
    event: AuditEvent,
) -> CommandRecoveryRecord:
    value = event.metadata.get("command_recovery_record_id")
    if not isinstance(value, str):
        raise IntegrityError(f"Command recovery event {event.id} lacks a recovery record ID")
    try:
        record_id = UUID(value)
    except ValueError as error:
        raise IntegrityError(
            f"Command recovery event {event.id} has an invalid record ID"
        ) from error
    return load_record(_record_path(layout, record_id), CommandRecoveryRecord)


def _validate_target_tail(
    events: tuple[AuditEvent, ...],
    recovered: tuple[IdempotencyEventReference, ...],
    *,
    resume_event: AuditEvent | None,
) -> None:
    expected_tail = events[:-1] if resume_event is not None else events
    count = len(recovered)
    if count > len(expected_tail):
        raise IntegrityError("Interrupted command event group is not an active journal tail")
    actual = tuple(_event_reference(event) for event in expected_tail[-count:])
    if actual != recovered:
        raise IntegrityError(
            "Interrupted command events are not one contiguous active-journal tail"
        )


def _validate_command_pattern(
    events: tuple[AuditEvent, ...],
    *,
    command: str,
    recovered_event_count: int,
    has_recovery_event: bool,
) -> None:
    patterns = EXPECTED_EVENT_PATTERNS.get(command)
    if patterns is None:
        raise ConflictError(
            f"Command {command!r} has no conservative receipt-recovery pattern; "
            "use its specialized transaction recovery path or preserve it for diagnosis"
        )
    end = len(events) - int(has_recovery_event)
    actual = tuple(item.event_type for item in events[end - recovered_event_count : end])
    if actual not in patterns:
        raise IntegrityError(
            f"Interrupted {command!r} event group is partial or ambiguous: {actual}"
        )


def _validate_snapshot_observation(
    layout: RepositoryLayout,
    events: tuple[AuditEvent, ...],
    state: MaterializedState,
    reducer: StateReducer,
    *,
    recovered_event_count: int,
    has_recovery_event: bool,
) -> None:
    # Atomic replacement can leave the exact snapshot from immediately before the
    # interrupted command, or the current replay if its refresh succeeded.
    report = inspect_snapshot_integrity(layout.event_journal_file, layout.state_file, reducer)
    prior_count = len(events) - recovered_event_count - int(has_recovery_event)
    previous = replay_events(events[:prior_count], reducer)
    before_recovery = replay_events(events[:-1], reducer) if has_recovery_event else state
    missing_initial_snapshot = previous is None and not layout.state_file.exists()
    matches_previous = previous is not None and report.snapshot == previous
    if not (
        missing_initial_snapshot
        or matches_previous
        or report.snapshot == before_recovery
        or report.snapshot == state
    ):
        raise IntegrityError(
            "Snapshot condition is not an atomic interruption boundary for this command"
        )


def recover_command_receipt(
    layout: RepositoryLayout,
    *,
    actor: Actor,
    interrupted_key: str,
    reason: str,
) -> CommandRecoveryResult:
    """Recover one mechanically complete active command without changing its effects."""
    if not reason.strip():
        raise ConflictError("Command receipt recovery requires a non-empty owner reason")
    request = current_idempotency_request()
    active, events = load_replayed_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "recover a command receipt")
    if active.state.lifecycle_state in {
        InitiativeLifecycleState.CLOSED,
        InitiativeLifecycleState.ABANDONED,
    }:
        raise ConflictError("Command receipt recovery operates only on an active initiative")

    resume_event = _matching_recovery_event(
        events,
        key=request.key,
        command=request.command,
        request_digest=request.request_digest,
    )
    incomplete = inspect_incomplete_command(
        layout,
        target_key=interrupted_key,
        recovery_key=request.key,
        allow_completed_target=resume_event is not None,
    )
    _validate_target_tail(events, incomplete.events, resume_event=resume_event)
    _validate_command_pattern(
        events,
        command=incomplete.command,
        recovered_event_count=len(incomplete.events),
        has_recovery_event=resume_event is not None,
    )

    if resume_event is not None:
        record = _load_resume_record(layout, resume_event)
        if (
            record.recovery_event_id != resume_event.id
            or record.interrupted_key != incomplete.key
            or record.interrupted_command != incomplete.command
            or record.interrupted_request_digest != incomplete.request_digest
            or record.recovered_events != incomplete.events
        ):
            raise IntegrityError(
                "Committed command recovery does not match the interrupted command"
            )
        receipt = _receipt_from_record(record)
        validate_governed_records(layout, events, active.state, active.workflow)
        _validate_snapshot_observation(
            layout,
            events,
            active.state,
            active.reducer,
            recovered_event_count=len(incomplete.events),
            has_recovery_event=True,
        )
        write_snapshot(layout.state_file, active.state)
        write_recovered_receipt(layout, receipt, recovery_key=request.key)
        return CommandRecoveryResult(record, resume_event, receipt, active.state, True)

    validate_governed_records(layout, events, active.state, active.workflow)
    _validate_snapshot_observation(
        layout,
        events,
        active.state,
        active.reducer,
        recovered_event_count=len(incomplete.events),
        has_recovery_event=False,
    )

    record_id = uuid4()
    event_id = uuid4()
    now = utc_now()
    receipt = IdempotencyReceipt(
        key=incomplete.key,
        command=incomplete.command,
        request_digest=incomplete.request_digest,
        completed_at=now,
        events=incomplete.events,
    )
    receipt_digest = canonical_json_digest(receipt.model_dump(mode="json"))
    authorization_basis = "configured owner explicitly recovered an interrupted command receipt"
    record = CommandRecoveryRecord(
        id=record_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        actor=actor,
        recorded_at=now,
        event_sequence=len(events) + 1,
        authorization_basis=authorization_basis,
        tool_version=__version__,
        affected_digests=(receipt_digest,),
        recovery_event_id=event_id,
        reason=reason,
        interrupted_key=incomplete.key,
        interrupted_command=incomplete.command,
        interrupted_request_digest=incomplete.request_digest,
        receipt_completed_at=now,
        recovered_events=incomplete.events,
        recovered_receipt_digest=receipt_digest,
    )
    record_digest = canonical_json_digest(record.model_dump(mode="json"))
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=len(events) + 1,
        timestamp=now,
        event_type=COMMAND_RECOVERED,
        actor=actor,
        authorization_basis=authorization_basis,
        affected_record_ids=(record_id,),
        affected_digests=(record_digest, receipt_digest),
        metadata={
            "command_recovery_record_id": str(record_id),
            "reason": record.reason,
            "interrupted_key": record.interrupted_key,
            "interrupted_command": record.interrupted_command,
            "interrupted_request_digest": record.interrupted_request_digest,
            "receipt_completed_at": record.model_dump(mode="json")["receipt_completed_at"],
            "recovered_event_ids": [str(item.event_id) for item in record.recovered_events],
            "recovered_receipt_digest": receipt_digest,
        },
    )

    path = _record_path(layout, record_id)
    try:
        _ensure_directory(layout.command_recovery_record_directory)
        write_record(path, record)
        committed = append_event(layout.event_journal_file, event)
        state = replay_events(committed, active.reducer)
        if state is None:
            raise IntegrityError("Command recovery journal did not produce materialized state")
        write_snapshot(layout.state_file, state)
        committed_event = committed[-1]
        write_recovered_receipt(layout, receipt, recovery_key=request.key)
        validate_governed_records(
            layout,
            read_journal(layout.event_journal_file),
            state,
            active.workflow,
        )
        return CommandRecoveryResult(record, committed_event, receipt, state, False)
    except BaseException:
        committed_ids: set[UUID] = set()
        with suppress(Exception):
            committed_ids = {item.id for item in read_journal(layout.event_journal_file)}
        if event_id not in committed_ids:
            path.unlink(missing_ok=True)
            with suppress(OSError):
                layout.command_recovery_record_directory.rmdir()
        raise
