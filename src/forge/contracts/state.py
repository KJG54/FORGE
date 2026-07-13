"""Canonical independent state dimensions and materialized-state contract."""

from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field

from forge.contracts.base import (
    NonEmptyString,
    SemanticVersion,
    Sha256Digest,
    SymbolicId,
    VersionedModel,
)


class RepositoryState(StrEnum):
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"


class InitiativeLifecycleState(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSING = "closing"
    CLOSED = "closed"
    ABANDONED = "abandoned"


class IntegrityState(StrEnum):
    HEALTHY = "healthy"
    RECOVERING = "recovering"
    INTEGRITY_ERROR = "integrity_error"


class StepState(StrEnum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    AWAITING_VERIFICATION = "awaiting_verification"
    AWAITING_ACCEPTANCE = "awaiting_acceptance"
    COMPLETED = "completed"
    INVALIDATED = "invalidated"
    SKIPPED = "skipped"


class RunState(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExplanationProfile(StrEnum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    GUIDED = "guided"
    MENTORED = "mentored"


class MaterializedState(VersionedModel):
    """Reconstructable snapshot shape; replay behavior arrives in Increment 2."""

    repository_state: RepositoryState
    initiative_id: UUID | None = None
    lifecycle_state: InitiativeLifecycleState | None = None
    integrity_state: IntegrityState = IntegrityState.HEALTHY
    workflow_id: SymbolicId | None = None
    workflow_version: SemanticVersion | None = None
    current_step_id: SymbolicId | None = None
    step_states: dict[SymbolicId, StepState] = Field(default_factory=dict)
    current_artifact_revisions: dict[UUID, Annotated[int, Field(ge=1)]] = Field(
        default_factory=dict
    )
    stale_record_ids: tuple[UUID, ...] = ()
    open_gate_ids: tuple[SymbolicId, ...] = ()
    open_decision_ids: tuple[UUID, ...] = ()
    active_run_ids: tuple[UUID, ...] = ()
    permitted_next_actions: tuple[NonEmptyString, ...] = ()
    journal_head_sequence: Annotated[int, Field(ge=0)] = 0
    journal_head_hash: Sha256Digest | None = None
