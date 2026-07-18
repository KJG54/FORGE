"""Versioned provenance for explicit repository-lock remediation."""

from typing import Annotated
from uuid import UUID

from pydantic import Field

from forge.contracts.actors import Actor
from forge.contracts.base import (
    IdempotencyKey,
    NonEmptyString,
    RepositoryRelativePath,
    Sha256Digest,
    UtcDateTime,
    VersionedModel,
)


class LockRemediationRecord(VersionedModel):
    """Owner authorization and exact-byte provenance for one removed stale lock."""

    id: UUID
    project_id: UUID
    actor: Actor
    reason: NonEmptyString
    idempotency_key: IdempotencyKey
    request_digest: Sha256Digest
    authorized_at: UtcDateTime
    authorization_basis: NonEmptyString
    source_lock_path: RepositoryRelativePath
    source_lock_digest: Sha256Digest
    source_lock_size: Annotated[int, Field(ge=1)]
    source_owner_pid: Annotated[int, Field(ge=1)]
    source_owner_hostname: NonEmptyString
    source_owner_command: NonEmptyString
    source_owner_created_at: UtcDateTime
    source_owner_token_digest: Sha256Digest
    preserved_lock_path: RepositoryRelativePath
