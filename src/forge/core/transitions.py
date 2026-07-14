"""Deterministic workflow reduction and transition invariant checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from forge.contracts.events import AuditEvent
from forge.contracts.state import (
    InitiativeLifecycleState,
    MaterializedState,
    RepositoryState,
    StepState,
)
from forge.contracts.workflows import StepDefinition, TransitionDefinition, WorkflowDefinition
from forge.core.authorization import authorize_transition, require_owner
from forge.errors import IntegrityError, TransitionError

INITIATIVE_CREATED = "initiative-created"
STEP_TRANSITIONED = "step-transitioned"
ARTIFACT_REGISTERED = "artifact-registered"
ARTIFACT_REVISED = "artifact-revised"
CLAIM_RECORDED = "claim-recorded"
CHECK_RECORDED = "check-recorded"
EVIDENCE_REGISTERED = "evidence-registered"
ACCEPTANCE_RECORDED = "acceptance-recorded"
ACCEPTANCE_REVOKED = "acceptance-revoked"
DECISION_RECORDED = "decision-recorded"
DECISION_SUPERSEDED = "decision-superseded"
RESULT_IMPORTED = "result-imported"


def _metadata_string(event: AuditEvent, key: str) -> str:
    value = event.metadata.get(key)
    if not isinstance(value, str) or not value:
        raise IntegrityError(f"Event {event.id} requires string metadata field {key!r}")
    return value


def _verified_conditions(event: AuditEvent) -> set[str]:
    value = event.metadata.get("verified_conditions", [])
    if not isinstance(value, list):
        raise IntegrityError(f"Event {event.id} has invalid verified_conditions metadata")
    items = cast("list[object]", value)
    if not all(isinstance(item, str) for item in items):
        raise IntegrityError(f"Event {event.id} has invalid verified_conditions metadata")
    return set(cast("list[str]", items))


def _metadata_string_list(event: AuditEvent, key: str) -> tuple[str, ...]:
    value = event.metadata.get(key, [])
    if not isinstance(value, list):
        raise IntegrityError(f"Event {event.id} has invalid {key} metadata")
    items = cast("list[object]", value)
    if not all(isinstance(item, str) and item for item in items):
        raise IntegrityError(f"Event {event.id} has invalid {key} metadata")
    return tuple(cast("list[str]", items))


def _metadata_uuid_list(event: AuditEvent, key: str) -> tuple[UUID, ...]:
    values = _metadata_string_list(event, key)
    try:
        return tuple(UUID(value) for value in values)
    except ValueError as error:
        raise IntegrityError(f"Event {event.id} has invalid UUIDs in {key}") from error


@dataclass(frozen=True)
class WorkflowStateReducer:
    workflow: WorkflowDefinition
    owner_identity_id: UUID

    def _step(self, step_id: str) -> StepDefinition:
        for step in self.workflow.steps:
            if step.id == step_id:
                return step
        raise IntegrityError(f"Journal references unknown workflow step {step_id!r}")

    def _transition(self, transition_id: str) -> TransitionDefinition:
        for transition in self.workflow.transitions:
            if transition.id == transition_id:
                return transition
        raise IntegrityError(f"Journal references unknown transition {transition_id!r}")

    def _next_actions(self, states: dict[str, StepState]) -> tuple[str, ...]:
        actions: list[str] = []
        for step in self.workflow.steps:
            state = states[step.id]
            if state is StepState.READY:
                actions.append(f"begin:{step.id}")
            elif state is StepState.IN_PROGRESS:
                actions.append(f"complete:{step.id}")
            elif state is StepState.AWAITING_VERIFICATION:
                actions.append(f"verify:{step.id}")
            elif state is StepState.AWAITING_ACCEPTANCE:
                actions.append(f"acceptance-record:{step.id}")
            elif state is StepState.INVALIDATED:
                actions.append(f"begin:{step.id}")
        return tuple(actions)

    def _current_step(self, states: dict[str, StepState]) -> str | None:
        for step in self.workflow.steps:
            if states[step.id] not in {StepState.COMPLETED, StepState.SKIPPED}:
                return step.id
        return None

    def _initial_state(self, event: AuditEvent) -> MaterializedState:
        require_owner(event.actor, self.owner_identity_id, "create an initiative")
        if _metadata_string(event, "workflow_id") != self.workflow.id:
            raise IntegrityError("Initiative event does not match the locked workflow ID")
        if _metadata_string(event, "workflow_version") != self.workflow.version:
            raise IntegrityError("Initiative event does not match the locked workflow version")
        states = {step.id: StepState.PENDING for step in self.workflow.steps}
        first = self.workflow.steps[0]
        states[first.id] = StepState.READY
        return MaterializedState(
            repository_state=RepositoryState.INITIALIZED,
            initiative_id=event.initiative_id,
            lifecycle_state=InitiativeLifecycleState.ACTIVE,
            workflow_id=self.workflow.id,
            workflow_version=self.workflow.version,
            current_step_id=first.id,
            step_states=states,
            open_gate_ids=tuple(gate.id for gate in self.workflow.required_gates),
            permitted_next_actions=self._next_actions(states),
        )

    def _apply_step_transition(
        self,
        state: MaterializedState,
        event: AuditEvent,
    ) -> MaterializedState:
        if state.lifecycle_state is not InitiativeLifecycleState.ACTIVE:
            raise IntegrityError("Normal step transitions require an active initiative")
        step = self._step(_metadata_string(event, "step_id"))
        transition = self._transition(_metadata_string(event, "transition_id"))
        if transition.id not in step.allowed_transitions:
            raise IntegrityError(
                f"Transition {transition.id} is not allowed for workflow step {step.id}"
            )
        if event.event_type != transition.event_type:
            raise IntegrityError(
                f"Event type {event.event_type} does not match transition {transition.event_type}"
            )
        current = state.step_states.get(step.id)
        if current is not transition.source_state:
            raise IntegrityError(
                f"Transition {transition.id} expected {transition.source_state.value} for "
                f"step {step.id}, found {current}"
            )
        recorded_source = _metadata_string(event, "source_state")
        recorded_destination = _metadata_string(event, "destination_state")
        if recorded_source != transition.source_state.value:
            raise IntegrityError("Event source state does not match locked transition")
        if recorded_destination != transition.destination_state.value:
            raise IntegrityError("Event destination state does not match locked transition")
        missing_conditions = set(transition.conditions) - _verified_conditions(event)
        if missing_conditions:
            raise IntegrityError(
                f"Transition {transition.id} lacks verified conditions: "
                f"{sorted(missing_conditions)}"
            )
        authorize_transition(event.actor, self.owner_identity_id, step, transition)

        states = dict(state.step_states)
        states[step.id] = transition.destination_state
        if transition.destination_state is StepState.COMPLETED:
            for candidate in self.workflow.steps:
                if states[candidate.id] is not StepState.PENDING:
                    continue
                if all(
                    states[required] is StepState.COMPLETED
                    for required in candidate.prerequisites
                ):
                    states[candidate.id] = StepState.READY

        active_runs = list(state.active_run_ids)
        if transition.destination_state is StepState.IN_PROGRESS:
            if event.run_id is None:
                raise IntegrityError("Beginning a step requires a run ID")
            active_runs.append(event.run_id)
        elif transition.source_state is StepState.IN_PROGRESS and event.run_id is not None:
            active_runs = [run_id for run_id in active_runs if run_id != event.run_id]
        return state.model_copy(
            update={
                "step_states": states,
                "current_step_id": self._current_step(states),
                "active_run_ids": tuple(active_runs),
                "permitted_next_actions": self._next_actions(states),
            }
        )

    def _apply_artifact_event(
        self,
        state: MaterializedState,
        event: AuditEvent,
    ) -> MaterializedState:
        artifact_value = _metadata_string(event, "artifact_id")
        try:
            artifact_id = UUID(artifact_value)
        except ValueError as error:
            raise IntegrityError(f"Event {event.id} has an invalid artifact ID") from error
        revision_value = event.metadata.get("revision_number")
        if not isinstance(revision_value, int) or isinstance(revision_value, bool):
            raise IntegrityError(f"Event {event.id} has an invalid artifact revision number")
        revisions = dict(state.current_artifact_revisions)
        current = revisions.get(artifact_id)
        if event.event_type == ARTIFACT_REGISTERED:
            if current is not None or revision_value != 1:
                raise IntegrityError("Artifact registration must create revision 1 exactly once")
        elif current is None or revision_value != current + 1:
            raise IntegrityError("Artifact revision event is not contiguous with current state")
        revisions[artifact_id] = revision_value
        if event.event_type == ARTIFACT_REVISED:
            return self._apply_invalidation(
                state.model_copy(update={"current_artifact_revisions": revisions}),
                event,
            )
        return state.model_copy(update={"current_artifact_revisions": revisions})

    def _apply_invalidation(
        self,
        state: MaterializedState,
        event: AuditEvent,
    ) -> MaterializedState:
        invalidated_steps = set(_metadata_string_list(event, "invalidated_step_ids"))
        reset_steps = set(_metadata_string_list(event, "reset_step_ids"))
        known_steps = {step.id for step in self.workflow.steps}
        if invalidated_steps & reset_steps or not (invalidated_steps | reset_steps) <= known_steps:
            raise IntegrityError(f"Event {event.id} has invalid workflow invalidation metadata")
        states = dict(state.step_states)
        for step_id in invalidated_steps:
            states[step_id] = StepState.INVALIDATED
        for step_id in reset_steps:
            states[step_id] = StepState.PENDING
        stale_ids = set(state.stale_record_ids)
        stale_ids.update(_metadata_uuid_list(event, "stale_record_ids"))
        open_decisions = tuple(
            decision_id
            for decision_id in state.open_decision_ids
            if decision_id not in stale_ids
        )
        invalidated_runs = set(_metadata_uuid_list(event, "invalidated_run_ids"))
        if not invalidated_runs <= set(state.active_run_ids):
            raise IntegrityError(f"Event {event.id} invalidates a run that is not active")
        active_runs = tuple(
            run_id for run_id in state.active_run_ids if run_id not in invalidated_runs
        )
        return state.model_copy(
            update={
                "step_states": states,
                "current_step_id": self._current_step(states),
                "stale_record_ids": tuple(sorted(stale_ids, key=str)),
                "active_run_ids": active_runs,
                "open_decision_ids": open_decisions,
                "permitted_next_actions": self._next_actions(states),
            }
        )

    def _apply_decision_event(
        self,
        state: MaterializedState,
        event: AuditEvent,
    ) -> MaterializedState:
        try:
            decision_id = UUID(_metadata_string(event, "decision_id"))
        except ValueError as error:
            raise IntegrityError(f"Event {event.id} has an invalid decision ID") from error
        open_decisions = list(state.open_decision_ids)
        stale_ids = set(state.stale_record_ids)
        if event.event_type == DECISION_RECORDED:
            if decision_id in open_decisions:
                raise IntegrityError(f"Decision {decision_id} was recorded more than once")
            open_decisions.append(decision_id)
        else:
            try:
                prior_id = UUID(_metadata_string(event, "prior_decision_id"))
            except ValueError as error:
                raise IntegrityError(
                    f"Event {event.id} has an invalid prior decision ID"
                ) from error
            if prior_id not in open_decisions:
                raise IntegrityError(f"Decision {prior_id} is not active for supersession")
            open_decisions = [item for item in open_decisions if item != prior_id]
            open_decisions.append(decision_id)
            stale_ids.add(prior_id)
        return state.model_copy(
            update={
                "open_decision_ids": tuple(open_decisions),
                "stale_record_ids": tuple(sorted(stale_ids, key=str)),
            }
        )

    def _apply_import_event(
        self,
        state: MaterializedState,
        event: AuditEvent,
    ) -> MaterializedState:
        value = event.metadata.get("artifact_updates")
        if not isinstance(value, list) or not value:
            raise IntegrityError(f"Import event {event.id} has no artifact updates")
        updates = cast("list[object]", value)
        revisions = dict(state.current_artifact_revisions)
        seen: set[UUID] = set()
        for raw in updates:
            if not isinstance(raw, dict):
                raise IntegrityError(f"Import event {event.id} has invalid artifact metadata")
            item = cast("dict[object, object]", raw)
            artifact_value = item.get("artifact_id")
            revision_value = item.get("revision_number")
            action = item.get("action")
            if (
                not isinstance(artifact_value, str)
                or not isinstance(revision_value, int)
                or isinstance(revision_value, bool)
                or action not in {"create", "revise"}
            ):
                raise IntegrityError(f"Import event {event.id} has invalid artifact metadata")
            try:
                artifact_id = UUID(artifact_value)
            except ValueError as error:
                raise IntegrityError(
                    f"Import event {event.id} has an invalid artifact ID"
                ) from error
            if artifact_id in seen:
                raise IntegrityError(f"Import event {event.id} updates an artifact twice")
            seen.add(artifact_id)
            current = revisions.get(artifact_id)
            if action == "create":
                if current is not None or revision_value != 1:
                    raise IntegrityError("Imported artifact creation must register revision 1")
            elif current is None or revision_value != current + 1:
                raise IntegrityError("Imported artifact revision is not contiguous")
            revisions[artifact_id] = revision_value
        return self._apply_invalidation(
            state.model_copy(update={"current_artifact_revisions": revisions}),
            event,
        )

    def __call__(
        self,
        state: MaterializedState | None,
        event: AuditEvent,
    ) -> MaterializedState:
        if state is None:
            if event.event_type != INITIATIVE_CREATED or event.sequence != 1:
                raise IntegrityError("The first initiative event must be initiative-created")
            return self._initial_state(event)
        if event.event_type == STEP_TRANSITIONED:
            return self._apply_step_transition(state, event)
        if event.event_type in {ARTIFACT_REGISTERED, ARTIFACT_REVISED}:
            return self._apply_artifact_event(state, event)
        if event.event_type in {DECISION_RECORDED, DECISION_SUPERSEDED}:
            return self._apply_decision_event(state, event)
        if event.event_type == ACCEPTANCE_REVOKED:
            return self._apply_invalidation(state, event)
        if event.event_type == RESULT_IMPORTED:
            return self._apply_import_event(state, event)
        return state


def resolve_transition(
    workflow: WorkflowDefinition,
    step_id: str,
    transition_id: str,
    current_state: StepState,
) -> tuple[StepDefinition, TransitionDefinition]:
    step = next((item for item in workflow.steps if item.id == step_id), None)
    if step is None:
        raise TransitionError(f"Unknown workflow step {step_id!r}")
    if transition_id not in step.allowed_transitions:
        raise TransitionError(f"Transition {transition_id!r} is not allowed for step {step_id}")
    transition = next(
        (item for item in workflow.transitions if item.id == transition_id),
        None,
    )
    if transition is None:
        raise TransitionError(f"Unknown workflow transition {transition_id!r}")
    if current_state is not transition.source_state:
        raise TransitionError(
            f"Step {step_id} is {current_state.value}; transition {transition_id} requires "
            f"{transition.source_state.value}"
        )
    return step, transition
