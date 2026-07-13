"""Initiative identity and predecessor-link contracts."""

from uuid import UUID

from forge.contracts.base import (
    GovernanceRecord,
    NonEmptyString,
    SemanticVersion,
    SymbolicId,
    VersionedModel,
)
from forge.contracts.state import ExplanationProfile, InitiativeLifecycleState


class InitiativeReference(VersionedModel):
    initiative_id: UUID
    relationship: SymbolicId
    archive_reference: NonEmptyString | None = None


class Initiative(GovernanceRecord):
    id: UUID
    objective: NonEmptyString
    pack_id: SymbolicId
    pack_version: SemanticVersion
    workflow_id: SymbolicId
    workflow_version: SemanticVersion
    owner_identity_id: UUID
    creation_event_id: UUID
    lifecycle_state: InitiativeLifecycleState
    predecessor_references: tuple[InitiativeReference, ...] = ()
    explanation_profile: ExplanationProfile = ExplanationProfile.STANDARD
    declared_scope_summary: NonEmptyString
