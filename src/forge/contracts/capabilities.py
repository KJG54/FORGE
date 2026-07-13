"""Executable capability declarations, separate from pack trust."""

from enum import StrEnum

from forge.contracts.base import (
    NonEmptyString,
    RepositoryRelativePath,
    SemanticVersion,
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
