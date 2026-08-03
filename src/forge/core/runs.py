"""Immutable run inspection and event-backed cancellation."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor, ActorType
from forge.contracts.base import utc_now
from forge.contracts.capabilities import SideEffectClass
from forge.contracts.events import AuditEvent
from forge.contracts.runs import RunCancellationRecord, RunRecord
from forge.contracts.state import MaterializedState, RunState, StepState
from forge.contracts.workflows import CancellationBehavior
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.transitions import ADAPTER_RUN_EXECUTED, RUN_CANCELLED, STEP_TRANSITIONED
from forge.errors import AuthorizationError, ConflictError, IntegrityError, SecurityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class RunView:
    record: RunRecord
    status: RunState
    ended_at: datetime | None = None
    cancellation_details: str | None = None
    cancellation: RunCancellationRecord | None = None
    invalidation_details: str | None = None


@dataclass(frozen=True)
class RunCancellationResult:
    run: RunView
    event: AuditEvent
    state: MaterializedState
    cancellation: RunCancellationRecord


def _cancellation_path(layout: RepositoryLayout, record_id: UUID) -> Path:
    return layout.run_cancellation_directory / f"{record_id}.json"


def _ensure_directory(path: Path) -> bool:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Expected a governed directory at {path}")
        return False
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create governed directory {path}: {error}") from error
    return True


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def _load_runs(active: ActiveInitiative) -> tuple[RunRecord, ...]:
    directory = active.layout.governed_run_directory
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise IntegrityError(f"Governed run directory is missing or unsafe: {directory}")
    return tuple(
        sorted(
            (load_record(path, RunRecord) for path in directory.glob("*.json")),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def _view(active: ActiveInitiative, run: RunRecord) -> RunView:
    journal = read_journal(active.layout.event_journal_file)
    events = [
        event
        for event in journal
        if event.run_id == run.id
    ]
    terminal = [
        event
        for event in events
        if (
            event.event_type == RUN_CANCELLED
            or (
                event.event_type == STEP_TRANSITIONED
                and event.metadata.get("source_state") == StepState.IN_PROGRESS.value
            )
        )
    ]
    if len(terminal) > 1:
        raise IntegrityError(f"Run {run.id} has multiple terminal events")
    invalidations = [
        event
        for event in journal
        if str(run.id) in event.metadata.get("invalidated_run_ids", [])
    ]
    if len(invalidations) > 1 or (terminal and invalidations):
        raise IntegrityError(f"Run {run.id} has multiple terminal events")
    if invalidations:
        event = invalidations[0]
        return RunView(
            run,
            RunState.CANCELLED,
            event.timestamp,
            invalidation_details=(
                f"Invalidated by {event.event_type} event {event.id}; "
                "no formal run-cancellation record was created"
            ),
        )
    if not terminal:
        if run.id not in active.state.active_run_ids:
            raise IntegrityError(f"Run {run.id} is neither active nor terminal")
        executions = [event for event in events if event.event_type == ADAPTER_RUN_EXECUTED]
        if len(executions) > 1:
            raise IntegrityError(f"Run {run.id} has multiple adapter execution events")
        if executions:
            execution = executions[0]
            try:
                status = RunState(execution.metadata.get("state"))
            except (TypeError, ValueError) as error:
                raise IntegrityError(
                    f"Run {run.id} has an invalid adapter execution state"
                ) from error
            if status not in {RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED}:
                raise IntegrityError(f"Run {run.id} has a non-terminal execution state")
            return RunView(run, status, execution.timestamp)
        return RunView(run, RunState.RUNNING)
    event = terminal[0]
    if event.event_type == RUN_CANCELLED:
        reason = event.metadata.get("reason")
        if not isinstance(reason, str) or not reason:
            raise IntegrityError(f"Run cancellation {event.id} has no reason")
        record_value = event.metadata.get("run_cancellation_record_id")
        if not isinstance(record_value, str):
            raise IntegrityError(f"Run cancellation {event.id} has no cancellation record")
        try:
            cancellation_id = UUID(record_value)
        except ValueError as error:
            raise IntegrityError(
                f"Run cancellation {event.id} has an invalid cancellation record"
            ) from error
        cancellation = load_record(
            _cancellation_path(active.layout, cancellation_id),
            RunCancellationRecord,
        )
        return RunView(
            run,
            RunState.CANCELLED,
            event.timestamp,
            reason,
            cancellation,
        )
    return RunView(run, RunState.SUCCEEDED, event.timestamp)


def list_runs(layout: RepositoryLayout) -> tuple[RunView, ...]:
    active = load_active_initiative(
        layout,
        allow_terminal=True,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    return tuple(_view(active, record) for record in _load_runs(active))


def show_run(layout: RepositoryLayout, run_id: UUID) -> RunView:
    matches = [item for item in list_runs(layout) if item.record.id == run_id]
    if not matches:
        raise ConflictError(f"Unknown run {run_id}")
    return matches[0]


def cancel_run(
    layout: RepositoryLayout,
    *,
    run_id: UUID,
    reason: str,
    actor: Actor,
) -> RunCancellationResult:
    active = load_active_initiative(layout, allow_untrusted_pack=True)
    reason = reason.strip()
    if not reason:
        raise ConflictError("Run cancellation reason must not be empty")
    if run_id not in active.state.active_run_ids:
        raise ConflictError(f"Run {run_id} is not active")
    run = load_record(active.layout.governed_run_directory / f"{run_id}.json", RunRecord)
    is_owner = (
        actor.actor_type is ActorType.OWNER
        and actor.id == active.initiative.owner_identity_id
    )
    if actor != run.worker and not is_owner:
        raise AuthorizationError("Only the run worker or repository owner may cancel a run")
    step = next((item for item in active.workflow.steps if item.id == run.step_id), None)
    if step is None or active.state.step_states.get(run.step_id) is not StepState.IN_PROGRESS:
        raise IntegrityError(f"Active run {run_id} does not match an in-progress step")
    run_events = tuple(
        event
        for event in read_journal(active.layout.event_journal_file)
        if event.run_id == run_id and event.event_type == ADAPTER_RUN_EXECUTED
    )
    if len(run_events) > 1:
        raise IntegrityError(f"Run {run_id} has multiple adapter execution events")
    terminal_execution = run_events[0] if run_events else None
    if run.adapter_reference is not None and terminal_execution is None:
        raise ConflictError(
            "Adapter-run cancellation requires a prior terminal execution event; "
            "live cross-process cancellation is not supported"
        )
    if run.adapter_reference is None and terminal_execution is not None:
        raise IntegrityError(f"Manual run {run_id} has an adapter execution event")
    if terminal_execution is not None and terminal_execution.event_hash is None:
        raise IntegrityError(f"Adapter execution event {terminal_execution.id} is not hash sealed")
    terminal_execution_hash = (
        terminal_execution.event_hash if terminal_execution is not None else None
    )
    externally_risky = run.side_effect_class in {
        SideEffectClass.EXTERNAL_REVERSIBLE,
        SideEffectClass.EXTERNAL_IRREVERSIBLE,
        SideEffectClass.SENSITIVE,
    }
    destination = (
        StepState.BLOCKED
        if externally_risky
        or step.cancellation_behavior is CancellationBehavior.BLOCK_FOR_OWNER_REVIEW
        else StepState.READY
    )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    cancellation_id = uuid4()
    run_digest = canonical_json_digest(run.model_dump(mode="json"))
    affected_record_ids = (
        (run.id, terminal_execution.id)
        if terminal_execution is not None
        else (run.id,)
    )
    affected_digests = (
        (run_digest, terminal_execution_hash)
        if terminal_execution_hash is not None
        else (run_digest,)
    )
    authorization_basis = (
        "authorized run worker or configured owner formally cancelled active work; "
        "managed execution was terminal when applicable"
    )
    cancellation = RunCancellationRecord(
        id=cancellation_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=authorization_basis,
        tool_version=__version__,
        affected_record_ids=affected_record_ids,
        affected_digests=affected_digests,
        run_id=run.id,
        step_id=run.step_id,
        reason=reason,
        actor=actor,
        source_state=StepState.IN_PROGRESS,
        destination_state=destination,
        cancellation_behavior=step.cancellation_behavior,
        side_effect_class=run.side_effect_class,
        terminal_execution_event_id=(
            terminal_execution.id if terminal_execution is not None else None
        ),
        terminal_execution_event_hash=terminal_execution_hash,
    )
    record_digest = canonical_json_digest(cancellation.model_dump(mode="json"))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=RUN_CANCELLED,
        actor=actor,
        run_id=run_id,
        authorization_basis=authorization_basis,
        affected_record_ids=(cancellation_id, *affected_record_ids),
        affected_digests=(*affected_digests, record_digest),
        metadata={
            "run_cancellation_record_id": str(cancellation_id),
            "destination_state": destination.value,
            "reason": reason,
            "source_state": StepState.IN_PROGRESS.value,
            "step_id": run.step_id,
            "terminal_execution_event_id": (
                str(terminal_execution.id) if terminal_execution is not None else None
            ),
        },
    )
    path = _cancellation_path(layout, cancellation_id)
    created_directory = _ensure_directory(path.parent)
    try:
        write_record(path, cancellation)
        state = append_event_and_update_snapshot(
            active.layout.event_journal_file,
            active.layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event.id):
            path.unlink(missing_ok=True)
            if created_directory:
                with suppress(OSError):
                    path.parent.rmdir()
        raise
    view = RunView(
        run,
        RunState.CANCELLED,
        event.timestamp,
        reason,
        cancellation,
    )
    return RunCancellationResult(view, event, state, cancellation)
