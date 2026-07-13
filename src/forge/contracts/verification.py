"""Claim, check, evidence, and owner-acceptance contracts."""

from enum import StrEnum
from uuid import UUID

from forge.contracts.actors import Actor
from forge.contracts.base import (
    GovernanceRecord,
    NonEmptyString,
    Sha256Digest,
    SymbolicId,
    UtcDateTime,
)


class CheckOutcome(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class Claim(GovernanceRecord):
    id: UUID
    step_id: SymbolicId
    assertion: NonEmptyString
    claimed_artifact_revision_ids: tuple[UUID, ...] = ()
    limitations: tuple[NonEmptyString, ...] = ()
    actor: Actor


class CheckResult(GovernanceRecord):
    id: UUID
    check_id: SymbolicId
    check_version: NonEmptyString
    target_artifact_revision_ids: tuple[UUID, ...]
    capability_id: SymbolicId | None = None
    invocation_metadata: dict[str, str]
    started_at: UtcDateTime
    ended_at: UtcDateTime
    exit_status: int | None = None
    outcome: CheckOutcome
    evidence_ids: tuple[UUID, ...] = ()
    limitations: tuple[NonEmptyString, ...] = ()
    result_digest: Sha256Digest
    actor: Actor


class EvidencePacket(GovernanceRecord):
    id: UUID
    purpose: NonEmptyString
    artifact_revision_ids: tuple[UUID, ...] = ()
    check_result_ids: tuple[UUID, ...] = ()
    claim_ids: tuple[UUID, ...] = ()
    limitations: tuple[NonEmptyString, ...] = ()
    packet_digest: Sha256Digest
    actor: Actor


class AcceptanceRecord(GovernanceRecord):
    id: UUID
    owner_actor: Actor
    accepted_artifact_revision_ids: tuple[UUID, ...]
    accepted_evidence_ids: tuple[UUID, ...]
    accepted_check_result_ids: tuple[UUID, ...]
    accepted_scope: NonEmptyString
    known_limitations: tuple[NonEmptyString, ...] = ()
    residual_risks: tuple[NonEmptyString, ...] = ()
    acceptance_event_id: UUID
    revocation_id: UUID | None = None
