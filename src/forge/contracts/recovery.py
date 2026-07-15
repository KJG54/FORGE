"""Explicit active-state recovery contracts."""

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


class JournalDamageCondition(StrEnum):
    TRUNCATED_FINAL_RECORD = "truncated_final_record"


class JournalRecoverySnapshotCondition(StrEnum):
    HEALTHY = "healthy"
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


class JournalRecoveryRecord(GovernanceRecord):
    """Owner-attributed provenance for one conservative final-record truncation recovery."""

    id: UUID
    recovery_event_id: UUID
    actor: Actor
    reason: NonEmptyString
    damage_condition: JournalDamageCondition
    valid_event_count: Annotated[int, Field(ge=1)]
    source_journal_head_sequence: Annotated[int, Field(ge=1)]
    source_journal_head_hash: Sha256Digest
    preserved_journal_path: RepositoryRelativePath
    preserved_journal_digest: Sha256Digest
    preserved_journal_size: Annotated[int, Field(ge=1)]
    valid_prefix_size: Annotated[int, Field(ge=1)]
    truncated_tail_digest: Sha256Digest
    truncated_tail_size: Annotated[int, Field(ge=1)]
    snapshot_condition: JournalRecoverySnapshotCondition
    preserved_snapshot_path: RepositoryRelativePath | None = None
    preserved_snapshot_digest: Sha256Digest | None = None
    preserved_snapshot_size: Annotated[int, Field(ge=0)] | None = None

    @model_validator(mode="after")
    def validate_recovery_evidence(self) -> "JournalRecoveryRecord":
        if self.source_journal_head_sequence != self.valid_event_count:
            raise ValueError("journal recovery head sequence must equal valid event count")
        if self.valid_prefix_size >= self.preserved_journal_size:
            raise ValueError("journal recovery requires a non-empty truncated tail")
        if self.valid_prefix_size + self.truncated_tail_size != self.preserved_journal_size:
            raise ValueError("journal recovery byte ranges must cover the preserved journal")
        snapshot_fields = (
            self.preserved_snapshot_path,
            self.preserved_snapshot_digest,
            self.preserved_snapshot_size,
        )
        if self.snapshot_condition is JournalRecoverySnapshotCondition.MISSING:
            if any(value is not None for value in snapshot_fields):
                raise ValueError("missing snapshots cannot have preserved snapshot fields")
        elif any(value is None for value in snapshot_fields):
            raise ValueError("observed snapshots require complete preservation fields")
        return self
