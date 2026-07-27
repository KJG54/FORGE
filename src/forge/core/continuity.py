"""Owner-authorized pause and long-gap resume continuity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID, uuid4

from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.decisions import DecisionRecord
from forge.contracts.events import AuditEvent
from forge.contracts.state import InitiativeLifecycleState, MaterializedState
from forge.core.artifacts import list_artifacts
from forge.core.authorization import require_owner
from forge.core.decisions import list_decisions
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.scope_amendments import effective_scope_summary
from forge.core.transitions import (
    CANONICAL_RESUMPTION_SUMMARY_PROFILE,
    INITIATIVE_PAUSED,
    INITIATIVE_RESUMED,
)
from forge.core.verification import list_evidence
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


@dataclass(frozen=True)
class _ResumptionSnapshot:
    summary: str
    summary_digest: str
    affected_record_ids: tuple[UUID, ...]
    affected_digests: tuple[str, ...]


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


def _single_line(value: str) -> str:
    return " ".join(value.split())


def _active_pause(
    active: ActiveInitiative,
) -> tuple[AuditEvent, str, tuple[str, ...]]:
    pause_event_id = active.state.active_pause_event_id
    if pause_event_id is None:
        raise IntegrityError("Paused state does not identify its governing pause event")
    pause_event = next(
        (
            event
            for event in read_journal(active.layout.event_journal_file)
            if event.id == pause_event_id
        ),
        None,
    )
    if pause_event is None or pause_event.event_type != INITIATIVE_PAUSED:
        raise IntegrityError("Active pause event is missing from authoritative history")
    reason = pause_event.metadata.get("reason")
    raw_actions = pause_event.metadata.get("resumable_next_actions")
    action_items = cast("list[object]", raw_actions) if isinstance(raw_actions, list) else []
    if (
        not isinstance(reason, str)
        or not reason.strip()
        or not isinstance(raw_actions, list)
        or not all(isinstance(item, str) and item for item in action_items)
    ):
        raise IntegrityError("Active pause event has invalid resumable metadata")
    return pause_event, reason, tuple(cast("list[str]", raw_actions))


def _resumption_snapshot(
    *,
    active: ActiveInitiative,
    reason: str,
    next_actions: tuple[str, ...],
) -> _ResumptionSnapshot:
    step = next(
        (
            item
            for item in active.workflow.steps
            if item.id == active.state.current_step_id
        ),
        None,
    )
    position = (
        "no remaining workflow step"
        if step is None
        else (
            f"{step.id} ({active.state.step_states[step.id].value}) — "
            f"{_single_line(step.purpose)}"
        )
    )
    states = ", ".join(
        f"{step_definition.id}={active.state.step_states[step_definition.id].value}"
        for step_definition in active.workflow.steps
    )
    actions = ", ".join(next_actions) or "none"
    decisions_by_id = {decision.id: decision for decision in list_decisions(active.layout)}
    open_decisions: list[DecisionRecord] = []
    for decision_id in active.state.open_decision_ids:
        decision = decisions_by_id.get(decision_id)
        if decision is None:
            raise IntegrityError(
                f"Open decision {decision_id} lacks its canonical decision record"
            )
        open_decisions.append(decision)
    open_decisions.sort(key=lambda item: (item.event_sequence, str(item.id)))

    artifact_views = list_artifacts(active.layout)
    current_evidence = tuple(
        packet
        for packet in list_evidence(active.layout)
        if packet.id not in active.state.stale_record_ids
    )
    decision_lines = (
        "\n".join(
            f"- {decision.id} [{decision.decision_type}]: "
            f"{_single_line(decision.question)} -> "
            f"{_single_line(decision.chosen_outcome)}"
            for decision in open_decisions
        )
        or "- none"
    )
    artifact_lines = (
        "\n".join(
            f"- {view.artifact.role}: {view.current_revision.path} "
            f"(artifact {view.artifact.id}, revision {view.current_revision.id}"
            f"@{view.current_revision.revision_number}, "
            f"{view.current_revision.content_digest}, working copy "
            f"{'current' if view.working_copy_matches else 'changed'})"
            for view in artifact_views
        )
        or "- none"
    )
    evidence_lines = (
        "\n".join(
            f"- {packet.id}: {_single_line(packet.purpose)} "
            f"({len(packet.artifact_revision_ids)} artifacts, "
            f"{len(packet.check_result_ids)} checks, {len(packet.claim_ids)} claims, "
            f"{packet.packet_digest})"
            for packet in current_evidence
        )
        or "- none"
    )
    summary = (
        f"Resuming objective: {_single_line(active.initiative.objective)}.\n"
        f"Approved scope: {_single_line(effective_scope_summary(active))}.\n"
        f"Pause reason: {_single_line(reason)}.\n"
        f"Current position: {position}.\n"
        f"Step states: {states}.\n"
        f"Open decisions:\n{decision_lines}\n"
        f"Current artifacts:\n{artifact_lines}\n"
        f"Current evidence:\n{evidence_lines}\n"
        f"Next legal actions: {actions}."
    )
    summary_digest = canonical_json_digest({"summary": summary})
    affected_record_ids = tuple(
        dict.fromkeys(
            (
                *(
                    record_id
                    for view in artifact_views
                    for record_id in (
                        view.artifact.id,
                        view.current_revision.id,
                    )
                ),
                *(decision.id for decision in open_decisions),
                *(packet.id for packet in current_evidence),
            )
        )
    )
    affected_digests = tuple(
        dict.fromkeys(
            (
                *(view.current_revision.content_digest for view in artifact_views),
                *(
                    canonical_json_digest(decision.model_dump(mode="json"))
                    for decision in open_decisions
                ),
                *(packet.packet_digest for packet in current_evidence),
            )
        )
    )
    return _ResumptionSnapshot(
        summary,
        summary_digest,
        affected_record_ids,
        affected_digests,
    )


def build_resumption_summary(layout: RepositoryLayout) -> str:
    """Derive compact resume context from validated canonical records."""
    active = load_active_initiative(layout, allow_paused=True)
    if active.state.lifecycle_state is not InitiativeLifecycleState.PAUSED:
        raise ConflictError("A resumption summary requires a paused initiative")
    _pause_event, reason, resumable_actions = _active_pause(active)
    return _resumption_snapshot(
        active=active,
        reason=reason,
        next_actions=resumable_actions,
    ).summary


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
    pause_event, reason, resumable_actions = _active_pause(active)
    snapshot = _resumption_snapshot(
        active=active,
        reason=reason,
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
        affected_record_ids=(
            pause_event.id,
            *snapshot.affected_record_ids,
        ),
        affected_digests=(
            snapshot.summary_digest,
            *snapshot.affected_digests,
        ),
        metadata={
            "pause_event_id": str(pause_event.id),
            "resumed_current_step_id": active.state.current_step_id,
            "resumption_summary": snapshot.summary,
            "resumption_summary_digest": snapshot.summary_digest,
            "resumption_summary_profile": CANONICAL_RESUMPTION_SUMMARY_PROFILE,
        },
    )
    state = append_event_and_update_snapshot(
        layout.event_journal_file,
        layout.state_file,
        event,
        active.reducer,
    )
    return ResumeResult(
        read_journal(layout.event_journal_file)[-1],
        state,
        snapshot.summary,
    )
