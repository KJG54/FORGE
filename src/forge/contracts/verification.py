"""Claim, check, evidence, and owner-acceptance contracts."""

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
    SymbolicId,
    UtcDateTime,
)


class CheckOutcome(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class CheckExecutionStatus(StrEnum):
    """Normalized process state for capability-backed check attempts."""

    COMPLETED = "completed"
    TIMED_OUT = "timed-out"
    OUTPUT_LIMIT_EXCEEDED = "output-limit-exceeded"
    START_ERROR = "start-error"
    SUPERVISION_ERROR = "supervision-error"


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
    capability_approval_id: UUID | None = None
    invocation_digest: Sha256Digest | None = None
    execution_status: CheckExecutionStatus | None = None
    stdout_capture_path: RepositoryRelativePath | None = None
    stderr_capture_path: RepositoryRelativePath | None = None
    stdout_digest: Sha256Digest | None = None
    stderr_digest: Sha256Digest | None = None
    stdout_byte_count: Annotated[int, Field(ge=0)] | None = None
    stderr_byte_count: Annotated[int, Field(ge=0)] | None = None
    invocation_metadata: dict[str, str]
    started_at: UtcDateTime
    ended_at: UtcDateTime
    exit_status: int | None = None
    outcome: CheckOutcome
    evidence_ids: tuple[UUID, ...] = ()
    limitations: tuple[NonEmptyString, ...] = ()
    result_digest: Sha256Digest
    actor: Actor

    @model_validator(mode="after")
    def validate_capability_execution(self) -> "CheckResult":
        execution_fields = (
            self.capability_approval_id,
            self.invocation_digest,
            self.execution_status,
            self.stdout_capture_path,
            self.stderr_capture_path,
            self.stdout_digest,
            self.stderr_digest,
            self.stdout_byte_count,
            self.stderr_byte_count,
        )
        if self.capability_id is None:
            if any(item is not None for item in execution_fields):
                raise ValueError(
                    "manual check results cannot contain capability execution fields"
                )
            return self
        if self.run_id is None or any(item is None for item in execution_fields):
            raise ValueError(
                "capability-backed check results require run, approval, invocation, "
                "execution, and capture bindings"
            )
        return self


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
