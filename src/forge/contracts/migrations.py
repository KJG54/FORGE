"""Explicit, owner-authorized persisted-state migration contracts."""

from typing import Annotated
from uuid import UUID

from pydantic import Field

from forge.contracts.actors import Actor
from forge.contracts.base import (
    GovernanceRecord,
    NonEmptyString,
    RepositoryRelativePath,
    Sha256Digest,
    SymbolicId,
)


class MigrationRecord(GovernanceRecord):
    """Provenance for one registered migration applied to active state."""

    id: UUID
    migration_event_id: UUID
    migration_id: SymbolicId
    owner_actor: Actor
    migration_actor: Actor
    source_schema_version: NonEmptyString
    target_schema_version: NonEmptyString
    source_format: NonEmptyString
    target_format: NonEmptyString
    source_event_count: Annotated[int, Field(ge=1)]
    preserved_source_path: RepositoryRelativePath
    preserved_source_digest: Sha256Digest
    preserved_source_size: Annotated[int, Field(ge=1)]
