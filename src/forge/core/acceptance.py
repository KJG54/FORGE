"""Owner acceptance, revocation, and append-only acceptance history."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.decisions import ApprovalRevocation
from forge.contracts.events import AuditEvent
from forge.contracts.state import InitiativeLifecycleState, StepState
from forge.contracts.verification import (
    AcceptanceRecord,
    CheckOutcome,
    CheckResult,
)
from forge.core.artifacts import current_revisions_for_roles
from forge.core.authorization import require_owner
from forge.core.invalidation import calculate_acceptance_revocation_invalidation
from forge.core.lifecycle import (
    ActiveInitiative,
    TransitionResult,
    apply_record_backed_transition,
    load_active_initiative,
)
from forge.core.transitions import ACCEPTANCE_RECORDED, ACCEPTANCE_REVOKED
from forge.core.verification import list_checks, list_claims, list_evidence
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class AcceptanceRecordingResult:
    acceptance: AcceptanceRecord
    event: AuditEvent
    transition: TransitionResult


@dataclass(frozen=True)
class AcceptanceRevocationResult:
    revocation: ApprovalRevocation
    event: AuditEvent


@dataclass(frozen=True)
class AcceptanceView:
    acceptance: AcceptanceRecord
    step_id: str
    revocation: ApprovalRevocation | None
    stale: bool


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _acceptance_path(layout: RepositoryLayout, record_id: UUID) -> Path:
    return layout.acceptance_directory / f"{record_id}.json"


def _revocation_path(layout: RepositoryLayout, record_id: UUID) -> Path:
    return layout.revocation_directory / f"{record_id}.json"


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
    path: Path,
    record: AcceptanceRecord | ApprovalRevocation,
    event: AuditEvent,
) -> None:
    created = _ensure_record_directory(path.parent)
    try:
        write_record(path, record)
        append_event_and_update_snapshot(
            active.layout.event_journal_file,
            active.layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(active.layout, event.id):
            path.unlink(missing_ok=True)
            if created:
                with suppress(OSError):
                    path.parent.rmdir()
        raise


def _require_open_lifecycle(active: ActiveInitiative) -> None:
    if active.state.lifecycle_state not in {
        InitiativeLifecycleState.ACTIVE,
        InitiativeLifecycleState.CLOSING,
    }:
        raise ConflictError("Acceptance changes require an active or closing initiative")


def _step_event_map(layout: RepositoryLayout) -> dict[UUID, str]:
    result: dict[UUID, str] = {}
    for event in read_journal(layout.event_journal_file):
        if event.event_type != ACCEPTANCE_RECORDED:
            continue
        value = event.metadata.get("acceptance_id")
        step_id = event.metadata.get("step_id")
        if not isinstance(value, str) or not isinstance(step_id, str):
            raise IntegrityError(f"Acceptance event {event.id} has invalid metadata")
        try:
            result[UUID(value)] = step_id
        except ValueError as error:
            raise IntegrityError(f"Acceptance event {event.id} has invalid metadata") from error
    return result


def list_acceptances(layout: RepositoryLayout) -> tuple[AcceptanceView, ...]:
    active = load_active_initiative(layout)
    steps = _step_event_map(layout)
    revocations = {
        item.approval_id: item
        for item in (
            load_record(path, ApprovalRevocation)
            for path in layout.revocation_directory.glob("*.json")
        )
    } if layout.revocation_directory.exists() else {}
    views = [
        AcceptanceView(
            load_record(_acceptance_path(layout, acceptance_id), AcceptanceRecord),
            step_id,
            revocations.get(acceptance_id),
            acceptance_id in active.state.stale_record_ids,
        )
        for acceptance_id, step_id in steps.items()
    ]
    return tuple(sorted(views, key=lambda item: item.acceptance.event_sequence))


def show_acceptance(layout: RepositoryLayout, acceptance_id: UUID) -> AcceptanceView:
    view = next(
        (item for item in list_acceptances(layout) if item.acceptance.id == acceptance_id),
        None,
    )
    if view is None:
        raise ConflictError(f"Unknown acceptance {acceptance_id}")
    return view


def record_acceptance(
    layout: RepositoryLayout,
    *,
    step_id: str,
    accepted_scope: str,
    actor: Actor,
    known_limitations: tuple[str, ...] = (),
    residual_risks: tuple[str, ...] = (),
) -> AcceptanceRecordingResult:
    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "record owner acceptance")
    _require_open_lifecycle(active)
    if active.state.step_states.get(step_id) is not StepState.AWAITING_ACCEPTANCE:
        raise ConflictError(f"Step {step_id} is not awaiting acceptance")
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise ConflictError(f"Unknown workflow step {step_id!r}")
    accepted_scope = _require_text("Accepted scope", accepted_scope)
    known_limitations = tuple(_require_text("Known limitation", item) for item in known_limitations)
    residual_risks = tuple(_require_text("Residual risk", item) for item in residual_risks)
    stale = set(active.state.stale_record_ids)
    revisions = current_revisions_for_roles(active, step.required_outputs)
    revision_ids = {item.id for item in revisions}
    claims = [
        item for item in list_claims(layout)
        if item.id not in stale
        and item.step_id == step_id
        and set(item.claimed_artifact_revision_ids) == revision_ids
    ]
    if not claims:
        raise ConflictError("No current non-stale claim supports owner acceptance")
    checks: list[CheckResult] = []
    available_checks = list_checks(layout)
    for requirement in step.check_requirements:
        matches = [
            item for item in available_checks
            if item.id not in stale
            and item.check_id == requirement
            and item.outcome is CheckOutcome.PASSED
            and set(item.target_artifact_revision_ids) == revision_ids
        ]
        if not matches:
            raise ConflictError(
                f"Required check {requirement!r} has no current non-stale passing result"
            )
        checks.append(max(matches, key=lambda item: (item.recorded_at, str(item.id))))
    check_ids = {item.id for item in checks}
    evidence = [
        item for item in list_evidence(layout)
        if item.id not in stale
        and revision_ids.issubset(item.artifact_revision_ids)
        and check_ids.issubset(item.check_result_ids)
        and any(claim.id in item.claim_ids for claim in claims)
    ]
    if not evidence:
        raise ConflictError("No current non-stale evidence packet supports owner acceptance")
    packet = max(evidence, key=lambda item: (item.recorded_at, str(item.id)))
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    acceptance_id = uuid4()
    event_id = uuid4()
    artifact_ids = tuple(sorted(revision_ids, key=str))
    accepted_check_ids = tuple(item.id for item in checks)
    evidence_ids = (packet.id,)
    dependencies = (*artifact_ids, *accepted_check_ids, *evidence_ids)
    digests = (
        *(item.content_digest for item in revisions),
        *(item.result_digest for item in checks),
        packet.packet_digest,
    )
    basis = "configured owner accepted exact current revisions, checks, evidence, and scope"
    acceptance = AcceptanceRecord(
        id=acceptance_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=dependencies,
        affected_digests=digests,
        owner_actor=actor,
        accepted_artifact_revision_ids=artifact_ids,
        accepted_evidence_ids=evidence_ids,
        accepted_check_result_ids=accepted_check_ids,
        accepted_scope=accepted_scope,
        known_limitations=known_limitations,
        residual_risks=residual_risks,
        acceptance_event_id=event_id,
    )
    acceptance_digest = canonical_json_digest(acceptance.model_dump(mode="json"))
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=ACCEPTANCE_RECORDED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(acceptance_id, *dependencies),
        affected_digests=(*digests, acceptance_digest),
        metadata={
            "acceptance_id": str(acceptance_id),
            "step_id": step_id,
            "artifact_revision_ids": [str(item) for item in artifact_ids],
            "check_result_ids": [str(item) for item in accepted_check_ids],
            "evidence_ids": [str(item) for item in evidence_ids],
        },
    )
    _append_record_event(active, _acceptance_path(layout, acceptance_id), acceptance, event)
    refreshed = load_active_initiative(layout)
    transition = next(
        (
            item for item in refreshed.workflow.transitions
            if item.source_state is StepState.AWAITING_ACCEPTANCE
            and item.destination_state is StepState.COMPLETED
            and item.id in step.allowed_transitions
        ),
        None,
    )
    if transition is None:
        raise IntegrityError(f"Workflow step {step_id} has no acceptance transition")
    transitioned = apply_record_backed_transition(
        refreshed,
        step_id=step_id,
        transition_id=transition.id,
        actor=actor,
        affected_record_ids=(acceptance_id, *dependencies),
        condition_record_ids={"owner-acceptance-recorded": (acceptance_id,)},
    )
    return AcceptanceRecordingResult(acceptance, event, transitioned)


def revoke_acceptance(
    layout: RepositoryLayout,
    *,
    acceptance_id: UUID,
    reason: str,
    actor: Actor,
) -> AcceptanceRevocationResult:
    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "revoke owner acceptance")
    _require_open_lifecycle(active)
    view = show_acceptance(layout, acceptance_id)
    if view.revocation is not None:
        raise ConflictError(f"Acceptance {acceptance_id} is already revoked")
    reason = _require_text("Revocation reason", reason)
    invalidation = calculate_acceptance_revocation_invalidation(
        active, acceptance_id, view.step_id
    )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    revocation_id = uuid4()
    basis = "configured owner revoked prior acceptance and invalidated dependent progression"
    revocation = ApprovalRevocation(
        id=revocation_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=(acceptance_id, *invalidation.stale_record_ids),
        affected_digests=view.acceptance.affected_digests,
        approval_id=acceptance_id,
        reason=reason,
        actor=actor,
    )
    revocation_digest = canonical_json_digest(revocation.model_dump(mode="json"))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=ACCEPTANCE_REVOKED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=tuple(
            dict.fromkeys((revocation_id, acceptance_id, *invalidation.stale_record_ids))
        ),
        affected_digests=(*view.acceptance.affected_digests, revocation_digest),
        metadata={
            "acceptance_id": str(acceptance_id),
            "revocation_id": str(revocation_id),
            "step_id": view.step_id,
            **invalidation.event_metadata(),
        },
    )
    _append_record_event(active, _revocation_path(layout, revocation_id), revocation, event)
    return AcceptanceRevocationResult(revocation, event)
