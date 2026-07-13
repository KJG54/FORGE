"""Append-only decision and governance-change contracts."""

from enum import StrEnum
from uuid import UUID

from forge.contracts.actors import Actor
from forge.contracts.base import GovernanceRecord, NonEmptyString, Sha256Digest, SymbolicId


class DecisionStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class DecisionRecord(GovernanceRecord):
    id: UUID
    decision_type: SymbolicId
    question: NonEmptyString
    considered_options: tuple[NonEmptyString, ...]
    chosen_outcome: NonEmptyString
    rationale: NonEmptyString
    actor: Actor
    affected_record_ids: tuple[UUID, ...] = ()
    bound_digests: tuple[Sha256Digest, ...] = ()
    status: DecisionStatus = DecisionStatus.ACTIVE


class DecisionSupersession(GovernanceRecord):
    id: UUID
    prior_decision_id: UUID
    replacement_decision_id: UUID
    rationale: NonEmptyString
    actor: Actor


class ApprovalRevocation(GovernanceRecord):
    id: UUID
    approval_id: UUID
    reason: NonEmptyString
    actor: Actor


class ScopeAmendment(GovernanceRecord):
    id: UUID
    changed_scope: NonEmptyString
    rationale: NonEmptyString
    affected_requirements: tuple[SymbolicId, ...]
    affected_artifact_ids: tuple[UUID, ...] = ()
    invalidated_check_ids: tuple[UUID, ...] = ()
    invalidated_gate_ids: tuple[SymbolicId, ...] = ()
    invalidated_acceptance_ids: tuple[UUID, ...] = ()
    workflow_return_step_id: SymbolicId
    actor: Actor


class WorkflowDeviation(GovernanceRecord):
    id: UUID
    workflow_id: SymbolicId
    declared_behavior: NonEmptyString
    actual_behavior: NonEmptyString
    rationale: NonEmptyString
    review_requirement: NonEmptyString
    actor: Actor


class EmergencyOverride(GovernanceRecord):
    id: UUID
    affected_requirement_or_gate: NonEmptyString
    rationale: NonEmptyString
    residual_risk: NonEmptyString
    permanence: SymbolicId
    review_requirement: NonEmptyString
    actor: Actor


class RiskAcceptance(GovernanceRecord):
    id: UUID
    risk: NonEmptyString
    rationale: NonEmptyString
    residual_impact: NonEmptyString
    review_condition: NonEmptyString | None = None
    actor: Actor
