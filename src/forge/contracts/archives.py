"""Terminal-decision and archive-inspection contracts."""

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


class AbandonmentRecord(GovernanceRecord):
    id: UUID
    owner_actor: Actor
    terminal_state: Literal[InitiativeLifecycleState.ABANDONED]
    abandonment_event_id: UUID
    reason: NonEmptyString
    unfinished_work_summary: NonEmptyString
    unresolved_risks: Annotated[tuple[NonEmptyString, ...], Field(min_length=1)]
    unfinished_step_ids: tuple[NonEmptyString, ...]
    current_artifact_revision_ids: tuple[UUID, ...]
    archive_reference: RepositoryRelativePath


class ArchiveManifest(VersionedModel):
    initiative_id: UUID
    terminal_state: InitiativeLifecycleState
    closure_record_id: UUID | None = None
    closure_event_id: UUID | None = None
    abandonment_record_id: UUID | None = None
    abandonment_event_id: UUID | None = None
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
        closure_ids = (self.closure_record_id, self.closure_event_id)
        abandonment_ids = (self.abandonment_record_id, self.abandonment_event_id)
        if self.terminal_state is InitiativeLifecycleState.CLOSED:
            if None in closure_ids or any(item is not None for item in abandonment_ids):
                raise ValueError("closed archives require only closure record and event IDs")
        elif self.terminal_state is InitiativeLifecycleState.ABANDONED:
            if None in abandonment_ids or any(item is not None for item in closure_ids):
                raise ValueError(
                    "abandoned archives require only abandonment record and event IDs"
                )
        else:
            raise ValueError("archives require a closed or abandoned terminal state")
        return self
