"""Durable command-idempotency contracts bound to exact journal events."""

from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, model_validator

from forge.contracts.base import (
    ForgeModel,
    IdempotencyKey,
    Sha256Digest,
    SymbolicId,
    UtcDateTime,
    VersionedModel,
)


class IdempotencyEventMetadata(ForgeModel):
    key: IdempotencyKey
    command: SymbolicId
    request_digest: Sha256Digest


class IdempotencyEventReference(ForgeModel):
    event_id: UUID
    initiative_id: UUID
    sequence: Annotated[int, Field(ge=1)]
    event_hash: Sha256Digest


class IdempotencyReceipt(VersionedModel):
    key: IdempotencyKey
    command: SymbolicId
    request_digest: Sha256Digest
    completed_at: UtcDateTime
    events: Annotated[tuple[IdempotencyEventReference, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def event_references_are_unique(self) -> Self:
        event_ids = tuple(item.event_id for item in self.events)
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("idempotency receipt event references must be unique")
        return self
