"""Bounded work-attempt records."""

from uuid import UUID

from pydantic import Field, field_validator

from forge.contracts.actors import Actor
from forge.contracts.base import (
    GovernanceRecord,
    NonEmptyString,
    RepositoryRelativePath,
    Sha256Digest,
    SymbolicId,
    UtcDateTime,
)
from forge.contracts.capabilities import SideEffectClass
from forge.contracts.state import RunState, StepState
from forge.contracts.workflows import CancellationBehavior


class RunRecord(GovernanceRecord):
    id: UUID
    step_id: SymbolicId
    worker: Actor
    adapter_reference: NonEmptyString | None = None
    capability_ids: tuple[SymbolicId, ...] = ()
    capability_approval_ids: tuple[UUID, ...] = ()
    side_effect_class: SideEffectClass
    status: RunState
    started_at: UtcDateTime | None = None
    ended_at: UtcDateTime | None = None
    input_context_digest: Sha256Digest
    output_manifest_path: RepositoryRelativePath | None = None
    exit_metadata: dict[str, str]
    cancellation_details: NonEmptyString | None = None


class RunCancellationRecord(GovernanceRecord):
    id: UUID
    # Cancellation always targets a run, unlike generic governance records.
    run_id: UUID | None = Field()  # pyright: ignore[reportGeneralTypeIssues]
    step_id: SymbolicId
    reason: NonEmptyString
    actor: Actor
    source_state: StepState
    destination_state: StepState
    cancellation_behavior: CancellationBehavior
    side_effect_class: SideEffectClass
    terminal_execution_event_id: UUID | None = None
    terminal_execution_event_hash: Sha256Digest | None = None

    @field_validator("run_id")
    @classmethod
    def require_run_id(cls, value: UUID | None) -> UUID:
        if value is None:
            raise ValueError("run cancellation record requires a run ID")
        return value
