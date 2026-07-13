"""Declarative pack manifest and data-trust contracts."""

from enum import StrEnum
from uuid import UUID

from forge.contracts.actors import Actor
from forge.contracts.base import (
    GovernanceRecord,
    NonEmptyString,
    RepositoryRelativePath,
    SemanticVersion,
    Sha256Digest,
    SymbolicId,
    VersionedModel,
)


class PackTrustState(StrEnum):
    UNTRUSTED = "untrusted"
    TRUSTED_DATA = "trusted-data"


class PackManifest(VersionedModel):
    id: SymbolicId
    version: SemanticVersion
    schema_compatibility: tuple[NonEmptyString, ...]
    provided_workflow_ids: tuple[SymbolicId, ...]
    template_paths: tuple[RepositoryRelativePath, ...] = ()
    explanation_paths: tuple[RepositoryRelativePath, ...] = ()
    data_resource_paths: tuple[RepositoryRelativePath, ...] = ()
    declared_capability_ids: tuple[SymbolicId, ...] = ()
    integrity_digest: Sha256Digest


class PackTrustDecision(GovernanceRecord):
    id: UUID
    pack_id: SymbolicId
    pack_version: SemanticVersion
    trust_state: PackTrustState
    rationale: NonEmptyString
    actor: Actor
