"""Logical artifact, immutable revision, and provenance contracts."""

from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, model_validator

from forge.contracts.actors import Actor
from forge.contracts.base import (
    GovernanceRecord,
    NonEmptyString,
    RepositoryRelativePath,
    Sha256Digest,
    SymbolicId,
    UtcDateTime,
    VersionedModel,
)


class ProvenanceRecord(VersionedModel):
    id: UUID
    source_type: SymbolicId
    source_reference: NonEmptyString
    actor_id: UUID
    run_id: UUID | None = None
    recorded_at: UtcDateTime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactRecord(GovernanceRecord):
    id: UUID
    role: SymbolicId
    title: NonEmptyString
    created_by: Actor
    current_revision: Annotated[int, Field(ge=1)]


class ArtifactRevision(GovernanceRecord):
    id: UUID
    artifact_id: UUID
    revision_number: Annotated[int, Field(ge=1)]
    path: RepositoryRelativePath
    content_digest: Sha256Digest
    byte_size: Annotated[int, Field(ge=0)]
    media_type: NonEmptyString
    provenance: ProvenanceRecord
    registration_event_id: UUID
    preserved_object_path: RepositoryRelativePath | None = None
    preservation_status: SymbolicId
    superseded_revision_number: Annotated[int, Field(ge=1)] | None = None
    stale_dependency_effects: tuple[UUID, ...] = ()

    @model_validator(mode="after")
    def validate_revision_chain(self) -> "ArtifactRevision":
        if (
            self.superseded_revision_number is not None
            and self.superseded_revision_number >= self.revision_number
        ):
            raise ValueError("superseded revision must precede the new revision")
        return self
