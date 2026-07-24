"""Owner-governed scope amendments with derived workflow invalidation."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.decisions import ScopeAmendment
from forge.contracts.events import AuditEvent
from forge.core.acceptance import list_acceptances
from forge.core.artifacts import list_artifacts
from forge.core.authorization import require_owner
from forge.core.invalidation import calculate_scope_amendment_invalidation
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.transitions import SCOPE_AMENDED
from forge.core.verification import list_checks
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class ScopeAmendmentResult:
    amendment: ScopeAmendment
    event: AuditEvent


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _record_path(layout: RepositoryLayout, amendment_id: UUID) -> Path:
    return layout.scope_amendment_directory / f"{amendment_id}.json"


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
        raise IntegrityError(f"Cannot create scope amendment directory {path}: {error}") from error
    return True


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def _descendant_step_ids(active: ActiveInitiative, root_step_id: str) -> tuple[str, ...]:
    affected = {root_step_id}
    changed = True
    while changed:
        changed = False
        for step in active.workflow.steps:
            if step.id not in affected and set(step.prerequisites) & affected:
                affected.add(step.id)
                changed = True
    return tuple(step.id for step in active.workflow.steps if step.id in affected)


def _known_requirement_ids(active: ActiveInitiative) -> set[str]:
    identifiers: set[str] = set(active.workflow.required_artifact_classes)
    identifiers.update(active.workflow.required_evidence_classes)
    for step in active.workflow.steps:
        identifiers.update(step.required_inputs)
        identifiers.update(step.required_outputs)
        identifiers.update(step.claim_requirements)
        identifiers.update(step.check_requirements)
        identifiers.update(step.acceptance_requirements)
    for gate in active.workflow.required_gates:
        identifiers.add(gate.id)
        identifiers.add(gate.authority_requirement)
        identifiers.update(gate.required_artifact_classes)
        identifiers.update(gate.required_evidence_classes)
        identifiers.update(gate.required_check_ids)
    for transition in active.workflow.transitions:
        identifiers.add(transition.authority_requirement)
        identifiers.update(transition.conditions)
    return identifiers


def _invalidated_gate_ids(
    active: ActiveInitiative,
    affected_step_ids: tuple[str, ...],
    affected_requirements: tuple[str, ...],
) -> tuple[str, ...]:
    steps = [step for step in active.workflow.steps if step.id in affected_step_ids]
    check_ids = {item for step in steps for item in step.check_requirements}
    artifact_classes = {
        item
        for step in steps
        for item in (*step.required_inputs, *step.required_outputs)
    }
    evidence_classes = set(active.workflow.required_evidence_classes)
    requirements = set(affected_requirements)
    return tuple(
        gate.id
        for gate in active.workflow.required_gates
        if (
            gate.id in requirements
            or gate.authority_requirement in requirements
            or set(gate.required_check_ids) & check_ids
            or set(gate.required_artifact_classes) & artifact_classes
            or set(gate.required_evidence_classes) & evidence_classes
        )
    )


def list_scope_amendments(layout: RepositoryLayout) -> tuple[ScopeAmendment, ...]:
    load_active_initiative(layout, allow_paused=True, allow_untrusted_pack=True)
    directory = layout.scope_amendment_directory
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise IntegrityError(f"Scope amendment directory is missing or unsafe: {directory}")
    return tuple(
        sorted(
            (
                load_record(path, ScopeAmendment)
                for path in directory.glob("*.json")
            ),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def show_scope_amendment(
    layout: RepositoryLayout,
    amendment_id: UUID,
) -> ScopeAmendment:
    matches = [
        item for item in list_scope_amendments(layout) if item.id == amendment_id
    ]
    if not matches:
        raise ConflictError(f"Unknown scope amendment {amendment_id}")
    return matches[0]


def effective_scope_summary(
    active: ActiveInitiative,
) -> str:
    """Return the latest complete owner-amended scope, or the initiative's original scope."""

    directory = active.layout.scope_amendment_directory
    amendments = (
        tuple(
            sorted(
                (
                    load_record(path, ScopeAmendment)
                    for path in directory.glob("*.json")
                ),
                key=lambda item: (item.event_sequence, str(item.id)),
            )
        )
        if directory.exists()
        else ()
    )
    if amendments:
        return amendments[-1].changed_scope
    return active.initiative.declared_scope_summary


def amend_scope(
    layout: RepositoryLayout,
    *,
    changed_scope: str,
    rationale: str,
    affected_requirements: tuple[str, ...],
    affected_artifact_ids: tuple[UUID, ...],
    workflow_return_step_id: str,
    actor: Actor,
) -> ScopeAmendmentResult:
    """Record one complete effective scope and invalidate derived downstream support."""

    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "amend initiative scope")
    changed_scope = _require_text("Changed scope", changed_scope)
    rationale = _require_text("Scope amendment rationale", rationale)
    if not affected_requirements:
        raise ConfigurationError("At least one affected requirement is required")
    if len(affected_requirements) != len(set(affected_requirements)):
        raise ConfigurationError("Affected requirements must not contain duplicates")
    known_requirements = _known_requirement_ids(active)
    unknown_requirements = set(affected_requirements) - known_requirements
    if unknown_requirements:
        raise ConfigurationError(
            f"Unknown affected workflow requirements: {sorted(unknown_requirements)}"
        )
    if len(affected_artifact_ids) != len(set(affected_artifact_ids)):
        raise ConfigurationError("Affected artifact IDs must not contain duplicates")
    artifacts = {item.artifact.id: item for item in list_artifacts(layout)}
    unknown_artifacts = set(affected_artifact_ids) - set(artifacts)
    if unknown_artifacts:
        raise ConflictError(f"Unknown affected artifacts: {sorted(map(str, unknown_artifacts))}")
    if workflow_return_step_id not in {step.id for step in active.workflow.steps}:
        raise ConflictError(f"Unknown workflow return step {workflow_return_step_id!r}")

    invalidation = calculate_scope_amendment_invalidation(
        active,
        workflow_return_step_id=workflow_return_step_id,
        affected_artifact_ids=affected_artifact_ids,
    )
    if invalidation.invalidated_run_ids:
        values = ", ".join(str(item) for item in invalidation.invalidated_run_ids)
        raise ConflictError(
            f"Scope amendment affects active runs; cancel them first: {values}"
        )
    stale_ids = set(invalidation.stale_record_ids)
    invalidated_check_ids = tuple(
        sorted((item.id for item in list_checks(layout) if item.id in stale_ids), key=str)
    )
    invalidated_acceptance_ids = tuple(
        sorted(
            (
                item.acceptance.id
                for item in list_acceptances(layout)
                if item.acceptance.id in stale_ids
            ),
            key=str,
        )
    )
    affected_step_ids = _descendant_step_ids(active, workflow_return_step_id)
    invalidated_gate_ids = _invalidated_gate_ids(
        active,
        affected_step_ids,
        affected_requirements,
    )
    artifact_digests = tuple(
        artifacts[item].current_revision.content_digest for item in affected_artifact_ids
    )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    amendment_id = uuid4()
    basis = (
        "configured owner replaced the effective initiative scope and invalidated "
        "derived downstream support"
    )
    governed_dependencies = tuple(
        dict.fromkeys((*affected_artifact_ids, *invalidation.stale_record_ids))
    )
    amendment = ScopeAmendment(
        id=amendment_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=governed_dependencies,
        affected_digests=artifact_digests,
        changed_scope=changed_scope,
        rationale=rationale,
        affected_requirements=affected_requirements,
        affected_artifact_ids=affected_artifact_ids,
        invalidated_check_ids=invalidated_check_ids,
        invalidated_gate_ids=invalidated_gate_ids,
        invalidated_acceptance_ids=invalidated_acceptance_ids,
        workflow_return_step_id=workflow_return_step_id,
        actor=actor,
    )
    record_digest = canonical_json_digest(amendment.model_dump(mode="json"))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=SCOPE_AMENDED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(amendment_id, *governed_dependencies),
        affected_digests=(*artifact_digests, record_digest),
        metadata={
            "scope_amendment_id": str(amendment_id),
            "workflow_return_step_id": workflow_return_step_id,
            "affected_requirement_ids": list(affected_requirements),
            "affected_artifact_ids": [str(item) for item in affected_artifact_ids],
            "invalidated_check_ids": [str(item) for item in invalidated_check_ids],
            "invalidated_gate_ids": list(invalidated_gate_ids),
            "invalidated_acceptance_ids": [
                str(item) for item in invalidated_acceptance_ids
            ],
            **invalidation.event_metadata(),
        },
    )
    path = _record_path(layout, amendment_id)
    created = _ensure_directory(path.parent)
    try:
        write_record(path, amendment)
        append_event_and_update_snapshot(
            active.layout.event_journal_file,
            active.layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event.id):
            path.unlink(missing_ok=True)
            if created:
                with suppress(OSError):
                    path.parent.rmdir()
        raise
    return ScopeAmendmentResult(amendment, event)
