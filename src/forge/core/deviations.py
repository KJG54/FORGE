"""Append-only workflow deviations with explicit owner review."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.decisions import (
    WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE,
    DecisionRecord,
    WorkflowDeviation,
)
from forge.contracts.events import AuditEvent
from forge.core.authorization import require_owner
from forge.core.lifecycle import load_active_initiative
from forge.core.transitions import WORKFLOW_DEVIATION_RECORDED
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class WorkflowDeviationResult:
    deviation: WorkflowDeviation
    event: AuditEvent


@dataclass(frozen=True)
class WorkflowDeviationView:
    deviation: WorkflowDeviation
    review_decision: DecisionRecord | None

    @property
    def review_open(self) -> bool:
        return self.review_decision is None


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _deviation_path(layout: RepositoryLayout, deviation_id: UUID) -> Path:
    return layout.workflow_deviation_directory / f"{deviation_id}.json"


def _ensure_directory(path: Path) -> bool:
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


def _review_decisions(layout: RepositoryLayout) -> dict[UUID, DecisionRecord]:
    active = load_active_initiative(
        layout,
        allow_terminal=True,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    open_ids = set(active.state.open_decision_ids)
    reviews: dict[UUID, DecisionRecord] = {}
    decisions = (
        (
            load_record(path, DecisionRecord)
            for path in layout.decision_directory.glob("*.json")
        )
        if layout.decision_directory.exists()
        else ()
    )
    for decision in decisions:
        if (
            decision.id not in open_ids
            or decision.id in active.state.stale_record_ids
            or decision.decision_type != WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE
            or len(decision.affected_record_ids) != 1
        ):
            continue
        reviews[decision.affected_record_ids[0]] = decision
    return reviews


def list_workflow_deviations(
    layout: RepositoryLayout,
) -> tuple[WorkflowDeviationView, ...]:
    load_active_initiative(
        layout,
        allow_terminal=True,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    if not layout.workflow_deviation_directory.exists():
        return ()
    reviews = _review_decisions(layout)
    deviations = sorted(
        (
            load_record(path, WorkflowDeviation)
            for path in layout.workflow_deviation_directory.glob("*.json")
        ),
        key=lambda item: (item.event_sequence, str(item.id)),
    )
    return tuple(
        WorkflowDeviationView(deviation, reviews.get(deviation.id))
        for deviation in deviations
    )


def show_workflow_deviation(
    layout: RepositoryLayout,
    deviation_id: UUID,
) -> WorkflowDeviationView:
    match = next(
        (
            item
            for item in list_workflow_deviations(layout)
            if item.deviation.id == deviation_id
        ),
        None,
    )
    if match is None:
        raise ConflictError(f"Unknown workflow deviation {deviation_id}")
    return match


def open_workflow_deviations(
    layout: RepositoryLayout,
) -> tuple[WorkflowDeviationView, ...]:
    return tuple(item for item in list_workflow_deviations(layout) if item.review_open)


def record_workflow_deviation(
    layout: RepositoryLayout,
    *,
    declared_behavior: str,
    actual_behavior: str,
    rationale: str,
    review_requirement: str,
    actor: Actor,
) -> WorkflowDeviationResult:
    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "record a workflow deviation")
    declared_behavior = _require_text("Declared behavior", declared_behavior)
    actual_behavior = _require_text("Actual behavior", actual_behavior)
    rationale = _require_text("Deviation rationale", rationale)
    review_requirement = _require_text("Review requirement", review_requirement)
    if declared_behavior == actual_behavior:
        raise ConflictError("Declared and actual behavior do not describe a deviation")

    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    deviation_id = uuid4()
    workflow_digest = canonical_json_digest(active.workflow.model_dump(mode="json"))
    basis = (
        "configured owner recorded an observed workflow deviation without granting a waiver"
    )
    deviation = WorkflowDeviation(
        id=deviation_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_digests=(workflow_digest,),
        workflow_id=active.workflow.id,
        declared_behavior=declared_behavior,
        actual_behavior=actual_behavior,
        rationale=rationale,
        review_requirement=review_requirement,
        actor=actor,
    )
    record_digest = canonical_json_digest(deviation.model_dump(mode="json"))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=WORKFLOW_DEVIATION_RECORDED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(deviation_id,),
        affected_digests=(workflow_digest, record_digest),
        metadata={
            "workflow_deviation_id": str(deviation_id),
            "workflow_id": active.workflow.id,
            "workflow_version": active.workflow.version,
            "workflow_digest": workflow_digest,
        },
    )
    path = _deviation_path(layout, deviation_id)
    created_directory = _ensure_directory(path.parent)
    try:
        write_record(path, deviation)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event.id):
            path.unlink(missing_ok=True)
            if created_directory:
                with suppress(OSError):
                    path.parent.rmdir()
        raise
    return WorkflowDeviationResult(deviation, event)
