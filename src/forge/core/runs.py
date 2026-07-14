"""Immutable run inspection and event-backed cancellation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from forge.contracts.actors import Actor, ActorType
from forge.contracts.base import utc_now
from forge.contracts.capabilities import SideEffectClass
from forge.contracts.events import AuditEvent
from forge.contracts.runs import RunRecord
from forge.contracts.state import MaterializedState, RunState, StepState
from forge.contracts.workflows import CancellationBehavior
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.transitions import RUN_CANCELLED, STEP_TRANSITIONED
from forge.errors import AuthorizationError, ConflictError, IntegrityError
from forge.storage.journal import read_journal
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class RunView:
    record: RunRecord
    status: RunState
    ended_at: datetime | None = None
    cancellation_details: str | None = None


@dataclass(frozen=True)
class RunCancellationResult:
    run: RunView
    event: AuditEvent
    state: MaterializedState


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
    terminal = [
        event
        for event in read_journal(active.layout.event_journal_file)
        if event.run_id == run.id
        and (
            event.event_type == RUN_CANCELLED
            or (
                event.event_type == STEP_TRANSITIONED
                and event.metadata.get("source_state") == StepState.IN_PROGRESS.value
            )
        )
    ]
    if len(terminal) > 1:
        raise IntegrityError(f"Run {run.id} has multiple terminal events")
    if not terminal:
        if run.id not in active.state.active_run_ids:
            raise IntegrityError(f"Run {run.id} is neither active nor terminal")
        return RunView(run, RunState.RUNNING)
    event = terminal[0]
    if event.event_type == RUN_CANCELLED:
        reason = event.metadata.get("reason")
        if not isinstance(reason, str) or not reason:
            raise IntegrityError(f"Run cancellation {event.id} has no reason")
        return RunView(run, RunState.CANCELLED, event.timestamp, reason)
    return RunView(run, RunState.SUCCEEDED, event.timestamp)


def list_runs(layout: RepositoryLayout) -> tuple[RunView, ...]:
    active = load_active_initiative(layout, allow_paused=True)
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
    active = load_active_initiative(layout)
    reason = reason.strip()
    if not reason:
        raise ConflictError("Run cancellation reason must not be empty")
    run = load_record(active.layout.governed_run_directory / f"{run_id}.json", RunRecord)
    if run_id not in active.state.active_run_ids:
        raise ConflictError(f"Run {run_id} is not active")
    is_owner = (
        actor.actor_type is ActorType.OWNER
        and actor.id == active.initiative.owner_identity_id
    )
    if actor != run.worker and not is_owner:
        raise AuthorizationError("Only the run worker or repository owner may cancel a run")
    step = next((item for item in active.workflow.steps if item.id == run.step_id), None)
    if step is None or active.state.step_states.get(run.step_id) is not StepState.IN_PROGRESS:
        raise IntegrityError(f"Active run {run_id} does not match an in-progress step")
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
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=active.state.journal_head_sequence + 1,
        timestamp=utc_now(),
        event_type=RUN_CANCELLED,
        actor=actor,
        run_id=run_id,
        authorization_basis="run worker or repository owner explicitly cancelled active work",
        affected_record_ids=(run_id,),
        metadata={
            "destination_state": destination.value,
            "reason": reason,
            "source_state": StepState.IN_PROGRESS.value,
            "step_id": run.step_id,
        },
    )
    state = append_event_and_update_snapshot(
        active.layout.event_journal_file,
        active.layout.state_file,
        event,
        active.reducer,
    )
    view = RunView(run, RunState.CANCELLED, event.timestamp, reason)
    return RunCancellationResult(view, event, state)
