"""Owner-authorized pause and long-gap resume continuity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import uuid4

from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.state import InitiativeLifecycleState, MaterializedState
from forge.core.authorization import require_owner
from forge.core.lifecycle import load_active_initiative
from forge.core.transitions import INITIATIVE_PAUSED, INITIATIVE_RESUMED
from forge.errors import ConflictError, IntegrityError
from forge.storage.canonical import canonical_json_digest
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class PauseResult:
    event: AuditEvent
    state: MaterializedState


@dataclass(frozen=True)
class ResumeResult:
    event: AuditEvent
    state: MaterializedState
    summary: str


def pause_initiative(
    layout: RepositoryLayout,
    *,
    actor: Actor,
    reason: str,
) -> PauseResult:
    """Pause active work only at a safe governed boundary."""
    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "pause an initiative")
    reason = reason.strip()
    if not reason:
        raise ConflictError("Pause reason must not be empty")
    if active.state.active_run_ids:
        identifiers = ", ".join(str(item) for item in active.state.active_run_ids)
        raise ConflictError(
            "Pause requires no active governed runs; cancel or complete these runs first: "
            f"{identifiers}"
        )
    resumable_digest = canonical_json_digest(active.state.model_dump(mode="json"))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=active.state.journal_head_sequence + 1,
        timestamp=utc_now(),
        event_type=INITIATIVE_PAUSED,
        actor=actor,
        authorization_basis="configured owner explicitly paused the active initiative",
        affected_digests=(resumable_digest,),
        metadata={
            "reason": reason,
            "resumable_current_step_id": active.state.current_step_id,
            "resumable_next_actions": list(active.state.permitted_next_actions),
            "resumable_state_digest": resumable_digest,
        },
    )
    state = append_event_and_update_snapshot(
        layout.event_journal_file,
        layout.state_file,
        event,
        active.reducer,
    )
    return PauseResult(read_journal(layout.event_journal_file)[-1], state)


def _resumption_summary(
    *,
    objective: str,
    reason: str,
    current_step_id: str | None,
    step_states: dict[str, object],
    next_actions: tuple[str, ...],
) -> str:
    position = current_step_id or "no remaining workflow step"
    states = ", ".join(
        f"{step_id}={getattr(state, 'value', state)}"
        for step_id, state in step_states.items()
    )
    actions = ", ".join(next_actions) or "none"
    return (
        f"Resuming objective: {objective}. Pause reason: {reason}. "
        f"Current position: {position}. Step states: {states}. Next legal actions: {actions}."
    )


def resume_initiative(
    layout: RepositoryLayout,
    *,
    actor: Actor,
) -> ResumeResult:
    """Validate paused state and restore active operation with durable context."""
    active = load_active_initiative(layout, allow_paused=True)
    require_owner(actor, active.initiative.owner_identity_id, "resume an initiative")
    if active.state.lifecycle_state is not InitiativeLifecycleState.PAUSED:
        raise ConflictError("Only a paused initiative may be resumed")
    pause_event_id = active.state.active_pause_event_id
    if pause_event_id is None:
        raise IntegrityError("Paused state does not identify its governing pause event")
    pause_event = next(
        (event for event in read_journal(layout.event_journal_file) if event.id == pause_event_id),
        None,
    )
    if pause_event is None or pause_event.event_type != INITIATIVE_PAUSED:
        raise IntegrityError("Active pause event is missing from authoritative history")
    reason = pause_event.metadata.get("reason")
    raw_actions = pause_event.metadata.get("resumable_next_actions")
    action_items = cast("list[object]", raw_actions) if isinstance(raw_actions, list) else []
    if (
        not isinstance(reason, str)
        or not reason
        or not isinstance(raw_actions, list)
        or not all(isinstance(item, str) and item for item in action_items)
    ):
        raise IntegrityError("Active pause event has invalid resumable metadata")
    resumable_actions = tuple(cast("list[str]", raw_actions))
    summary = _resumption_summary(
        objective=active.initiative.objective,
        reason=reason,
        current_step_id=active.state.current_step_id,
        step_states=dict(active.state.step_states),
        next_actions=resumable_actions,
    )
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=active.state.journal_head_sequence + 1,
        timestamp=utc_now(),
        event_type=INITIATIVE_RESUMED,
        actor=actor,
        authorization_basis="configured owner explicitly resumed the paused initiative",
        metadata={
            "pause_event_id": str(pause_event_id),
            "resumed_current_step_id": active.state.current_step_id,
            "resumption_summary": summary,
        },
    )
    state = append_event_and_update_snapshot(
        layout.event_journal_file,
        layout.state_file,
        event,
        active.reducer,
    )
    return ResumeResult(read_journal(layout.event_journal_file)[-1], state, summary)
