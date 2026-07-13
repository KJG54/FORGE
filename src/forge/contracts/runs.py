"""Bounded work-attempt records."""

from uuid import UUID

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
from forge.contracts.state import RunState


class RunRecord(GovernanceRecord):
    id: UUID
    step_id: SymbolicId
    worker: Actor
    adapter_reference: NonEmptyString | None = None
    capability_ids: tuple[SymbolicId, ...] = ()
    side_effect_class: SideEffectClass
    status: RunState
    started_at: UtcDateTime | None = None
    ended_at: UtcDateTime | None = None
    input_context_digest: Sha256Digest
    output_manifest_path: RepositoryRelativePath | None = None
    exit_metadata: dict[str, str]
    cancellation_details: NonEmptyString | None = None
