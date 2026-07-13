"""Declarative, domain-neutral workflow contracts."""

from enum import StrEnum

from pydantic import Field, model_validator

from forge.contracts.actors import ActorType
from forge.contracts.base import (
    NonEmptyString,
    SemanticVersion,
    SymbolicId,
    VersionedModel,
)
from forge.contracts.state import StepState


class CancellationBehavior(StrEnum):
    RETURN_TO_READY = "return_to_ready"
    BLOCK_FOR_OWNER_REVIEW = "block_for_owner_review"


class Gate(VersionedModel):
    id: SymbolicId
    purpose: NonEmptyString
    authority_requirement: SymbolicId
    required_artifact_classes: tuple[SymbolicId, ...] = ()
    required_evidence_classes: tuple[SymbolicId, ...] = ()
    required_check_ids: tuple[SymbolicId, ...] = ()


class TransitionDefinition(VersionedModel):
    id: SymbolicId
    source_state: StepState
    destination_state: StepState
    conditions: tuple[NonEmptyString, ...] = ()
    authority_requirement: SymbolicId
    invalidation_effects: tuple[NonEmptyString, ...] = ()
    event_type: SymbolicId


class StepDefinition(VersionedModel):
    id: SymbolicId
    purpose: NonEmptyString
    instructions: NonEmptyString
    prerequisites: tuple[SymbolicId, ...] = ()
    required_inputs: tuple[SymbolicId, ...] = ()
    required_outputs: tuple[SymbolicId, ...] = ()
    claim_requirements: tuple[SymbolicId, ...] = ()
    check_requirements: tuple[SymbolicId, ...] = ()
    acceptance_requirements: tuple[SymbolicId, ...] = ()
    allowed_actors: tuple[ActorType, ...]
    allowed_transitions: tuple[SymbolicId, ...]
    cancellation_behavior: CancellationBehavior
    context_selection_rules: tuple[NonEmptyString, ...] = ()


class WorkflowDefinition(VersionedModel):
    id: SymbolicId
    version: SemanticVersion
    pack_id: SymbolicId
    name: NonEmptyString
    description: NonEmptyString
    steps: tuple[StepDefinition, ...]
    transitions: tuple[TransitionDefinition, ...]
    required_gates: tuple[Gate, ...] = ()
    required_artifact_classes: tuple[SymbolicId, ...] = ()
    required_evidence_classes: tuple[SymbolicId, ...] = ()
    explanation_content: dict[str, NonEmptyString] = Field(default_factory=dict)
    compatibility_constraints: tuple[NonEmptyString, ...] = ()

    @model_validator(mode="after")
    def validate_identifiers(self) -> "WorkflowDefinition":
        collections = {
            "step": [item.id for item in self.steps],
            "transition": [item.id for item in self.transitions],
            "gate": [item.id for item in self.required_gates],
        }
        for label, identifiers in collections.items():
            if len(identifiers) != len(set(identifiers)):
                raise ValueError(f"{label} identifiers must be unique")

        step_ids = set(collections["step"])
        transition_ids = set(collections["transition"])
        for step in self.steps:
            missing_prerequisites = set(step.prerequisites) - step_ids
            if missing_prerequisites:
                raise ValueError(
                    f"step {step.id!r} has unknown prerequisites: "
                    f"{sorted(missing_prerequisites)}"
                )
            missing_transitions = set(step.allowed_transitions) - transition_ids
            if missing_transitions:
                raise ValueError(
                    f"step {step.id!r} has unknown transitions: {sorted(missing_transitions)}"
                )
        return self
