"""Durable command-idempotency contracts bound to exact journal events."""

from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, model_validator

from forge.contracts.actors import Actor
from forge.contracts.base import (
    ForgeModel,
    GovernanceRecord,
    IdempotencyKey,
    NonEmptyString,
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


class CommandRecoveryRecord(GovernanceRecord):
    """Owner-attributed provenance for one reconstructed completion receipt."""

    id: UUID
    recovery_event_id: UUID
    actor: Actor
    reason: NonEmptyString
    interrupted_key: IdempotencyKey
    interrupted_command: SymbolicId
    interrupted_request_digest: Sha256Digest
    receipt_completed_at: UtcDateTime
    recovered_events: Annotated[
        tuple[IdempotencyEventReference, ...], Field(min_length=1)
    ]
    recovered_receipt_digest: Sha256Digest

    @model_validator(mode="after")
    def recovered_event_references_are_unique(self) -> Self:
        event_ids = tuple(item.event_id for item in self.recovered_events)
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("command recovery event references must be unique")
        return self
