"""Deterministic dependency staleness and workflow invalidation planning."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from forge.contracts.artifacts import ArtifactRevision
from forge.contracts.decisions import DecisionRecord
from forge.contracts.runs import RunRecord
from forge.contracts.state import StepState
from forge.contracts.verification import AcceptanceRecord, CheckResult, Claim, EvidencePacket
from forge.core.lifecycle import ActiveInitiative
from forge.core.transitions import (
    ACCEPTANCE_RECORDED,
    CHECK_RECORDED,
    CLAIM_RECORDED,
    DECISION_RECORDED,
    DECISION_SUPERSEDED,
    EVIDENCE_REGISTERED,
)
from forge.errors import IntegrityError
from forge.storage.journal import read_journal
from forge.storage.records import load_record


@dataclass(frozen=True)
class DependencyInvalidation:
    """Exact append-only records and workflow state affected by a governance change."""

    stale_record_ids: tuple[UUID, ...]
    invalidated_step_ids: tuple[str, ...]
    reset_step_ids: tuple[str, ...]
    invalidated_run_ids: tuple[UUID, ...]

    def event_metadata(self) -> dict[str, object]:
        return {
            "stale_record_ids": [str(item) for item in self.stale_record_ids],
            "invalidated_step_ids": list(self.invalidated_step_ids),
            "reset_step_ids": list(self.reset_step_ids),
            "invalidated_run_ids": [str(item) for item in self.invalidated_run_ids],
        }


@dataclass
class _DependencyInventory:
    claims: dict[UUID, Claim]
    checks: dict[UUID, CheckResult]
    evidence: dict[UUID, EvidencePacket]
    acceptances: dict[UUID, AcceptanceRecord]
    decisions: dict[UUID, DecisionRecord]
    record_steps: dict[UUID, str]


def _uuid_metadata(value: object, *, event_id: UUID, key: str) -> UUID:
    if not isinstance(value, str):
        raise IntegrityError(f"Event {event_id} lacks {key} metadata")
    try:
        return UUID(value)
    except ValueError as error:
        raise IntegrityError(f"Event {event_id} has invalid {key} metadata") from error


def _inventory(active: ActiveInitiative) -> _DependencyInventory:
    claims: dict[UUID, Claim] = {}
    checks: dict[UUID, CheckResult] = {}
    evidence: dict[UUID, EvidencePacket] = {}
    acceptances: dict[UUID, AcceptanceRecord] = {}
    decisions: dict[UUID, DecisionRecord] = {}
    record_steps: dict[UUID, str] = {}
    for event in read_journal(active.layout.event_journal_file):
        record_id: UUID | None = None
        if event.event_type == CLAIM_RECORDED:
            record_id = _uuid_metadata(
                event.metadata.get("claim_id"), event_id=event.id, key="claim_id"
            )
            claims[record_id] = load_record(
                active.layout.claim_directory / f"{record_id}.json", Claim
            )
        elif event.event_type == CHECK_RECORDED:
            record_id = _uuid_metadata(
                event.metadata.get("check_result_id"),
                event_id=event.id,
                key="check_result_id",
            )
            checks[record_id] = load_record(
                active.layout.check_directory / f"{record_id}.json", CheckResult
            )
        elif event.event_type == EVIDENCE_REGISTERED:
            record_id = _uuid_metadata(
                event.metadata.get("evidence_id"),
                event_id=event.id,
                key="evidence_id",
            )
            evidence[record_id] = load_record(
                active.layout.evidence_directory / f"{record_id}.json", EvidencePacket
            )
        elif event.event_type == ACCEPTANCE_RECORDED:
            record_id = _uuid_metadata(
                event.metadata.get("acceptance_id"),
                event_id=event.id,
                key="acceptance_id",
            )
            acceptances[record_id] = load_record(
                active.layout.acceptance_directory / f"{record_id}.json",
                AcceptanceRecord,
            )
        if record_id is not None:
            step_id = event.metadata.get("step_id")
            if not isinstance(step_id, str):
                raise IntegrityError(f"Event {event.id} lacks step_id metadata")
            record_steps[record_id] = step_id
        if event.event_type in {DECISION_RECORDED, DECISION_SUPERSEDED}:
            decision_id = _uuid_metadata(
                event.metadata.get("decision_id"), event_id=event.id, key="decision_id"
            )
            decisions[decision_id] = load_record(
                active.layout.decision_directory / f"{decision_id}.json", DecisionRecord
            )
    return _DependencyInventory(
        claims, checks, evidence, acceptances, decisions, record_steps
    )


def _descendants(active: ActiveInitiative, roots: set[str]) -> set[str]:
    affected = set(roots)
    changed = True
    while changed:
        changed = False
        for step in active.workflow.steps:
            if step.id not in affected and set(step.prerequisites) & affected:
                affected.add(step.id)
                changed = True
    return affected


def _plan(
    active: ActiveInitiative,
    inventory: _DependencyInventory,
    stale_ids: set[UUID],
    root_steps: set[str],
) -> DependencyInvalidation:
    affected_steps = _descendants(active, root_steps)
    stale_ids.update(
        record_id
        for record_id, step_id in inventory.record_steps.items()
        if step_id in affected_steps
    )
    invalidated: set[str] = set()
    reset: set[str] = set()
    for step_id in affected_steps:
        state = active.state.step_states[step_id]
        if state in {StepState.PENDING, StepState.READY}:
            reset.add(step_id)
        else:
            invalidated.add(step_id)
    invalidated_runs: list[UUID] = []
    for run_id in active.state.active_run_ids:
        run = load_record(
            active.layout.governed_run_directory / f"{run_id}.json", RunRecord
        )
        if run.step_id in affected_steps:
            invalidated_runs.append(run_id)
    return DependencyInvalidation(
        tuple(sorted(stale_ids, key=str)),
        tuple(step.id for step in active.workflow.steps if step.id in invalidated),
        tuple(step.id for step in active.workflow.steps if step.id in reset),
        tuple(sorted(invalidated_runs, key=str)),
    )


def calculate_artifact_revision_invalidation(
    active: ActiveInitiative,
    prior_revision: ArtifactRevision,
) -> DependencyInvalidation:
    """Propagate a superseded artifact revision through governed dependencies."""

    inventory = _inventory(active)
    stale: set[UUID] = {prior_revision.id}
    stale.update(
        item.id
        for item in inventory.claims.values()
        if prior_revision.id in item.claimed_artifact_revision_ids
    )
    stale.update(
        item.id
        for item in inventory.checks.values()
        if prior_revision.id in item.target_artifact_revision_ids
    )
    for item in inventory.evidence.values():
        if (
            prior_revision.id in item.artifact_revision_ids
            or set(item.check_result_ids) & stale
            or set(item.claim_ids) & stale
        ):
            stale.add(item.id)
    for item in inventory.acceptances.values():
        if (
            prior_revision.id in item.accepted_artifact_revision_ids
            or set(item.accepted_check_result_ids) & stale
            or set(item.accepted_evidence_ids) & stale
        ):
            stale.add(item.id)
    stale.update(
        item.id
        for item in inventory.decisions.values()
        if prior_revision.content_digest in item.bound_digests
    )
    roots = {
        step_id
        for record_id, step_id in inventory.record_steps.items()
        if record_id in stale
    }
    return _plan(active, inventory, stale, roots)


def calculate_acceptance_revocation_invalidation(
    active: ActiveInitiative,
    acceptance_id: UUID,
    step_id: str,
) -> DependencyInvalidation:
    """Invalidate an accepted step and all workflow descendants after revocation."""

    inventory = _inventory(active)
    if acceptance_id not in inventory.acceptances:
        raise IntegrityError(f"Acceptance {acceptance_id} is not journal-backed")
    return _plan(active, inventory, {acceptance_id}, {step_id})


def calculate_scope_amendment_invalidation(
    active: ActiveInitiative,
    *,
    workflow_return_step_id: str,
    affected_artifact_ids: tuple[UUID, ...],
) -> DependencyInvalidation:
    """Invalidate current support at and below an owner-selected workflow return point."""

    if workflow_return_step_id not in {step.id for step in active.workflow.steps}:
        raise IntegrityError(
            f"Scope amendment return step {workflow_return_step_id!r} is unknown"
        )
    inventory = _inventory(active)
    affected_steps = _descendants(active, {workflow_return_step_id})
    stale = {
        record_id
        for record_id, step_id in inventory.record_steps.items()
        if step_id in affected_steps
    }
    decision_dependencies = {*stale, *affected_artifact_ids}
    stale.update(
        decision.id
        for decision in inventory.decisions.values()
        if set(decision.affected_record_ids) & decision_dependencies
    )
    planned = _plan(active, inventory, stale, {workflow_return_step_id})
    invalidated = set(planned.invalidated_step_ids)
    reset = set(planned.reset_step_ids)
    if active.state.step_states[workflow_return_step_id] is not StepState.PENDING:
        invalidated.add(workflow_return_step_id)
        reset.discard(workflow_return_step_id)
    return DependencyInvalidation(
        planned.stale_record_ids,
        tuple(step.id for step in active.workflow.steps if step.id in invalidated),
        tuple(step.id for step in active.workflow.steps if step.id in reset),
        planned.invalidated_run_ids,
    )
