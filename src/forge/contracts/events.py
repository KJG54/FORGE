"""Canonical event shape; append and replay behavior begin in Increment 2."""

from typing import Annotated, Any
from uuid import UUID

from pydantic import Field

from forge.contracts.actors import Actor
from forge.contracts.base import (
    NonEmptyString,
    Sha256Digest,
    SymbolicId,
    UtcDateTime,
    VersionedModel,
)


class AuditEvent(VersionedModel):
    id: UUID
    initiative_id: UUID
    sequence: Annotated[int, Field(ge=1)]
    timestamp: UtcDateTime
    event_type: SymbolicId
    actor: Actor
    correlation_id: UUID | None = None
    run_id: UUID | None = None
    authorization_basis: NonEmptyString
    affected_record_ids: tuple[UUID, ...] = ()
    affected_digests: tuple[Sha256Digest, ...] = ()
    previous_event_hash: Sha256Digest | None = None
    event_hash: Sha256Digest | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
