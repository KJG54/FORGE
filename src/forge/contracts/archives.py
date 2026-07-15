"""Successful-closure and archive-inspection contracts."""

from __future__ import annotations

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from forge.contracts.actors import Actor
from forge.contracts.base import (
    GovernanceRecord,
    NonEmptyString,
    RepositoryRelativePath,
    Sha256Digest,
    UtcDateTime,
    VersionedModel,
)
from forge.contracts.state import InitiativeLifecycleState


class ArchivedFile(VersionedModel):
    path: RepositoryRelativePath
    content_digest: Sha256Digest
    byte_size: Annotated[int, Field(ge=0)]


class ArchivedObjectReference(VersionedModel):
    artifact_revision_id: UUID
    content_digest: Sha256Digest
    byte_size: Annotated[int, Field(ge=0)]
    preserved_object_path: RepositoryRelativePath
    accepted: bool


class ClosureRecord(GovernanceRecord):
    id: UUID
    owner_actor: Actor
    terminal_state: Literal[InitiativeLifecycleState.CLOSED]
    closure_event_id: UUID
    closing_summary: NonEmptyString
    final_acceptance_ids: tuple[UUID, ...]
    current_artifact_revision_ids: tuple[UUID, ...]
    accepted_artifact_revision_ids: tuple[UUID, ...]
    archive_reference: RepositoryRelativePath


class ArchiveManifest(VersionedModel):
    initiative_id: UUID
    terminal_state: Literal[InitiativeLifecycleState.CLOSED]
    closure_record_id: UUID
    closure_event_id: UUID
    created_at: UtcDateTime
    files: tuple[ArchivedFile, ...]
    object_references: tuple[ArchivedObjectReference, ...]
    archive_digest: Sha256Digest
    preliminary: bool = True
    limitations: tuple[NonEmptyString, ...] = (
        "M1 archives are not hash-chained and do not claim interruption recovery",
    )

    @model_validator(mode="after")
    def validate_guarantee_label(self) -> Self:
        if self.preliminary and not self.limitations:
            raise ValueError("preliminary archives must declare their limitations")
        if not self.preliminary and self.limitations:
            raise ValueError("hardened archives must not carry preliminary limitations")
        return self
