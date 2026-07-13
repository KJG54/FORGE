"""Portable, provider-neutral handoff and untrusted-result contracts."""

from typing import Any
from uuid import UUID

from pydantic import Field

from forge.contracts.base import (
    NonEmptyString,
    RepositoryRelativePath,
    Sha256Digest,
    SymbolicId,
    VersionedModel,
)


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
