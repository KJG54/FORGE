"""Executable capability declarations, separate from pack trust."""

import re
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, model_validator

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


class SideEffectClass(StrEnum):
    READ_ONLY = "read_only"
    REPOSITORY_WRITE = "repository_write"
    EXTERNAL_REVERSIBLE = "external_reversible"
    EXTERNAL_IRREVERSIBLE = "external_irreversible"
    SENSITIVE = "sensitive"


class CapabilityTrustState(StrEnum):
    DISABLED = "disabled"
    APPROVED_ONCE = "approved-once"
    APPROVED_FOR_VERSION = "approved-for-version"
    APPROVED_FOR_PROJECT = "approved-for-project"


class LocalValidatorDefinition(VersionedModel):
    """Tracked declaration for one disabled-by-default local validator profile."""

    id: SymbolicId
    version: SemanticVersion
    provider: NonEmptyString
    provider_version: NonEmptyString
    purpose: NonEmptyString
    executable: NonEmptyString
    arguments: tuple[NonEmptyString, ...] = ()
    working_directory: RepositoryRelativePath | None = None
    timeout_seconds: Annotated[int, Field(ge=1, le=3600)]
    expected_outputs: tuple[SymbolicId, ...]
    environment_access: tuple[NonEmptyString, ...] = ()
    side_effect_class: SideEffectClass

    @model_validator(mode="after")
    def validate_local_validator(self) -> "LocalValidatorDefinition":
        if not self.id.startswith("validator."):
            raise ValueError("local validator ID must start with 'validator.'")
        if not self.expected_outputs:
            raise ValueError("local validator must declare at least one expected output")
        if len(self.expected_outputs) != len(set(self.expected_outputs)):
            raise ValueError("local validator expected outputs must be unique")
        if len(self.environment_access) != len(set(self.environment_access)):
            raise ValueError("local validator environment access names must be unique")
        invalid_environment_names = [
            item
            for item in self.environment_access
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item) is None
        ]
        if invalid_environment_names:
            raise ValueError(
                "local validator environment access must contain variable names only"
            )
        invocation_parts = (self.executable, *self.arguments)
        if any("\x00" in item or "\r" in item or "\n" in item for item in invocation_parts):
            raise ValueError("local validator invocation parts must be single-line, NUL-free text")
        return self


class CapabilityDefinition(VersionedModel):
    id: SymbolicId
    version: SemanticVersion
    provider: NonEmptyString
    purpose: NonEmptyString
    input_schema_reference: NonEmptyString
    output_schema_reference: NonEmptyString
    executable: NonEmptyString | None = None
    arguments: tuple[NonEmptyString, ...] = ()
    working_directory_rules: tuple[RepositoryRelativePath, ...] = ()
    timeout_seconds: int | None = None
    side_effect_class: SideEffectClass
    authorization_class: SymbolicId
    trust_requirement: CapabilityTrustState = CapabilityTrustState.DISABLED
    verification_hooks: tuple[SymbolicId, ...] = ()


class CapabilityApproval(GovernanceRecord):
    """Owner authorization bound to an inspected executable invocation profile."""

    id: UUID
    capability_id: SymbolicId
    capability_version: SemanticVersion
    capability_digest: Sha256Digest
    provider: NonEmptyString
    provider_version: NonEmptyString
    executable: NonEmptyString
    arguments: tuple[NonEmptyString, ...]
    working_directory_rules: tuple[RepositoryRelativePath, ...]
    environment_access: tuple[NonEmptyString, ...]
    side_effect_class: SideEffectClass
    approval_scope: CapabilityTrustState
    rationale: NonEmptyString
    owner_actor: Actor
    approval_event_id: UUID

    @model_validator(mode="after")
    def validate_approval_scope(self) -> "CapabilityApproval":
        if self.approval_scope is CapabilityTrustState.DISABLED:
            raise ValueError("capability approval scope must grant execution")
        return self


class CapabilityRevocation(GovernanceRecord):
    """Immutable owner revocation of one prior capability approval."""

    id: UUID
    approval_id: UUID
    reason: NonEmptyString
    owner_actor: Actor
    revocation_event_id: UUID
