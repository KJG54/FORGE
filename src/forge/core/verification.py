"""Worker claims, manual check results, evidence packets, and verified transitions."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor, ActorType
from forge.contracts.agents import AgentResult
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.state import StepState
from forge.contracts.verification import CheckOutcome, CheckResult, Claim, EvidencePacket
from forge.contracts.workflows import StepDefinition
from forge.core.artifacts import current_revisions_for_roles, load_artifact_revision
from forge.core.authorization import forge_cli_actor
from forge.core.lifecycle import (
    ActiveInitiative,
    TransitionResult,
    apply_record_backed_transition,
    load_active_initiative,
)
from forge.core.transitions import CHECK_RECORDED, CLAIM_RECORDED, EVIDENCE_REGISTERED
from forge.errors import (
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    IntegrityError,
    SecurityError,
)
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class CompletionResult:
    claim: Claim
    claim_event: AuditEvent
    transition: TransitionResult


@dataclass(frozen=True)
class CheckRecordingResult:
    check: CheckResult
    event: AuditEvent


@dataclass(frozen=True)
class EvidenceRecordingResult:
    evidence: EvidencePacket
    event: AuditEvent


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _validate_limitations(limitations: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_require_text("Limitation", item) for item in limitations)


def _claim_path(layout: RepositoryLayout, claim_id: UUID) -> Path:
    return layout.claim_directory / f"{claim_id}.json"


def _check_path(layout: RepositoryLayout, check_id: UUID) -> Path:
    return layout.check_directory / f"{check_id}.json"


def _evidence_path(layout: RepositoryLayout, evidence_id: UUID) -> Path:
    return layout.evidence_directory / f"{evidence_id}.json"


def _ensure_record_directory(path: Path) -> bool:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Expected a governed directory at {path}")
        return False
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create governed directory {path}: {error}") from error
    return True


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def _append_record_event(
    active: ActiveInitiative,
    record_path: Path,
    record: Claim | CheckResult | EvidencePacket,
    event: AuditEvent,
) -> None:
    created_directory = _ensure_record_directory(record_path.parent)
    try:
        write_record(record_path, record)
        append_event_and_update_snapshot(
            active.layout.event_journal_file,
            active.layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(active.layout, event.id):
            record_path.unlink(missing_ok=True)
            if created_directory:
                with suppress(OSError):
                    record_path.parent.rmdir()
        raise


def _step(active: ActiveInitiative, step_id: str) -> StepDefinition:
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise ConflictError(f"Unknown workflow step {step_id!r}")
    return step


def _require_actor_for_step(active: ActiveInitiative, step_id: str, actor: Actor) -> None:
    step = _step(active, step_id)
    if actor.actor_type not in step.allowed_actors:
        raise AuthorizationError(
            f"Actor type {actor.actor_type.value} is not allowed for step {step_id}"
        )


def _active_run_for_step(active: ActiveInitiative, step_id: str, actor: Actor) -> UUID:
    matching: list[UUID] = []
    from forge.contracts.runs import RunRecord

    for run_id in active.state.active_run_ids:
        run = load_record(active.layout.governed_run_directory / f"{run_id}.json", RunRecord)
        if run.step_id == step_id and run.worker == actor:
            matching.append(run_id)
    if len(matching) != 1:
        raise ConflictError(
            f"Step {step_id} requires exactly one active run for the claiming actor"
        )
    return matching[0]


def _require_imported_agent_claim(
    active: ActiveInitiative,
    *,
    run_id: UUID,
    assertion: str,
) -> None:
    directory = active.layout.imported_result_directory
    matching = (
        result
        for path in directory.glob("*.json")
        if (result := load_record(path, AgentResult)).source_run_or_handoff_id == run_id
    )
    if not any(assertion in result.worker_claims for result in matching):
        raise ConflictError(
            "An agent-adapter claim must exactly match a worker claim in an imported result "
            f"from run {run_id}"
        )


def list_claims(layout: RepositoryLayout) -> tuple[Claim, ...]:
    load_active_initiative(layout, allow_paused=True)
    if not layout.claim_directory.exists():
        return ()
    return tuple(
        sorted(
            (load_record(path, Claim) for path in layout.claim_directory.glob("*.json")),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def list_checks(layout: RepositoryLayout) -> tuple[CheckResult, ...]:
    load_active_initiative(layout, allow_paused=True)
    if not layout.check_directory.exists():
        return ()
    return tuple(
        sorted(
            (load_record(path, CheckResult) for path in layout.check_directory.glob("*.json")),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def list_evidence(layout: RepositoryLayout) -> tuple[EvidencePacket, ...]:
    load_active_initiative(layout, allow_paused=True)
    if not layout.evidence_directory.exists():
        return ()
    return tuple(
        sorted(
            (
                load_record(path, EvidencePacket)
                for path in layout.evidence_directory.glob("*.json")
            ),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def show_evidence(layout: RepositoryLayout, evidence_id: UUID) -> EvidencePacket:
    load_active_initiative(layout, allow_paused=True)
    if not _evidence_path(layout, evidence_id).exists():
        raise ConflictError(f"Unknown evidence packet {evidence_id}")
    return load_record(_evidence_path(layout, evidence_id), EvidencePacket)


def dependency_references(layout: RepositoryLayout, revision_id: UUID) -> tuple[UUID, ...]:
    """Return governed claim, check, and evidence records directly bound to a revision."""
    dependent_ids = {
        claim.id
        for claim in list_claims(layout)
        if revision_id in claim.claimed_artifact_revision_ids
    }
    dependent_ids.update(
        check.id
        for check in list_checks(layout)
        if revision_id in check.target_artifact_revision_ids
    )
    dependent_ids.update(
        evidence.id
        for evidence in list_evidence(layout)
        if revision_id in evidence.artifact_revision_ids
    )
    return tuple(sorted(dependent_ids, key=str))


def complete_step(
    layout: RepositoryLayout,
    *,
    step_id: str,
    assertion: str,
    actor: Actor,
    limitations: tuple[str, ...] = (),
) -> CompletionResult:
    active = load_active_initiative(layout)
    step = _step(active, step_id)
    if active.state.step_states.get(step_id) is not StepState.IN_PROGRESS:
        state = active.state.step_states.get(step_id)
        label = state.value if state is not None else "unknown"
        raise ConflictError(f"Step {step_id} cannot be completed from state {label}")
    _require_actor_for_step(active, step_id, actor)
    assertion = _require_text("Claim assertion", assertion)
    limitations = _validate_limitations(limitations)
    run_id = _active_run_for_step(active, step_id, actor)
    if actor.actor_type is ActorType.AGENT_ADAPTER:
        _require_imported_agent_claim(active, run_id=run_id, assertion=assertion)
    revisions = current_revisions_for_roles(active, step.required_outputs)
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    claim_id = uuid4()
    basis = "participant asserted declared outputs against exact current artifact revisions"
    claim = Claim(
        id=claim_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        run_id=run_id,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=tuple(revision.id for revision in revisions),
        affected_digests=tuple(revision.content_digest for revision in revisions),
        step_id=step_id,
        assertion=assertion,
        claimed_artifact_revision_ids=tuple(revision.id for revision in revisions),
        limitations=limitations,
        actor=actor,
    )
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=CLAIM_RECORDED,
        actor=actor,
        run_id=run_id,
        authorization_basis=basis,
        affected_record_ids=(claim_id, *(revision.id for revision in revisions)),
        affected_digests=tuple(revision.content_digest for revision in revisions),
        metadata={
            "claim_id": str(claim_id),
            "step_id": step_id,
            "artifact_revision_ids": [str(revision.id) for revision in revisions],
        },
    )
    _append_record_event(active, _claim_path(layout, claim_id), claim, event)
    refreshed = load_active_initiative(layout)
    transition = next(
        (
            item
            for item in refreshed.workflow.transitions
            if item.source_state is StepState.IN_PROGRESS
            and item.destination_state is StepState.AWAITING_VERIFICATION
            and item.id in step.allowed_transitions
        ),
        None,
    )
    if transition is None:
        raise IntegrityError(f"Workflow step {step_id} has no submit transition")
    transitioned = apply_record_backed_transition(
        refreshed,
        step_id=step_id,
        transition_id=transition.id,
        actor=actor,
        run_id=run_id,
        affected_record_ids=(claim_id, *(revision.id for revision in revisions)),
        condition_record_ids={
            "claim-recorded": (claim_id, *(revision.id for revision in revisions))
        },
    )
    return CompletionResult(claim, event, transitioned)


def _check_digest_payload(
    *,
    check_id: str,
    check_version: str,
    target_ids: tuple[UUID, ...],
    invocation_metadata: dict[str, str],
    started_at: datetime,
    ended_at: datetime,
    exit_status: int | None,
    outcome: CheckOutcome,
    limitations: tuple[str, ...],
    actor: Actor,
) -> dict[str, object]:
    return {
        "actor": actor.model_dump(mode="json"),
        "check_id": check_id,
        "check_version": check_version,
        "ended_at": ended_at.isoformat(),
        "exit_status": exit_status,
        "invocation_metadata": invocation_metadata,
        "limitations": list(limitations),
        "outcome": outcome.value,
        "started_at": started_at.isoformat(),
        "target_artifact_revision_ids": [str(item) for item in target_ids],
    }


def record_check(
    layout: RepositoryLayout,
    *,
    step_id: str,
    check_id: str,
    check_version: str,
    invocation_metadata: dict[str, str],
    outcome: CheckOutcome,
    actor: Actor,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    exit_status: int | None = None,
    limitations: tuple[str, ...] = (),
) -> CheckRecordingResult:
    active = load_active_initiative(layout)
    step = _step(active, step_id)
    if active.state.step_states.get(step_id) is not StepState.AWAITING_VERIFICATION:
        raise ConflictError(f"Step {step_id} is not awaiting verification")
    _require_actor_for_step(active, step_id, actor)
    check_version = _require_text("Check version", check_version)
    if not invocation_metadata:
        raise ConfigurationError("Check invocation metadata must not be empty")
    invocation_metadata = {
        _require_text("Invocation metadata key", key): _require_text(
            "Invocation metadata value", value
        )
        for key, value in invocation_metadata.items()
    }
    limitations = _validate_limitations(limitations)
    if check_id not in step.check_requirements:
        raise ConflictError(
            f"Check {check_id!r} is not declared for step {step_id}; required checks are "
            f"{list(step.check_requirements)}"
        )
    revisions = current_revisions_for_roles(active, step.required_outputs)
    target_ids = tuple(revision.id for revision in revisions)
    start = started_at or utc_now()
    end = ended_at or utc_now()
    if start.tzinfo is None or end.tzinfo is None:
        raise ConfigurationError("Check timestamps must include a timezone")
    start = start.astimezone(UTC)
    end = end.astimezone(UTC)
    if end < start:
        raise ConflictError("Check end time cannot precede its start time")
    result_digest = canonical_json_digest(
        _check_digest_payload(
            check_id=check_id,
            check_version=check_version,
            target_ids=target_ids,
            invocation_metadata=invocation_metadata,
            started_at=start,
            ended_at=end,
            exit_status=exit_status,
            outcome=outcome,
            limitations=limitations,
            actor=actor,
        )
    )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    result_id = uuid4()
    basis = "participant recorded a manual structured check without executable capability trust"
    check = CheckResult(
        id=result_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=target_ids,
        affected_digests=tuple(revision.content_digest for revision in revisions),
        check_id=check_id,
        check_version=check_version,
        target_artifact_revision_ids=target_ids,
        invocation_metadata=invocation_metadata,
        started_at=start,
        ended_at=end,
        exit_status=exit_status,
        outcome=outcome,
        limitations=limitations,
        result_digest=result_digest,
        actor=actor,
    )
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=CHECK_RECORDED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(result_id, *target_ids),
        affected_digests=(result_digest, *(revision.content_digest for revision in revisions)),
        metadata={
            "check_id": check_id,
            "check_result_id": str(result_id),
            "outcome": outcome.value,
            "step_id": step_id,
            "target_artifact_revision_ids": [str(item) for item in target_ids],
        },
    )
    _append_record_event(active, _check_path(layout, result_id), check, event)
    return CheckRecordingResult(check, event)


def _evidence_digest_payload(
    *,
    purpose: str,
    artifact_revision_ids: tuple[UUID, ...],
    check_result_ids: tuple[UUID, ...],
    claim_ids: tuple[UUID, ...],
    limitations: tuple[str, ...],
    actor: Actor,
) -> dict[str, object]:
    return {
        "actor": actor.model_dump(mode="json"),
        "artifact_revision_ids": [str(item) for item in artifact_revision_ids],
        "check_result_ids": [str(item) for item in check_result_ids],
        "claim_ids": [str(item) for item in claim_ids],
        "limitations": list(limitations),
        "purpose": purpose,
    }


def record_evidence(
    layout: RepositoryLayout,
    *,
    step_id: str,
    purpose: str,
    actor: Actor,
    artifact_revision_ids: tuple[UUID, ...] = (),
    check_result_ids: tuple[UUID, ...] = (),
    claim_ids: tuple[UUID, ...] = (),
    limitations: tuple[str, ...] = (),
) -> EvidenceRecordingResult:
    active = load_active_initiative(layout)
    if active.state.step_states.get(step_id) is not StepState.AWAITING_VERIFICATION:
        raise ConflictError(f"Step {step_id} is not awaiting verification")
    _require_actor_for_step(active, step_id, actor)
    purpose = _require_text("Evidence purpose", purpose)
    limitations = _validate_limitations(limitations)
    if not (artifact_revision_ids or check_result_ids or claim_ids):
        raise ConflictError("Evidence must reference an artifact revision, check result, or claim")
    for revision_id in artifact_revision_ids:
        revision = load_artifact_revision(layout, revision_id)
        if revision.initiative_id != active.initiative.id:
            raise IntegrityError(f"Artifact revision belongs to another initiative: {revision_id}")
    for result_id in check_result_ids:
        result = load_record(_check_path(layout, result_id), CheckResult)
        if result.initiative_id != active.initiative.id:
            raise IntegrityError(f"Check result belongs to another initiative: {result_id}")
    for claim_id in claim_ids:
        claim = load_record(_claim_path(layout, claim_id), Claim)
        if claim.initiative_id != active.initiative.id:
            raise IntegrityError(f"Claim belongs to another initiative: {claim_id}")
    packet_digest = canonical_json_digest(
        _evidence_digest_payload(
            purpose=purpose,
            artifact_revision_ids=artifact_revision_ids,
            check_result_ids=check_result_ids,
            claim_ids=claim_ids,
            limitations=limitations,
            actor=actor,
        )
    )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    evidence_id = uuid4()
    references = (*artifact_revision_ids, *check_result_ids, *claim_ids)
    basis = "participant registered digest-bound evidence references and limitations"
    evidence = EvidencePacket(
        id=evidence_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=references,
        affected_digests=(packet_digest,),
        purpose=purpose,
        artifact_revision_ids=artifact_revision_ids,
        check_result_ids=check_result_ids,
        claim_ids=claim_ids,
        limitations=limitations,
        packet_digest=packet_digest,
        actor=actor,
    )
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=EVIDENCE_REGISTERED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(evidence_id, *references),
        affected_digests=(packet_digest,),
        metadata={
            "artifact_revision_ids": [str(item) for item in artifact_revision_ids],
            "check_result_ids": [str(item) for item in check_result_ids],
            "claim_ids": [str(item) for item in claim_ids],
            "evidence_id": str(evidence_id),
            "step_id": step_id,
        },
    )
    _append_record_event(active, _evidence_path(layout, evidence_id), evidence, event)
    return EvidenceRecordingResult(evidence, event)


def verify_step(layout: RepositoryLayout, *, step_id: str) -> TransitionResult:
    active = load_active_initiative(layout)
    step = _step(active, step_id)
    if active.state.step_states.get(step_id) is not StepState.AWAITING_VERIFICATION:
        raise ConflictError(f"Step {step_id} is not awaiting verification")
    revisions = current_revisions_for_roles(active, step.required_outputs)
    current_ids = {revision.id for revision in revisions}
    claims = tuple(
        claim
        for claim in list_claims(layout)
        if claim.step_id == step_id and set(claim.claimed_artifact_revision_ids) == current_ids
    )
    if not claims:
        raise ConflictError("No current worker claim covers the required artifact revisions")
    checks = list_checks(layout)
    passing: list[CheckResult] = []
    for required_check_id in step.check_requirements:
        candidates = [
            result
            for result in checks
            if result.check_id == required_check_id
            and result.outcome is CheckOutcome.PASSED
            and set(result.target_artifact_revision_ids) == current_ids
        ]
        if not candidates:
            raise ConflictError(
                f"Required check {required_check_id!r} has no passing result for current revisions"
            )
        passing.append(max(candidates, key=lambda item: (item.recorded_at, str(item.id))))
    passing_ids = {result.id for result in passing}
    evidence_packets = [
        packet
        for packet in list_evidence(layout)
        if current_ids.issubset(packet.artifact_revision_ids)
        and passing_ids.issubset(packet.check_result_ids)
        and any(claim.id in packet.claim_ids for claim in claims)
    ]
    if not evidence_packets:
        raise ConflictError(
            "No evidence packet binds the current artifact revisions, passing checks, and claim"
        )
    evidence = max(evidence_packets, key=lambda item: (item.recorded_at, str(item.id)))
    transition = next(
        (
            item
            for item in active.workflow.transitions
            if item.source_state is StepState.AWAITING_VERIFICATION
            and item.destination_state is StepState.AWAITING_ACCEPTANCE
            and item.id in step.allowed_transitions
        ),
        None,
    )
    if transition is None:
        raise IntegrityError(f"Workflow step {step_id} has no verification transition")
    check_support = tuple(result.id for result in passing) + tuple(current_ids)
    evidence_support = (evidence.id, *evidence.artifact_revision_ids, *evidence.check_result_ids)
    return apply_record_backed_transition(
        active,
        step_id=step_id,
        transition_id=transition.id,
        actor=forge_cli_actor(),
        affected_record_ids=(
            *(claim.id for claim in claims),
            *check_support,
            *evidence_support,
        ),
        condition_record_ids={
            "required-checks-passed": check_support,
            "required-evidence-registered": evidence_support,
        },
    )
