"""Explicit active-snapshot recovery contracts."""

from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, model_validator

from forge.contracts.actors import Actor
from forge.contracts.base import (
    GovernanceRecord,
    NonEmptyString,
    RepositoryRelativePath,
    Sha256Digest,
)


class SnapshotCondition(StrEnum):
    MISSING = "missing"
    INVALID = "invalid"
    MISMATCHED = "mismatched"


class RecoveryRecord(GovernanceRecord):
    """Owner-attributed evidence for one explicit snapshot reconstruction."""

    id: UUID
    recovery_event_id: UUID
    actor: Actor
    reason: NonEmptyString
    source_journal_head_sequence: Annotated[int, Field(ge=1)]
    source_journal_head_hash: Sha256Digest
    snapshot_condition: SnapshotCondition
    preserved_snapshot_path: RepositoryRelativePath | None = None
    preserved_snapshot_digest: Sha256Digest | None = None
    preserved_snapshot_size: Annotated[int, Field(ge=0)] | None = None

    @model_validator(mode="after")
    def validate_preservation_fields(self) -> "RecoveryRecord":
        fields = (
            self.preserved_snapshot_path,
            self.preserved_snapshot_digest,
            self.preserved_snapshot_size,
        )
        if self.snapshot_condition is SnapshotCondition.MISSING:
            if any(value is not None for value in fields):
                raise ValueError("missing snapshots cannot have preserved snapshot fields")
        elif any(value is None for value in fields):
            raise ValueError("observed snapshots require complete preservation fields")
        return self
