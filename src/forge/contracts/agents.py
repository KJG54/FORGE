"""Provider-neutral context, handoff, and untrusted-result contracts."""

from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from forge.contracts.base import (
    ForgeModel,
    NonEmptyString,
    RepositoryRelativePath,
    Sha256Digest,
    SymbolicId,
    VersionedModel,
)
from forge.contracts.state import StepState


class AgentContextInput(ForgeModel):
    """One explicitly selected governed input, without embedding its file content."""

    role: SymbolicId
    path: RepositoryRelativePath
    content_digest: Sha256Digest
    media_type: NonEmptyString


class AgentContextStep(ForgeModel):
    id: SymbolicId
    state: StepState
    purpose: NonEmptyString
    instructions: NonEmptyString
    required_inputs: tuple[AgentContextInput, ...] = ()
    context_selection_rules: tuple[NonEmptyString, ...] = ()


class AgentContextDecision(ForgeModel):
    id: UUID
    decision_type: SymbolicId
    question: NonEmptyString
    chosen_outcome: NonEmptyString
    rationale: NonEmptyString


class AgentContextReturnContract(ForgeModel):
    contract: Literal["agent-result"] = "agent-result"
    manifest_filename: RepositoryRelativePath = "result.json"
    schema_filename: RepositoryRelativePath = "agent-result.schema.json"
    requirements: tuple[NonEmptyString, ...]


class CanonicalAgentContext(VersionedModel):
    """Authoritative generated context containing only the specification's categories."""

    objective: NonEmptyString
    active_step: AgentContextStep
    approved_scope: NonEmptyString
    relevant_constraints: tuple[NonEmptyString, ...] = ()
    relevant_decisions: tuple[AgentContextDecision, ...] = ()
    permitted_actions: tuple[NonEmptyString, ...] = ()
    prohibited_actions: tuple[NonEmptyString, ...]
    required_outputs: tuple[SymbolicId, ...]
    expected_evidence: tuple[NonEmptyString, ...]
    return_contract: AgentContextReturnContract
    known_blockers: tuple[NonEmptyString, ...] = ()


class ReturnedFile(VersionedModel):
    source_path: RepositoryRelativePath
    proposed_target_path: RepositoryRelativePath
    declared_digest: Sha256Digest | None = None
    media_type: NonEmptyString | None = None


class AgentHandoff(VersionedModel):
    id: UUID
    initiative_id: UUID
    step_id: SymbolicId
    objective: NonEmptyString
    approved_scope: NonEmptyString
    constraints: tuple[NonEmptyString, ...] = ()
    relevant_decision_ids: tuple[UUID, ...] = ()
    permitted_actions: tuple[NonEmptyString, ...]
    prohibited_actions: tuple[NonEmptyString, ...]
    required_outputs: tuple[SymbolicId, ...]
    return_manifest_schema: NonEmptyString
    verification_expectations: tuple[NonEmptyString, ...]


class AgentResult(VersionedModel):
    id: UUID
    source_run_or_handoff_id: UUID
    worker_claims: tuple[NonEmptyString, ...]
    returned_files: tuple[ReturnedFile, ...]
    declared_limitations: tuple[NonEmptyString, ...] = ()
    tool_metadata: dict[str, Any] = Field(default_factory=dict)
