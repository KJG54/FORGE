"""Owner-authorized initiative creation and manual workflow operations."""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.capabilities import SideEffectClass
from forge.contracts.events import AuditEvent
from forge.contracts.initiatives import Initiative
from forge.contracts.packs import PackManifest, PackTrustDecision, PackTrustState
from forge.contracts.runs import RunRecord
from forge.contracts.state import (
    ExplanationProfile,
    InitiativeLifecycleState,
    MaterializedState,
    RunState,
    StepState,
)
from forge.contracts.workflows import WorkflowDefinition
from forge.core.authorization import authorize_transition, require_owner
from forge.core.transitions import (
    INITIATIVE_CREATED,
    STEP_TRANSITIONED,
    WorkflowStateReducer,
    resolve_transition,
)
from forge.errors import (
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    IntegrityError,
    TransitionError,
)
from forge.packs.loader import find_pack
from forge.packs.validation import ValidatedPack, validate_pack
from forge.storage.configuration import load_configuration
from forge.storage.journal import read_journal
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot, inspect_snapshot_integrity


@dataclass(frozen=True)
class ActiveInitiative:
    layout: RepositoryLayout
    initiative: Initiative
    pack_manifest: PackManifest
    pack_trust: PackTrustDecision
    workflow: WorkflowDefinition
    state: MaterializedState

    @property
    def reducer(self) -> WorkflowStateReducer:
        return WorkflowStateReducer(self.workflow, self.initiative.owner_identity_id)


@dataclass(frozen=True)
class InitiativeCreationResult:
    active: ActiveInitiative
    creation_event: AuditEvent


@dataclass(frozen=True)
class TransitionResult:
    state: MaterializedState
    event: AuditEvent


@dataclass(frozen=True)
class ManualRunResult:
    active: ActiveInitiative
    run: RunRecord
    transition: TransitionResult


def _require_empty_active_directory(layout: RepositoryLayout) -> None:
    contents = tuple(layout.active_directory.iterdir())
    if contents:
        raise ConflictError(
            "An active initiative or unmanaged active-state content already exists: "
            f"{[path.name for path in contents]}"
        )


def _input_context_digest(active: ActiveInitiative, step_id: str) -> str:
    payload = {
        "initiative_id": str(active.initiative.id),
        "journal_head_sequence": active.state.journal_head_sequence,
        "step_id": step_id,
        "workflow_id": active.workflow.id,
        "workflow_version": active.workflow.version,
    }
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def create_initiative(
    layout: RepositoryLayout,
    *,
    objective: str,
    declared_scope_summary: str,
    actor: Actor,
    trust_pack_data: bool,
    pack_id: str = "software-basic",
    workflow_id: str | None = None,
    explanation_profile: ExplanationProfile | None = None,
) -> InitiativeCreationResult:
    configuration = load_configuration(layout.configuration_file)
    require_owner(actor, configuration.owner.id, "create an initiative")
    if not objective.strip():
        raise ConfigurationError("Initiative objective must not be empty")
    if not declared_scope_summary.strip():
        raise ConfigurationError("Initiative scope summary must not be empty")
    if not trust_pack_data:
        raise AuthorizationError(
            "Initiative creation requires explicit owner confirmation that the selected pack "
            "is trusted as data; executable capabilities remain separately disabled"
        )
    _require_empty_active_directory(layout)
    pack = find_pack(layout, configuration, pack_id)
    workflow = pack.workflow(workflow_id)
    selected_profile = explanation_profile or configuration.behavior.explanation_profile
    if selected_profile not in {ExplanationProfile.STANDARD, ExplanationProfile.GUIDED}:
        raise ConfigurationError(
            "M1 supports only standard and guided explanation profiles"
        )
    now = utc_now()
    initiative_id = uuid4()
    event_id = uuid4()
    trust_id = uuid4()
    authorization_basis = (
        "configured owner explicitly trusted the selected pack as data and created the initiative"
    )
    trust = PackTrustDecision(
        id=trust_id,
        initiative_id=initiative_id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=1,
        authorization_basis=authorization_basis,
        affected_record_ids=(initiative_id,),
        affected_digests=(pack.manifest.integrity_digest,),
        pack_id=pack.manifest.id,
        pack_version=pack.manifest.version,
        trust_state=PackTrustState.TRUSTED_DATA,
        rationale="Owner confirmed this exact validated pack version for the initiative",
        actor=actor,
    )
    initiative = Initiative(
        id=initiative_id,
        initiative_id=initiative_id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=1,
        authorization_basis=authorization_basis,
        affected_record_ids=(trust_id,),
        affected_digests=(pack.manifest.integrity_digest,),
        objective=objective,
        pack_id=pack.manifest.id,
        pack_version=pack.manifest.version,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        owner_identity_id=configuration.owner.id,
        creation_event_id=event_id,
        lifecycle_state=InitiativeLifecycleState.ACTIVE,
        explanation_profile=selected_profile,
        declared_scope_summary=declared_scope_summary,
    )
    event = AuditEvent(
        id=event_id,
        initiative_id=initiative_id,
        sequence=1,
        timestamp=now,
        event_type=INITIATIVE_CREATED,
        actor=actor,
        authorization_basis=authorization_basis,
        affected_record_ids=(initiative_id, trust_id),
        affected_digests=(pack.manifest.integrity_digest,),
        metadata={
            "pack_id": pack.manifest.id,
            "pack_version": pack.manifest.version,
            "pack_trust_decision_id": str(trust_id),
            "workflow_id": workflow.id,
            "workflow_version": workflow.version,
        },
    )
    created: list[Path] = []
    try:
        records = (
            (layout.initiative_file, initiative),
            (layout.pack_lock_file, pack.manifest),
            (layout.pack_trust_file, trust),
            (layout.workflow_lock_file, workflow),
        )
        for path, record in records:
            write_record(path, record)
            created.append(path)
        reducer = WorkflowStateReducer(workflow, configuration.owner.id)
        state = append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            reducer,
        )
    except Exception:
        committed = False
        if layout.event_journal_file.exists():
            try:
                committed = bool(read_journal(layout.event_journal_file))
            except IntegrityError:
                committed = True
        if not committed:
            for path in reversed(created):
                path.unlink(missing_ok=True)
        raise
    active = ActiveInitiative(layout, initiative, pack.manifest, trust, workflow, state)
    return InitiativeCreationResult(active, event)


def load_active_initiative(layout: RepositoryLayout) -> ActiveInitiative:
    if not layout.initiative_file.exists():
        raise ConflictError("No active initiative exists; run 'forge create' first")
    configuration = load_configuration(layout.configuration_file)
    initiative = load_record(layout.initiative_file, Initiative)
    manifest = load_record(layout.pack_lock_file, PackManifest)
    trust = load_record(layout.pack_trust_file, PackTrustDecision)
    workflow = load_record(layout.workflow_lock_file, WorkflowDefinition)
    locked_pack = ValidatedPack(layout.active_directory, manifest, (workflow,))
    try:
        validate_pack(locked_pack)
    except ConfigurationError as error:
        raise IntegrityError(f"Invalid locked pack data: {error}") from error
    if (
        initiative.pack_id != manifest.id
        or initiative.pack_version != manifest.version
        or initiative.workflow_id != workflow.id
        or initiative.workflow_version != workflow.version
        or workflow.pack_id != manifest.id
    ):
        raise IntegrityError("Initiative identity does not match its pack and workflow locks")
    if initiative.owner_identity_id != configuration.owner.id:
        raise IntegrityError("Initiative owner does not match the repository owner configuration")
    if (
        trust.initiative_id != initiative.id
        or trust.actor_id != trust.actor.id
        or trust.pack_id != manifest.id
        or trust.pack_version != manifest.version
        or trust.trust_state is not PackTrustState.TRUSTED_DATA
    ):
        raise IntegrityError("Pack trust record does not authorize the locked pack")
    try:
        require_owner(trust.actor, configuration.owner.id, "record pack data trust")
    except AuthorizationError as error:
        raise IntegrityError(f"Invalid pack trust authority: {error}") from error
    events = read_journal(layout.event_journal_file)
    if not events or events[0].id != initiative.creation_event_id:
        raise IntegrityError("Initiative creation event does not match the journal")
    creation_metadata = events[0].metadata
    if (
        creation_metadata.get("pack_id") != manifest.id
        or creation_metadata.get("pack_version") != manifest.version
        or creation_metadata.get("workflow_id") != workflow.id
        or creation_metadata.get("workflow_version") != workflow.version
        or creation_metadata.get("pack_trust_decision_id") != str(trust.id)
    ):
        raise IntegrityError("Initiative creation event does not match locked records")
    reducer = WorkflowStateReducer(workflow, configuration.owner.id)
    try:
        report = inspect_snapshot_integrity(
            layout.event_journal_file,
            layout.state_file,
            reducer,
        )
    except (AuthorizationError, TransitionError) as error:
        raise IntegrityError(f"Journal violates locked governance rules: {error}") from error
    if not report.is_healthy or report.replayed_state is None:
        details = report.diagnostics or ("Journal replay did not produce active state",)
        raise IntegrityError("; ".join(details))
    if report.replayed_state.initiative_id != initiative.id:
        raise IntegrityError("Materialized state belongs to a different initiative")
    from forge.core.record_validation import validate_increment4_records

    validate_increment4_records(
        layout,
        events,
        report.replayed_state,
        workflow,
    )
    for run_id in report.replayed_state.active_run_ids:
        run = load_record(layout.governed_run_directory / f"{run_id}.json", RunRecord)
        run_event = next(
            (
                event
                for event in events
                if event.run_id == run_id and event.sequence == run.event_sequence
            ),
            None,
        )
        if (
            run.id != run_id
            or run.initiative_id != initiative.id
            or run.status is not RunState.RUNNING
            or report.replayed_state.step_states.get(run.step_id) is not StepState.IN_PROGRESS
            or run_event is None
            or run_event.actor != run.worker
        ):
            raise IntegrityError(f"Active run record is inconsistent: {run_id}")
    return ActiveInitiative(
        layout,
        initiative,
        manifest,
        trust,
        workflow,
        report.replayed_state,
    )


def transition_step(
    layout: RepositoryLayout,
    *,
    step_id: str,
    transition_id: str,
    actor: Actor,
    run_id: UUID | None = None,
    affected_record_ids: tuple[UUID, ...] = (),
) -> TransitionResult:
    active = load_active_initiative(layout)
    return apply_record_backed_transition(
        active,
        step_id=step_id,
        transition_id=transition_id,
        actor=actor,
        run_id=run_id,
        affected_record_ids=affected_record_ids,
        condition_record_ids={},
    )


def apply_record_backed_transition(
    active: ActiveInitiative,
    *,
    step_id: str,
    transition_id: str,
    actor: Actor,
    run_id: UUID | None = None,
    affected_record_ids: tuple[UUID, ...] = (),
    condition_record_ids: dict[str, tuple[UUID, ...]],
) -> TransitionResult:
    layout = active.layout
    current = active.state.step_states.get(step_id)
    if current is None:
        raise TransitionError(f"Unknown workflow step {step_id!r}")
    step, transition = resolve_transition(active.workflow, step_id, transition_id, current)
    required_conditions = set(transition.conditions)
    supplied_conditions = set(condition_record_ids)
    if required_conditions != supplied_conditions or any(
        not record_ids for record_ids in condition_record_ids.values()
    ):
        missing = sorted(required_conditions - supplied_conditions)
        unsupported = sorted(supplied_conditions - required_conditions)
        details: list[str] = []
        if missing:
            details.append(f"unmet conditions: {missing}")
        if unsupported:
            details.append(f"unsupported conditions: {unsupported}")
        if not details:
            details.append("every condition requires governed supporting records")
        raise TransitionError(
            f"Transition {transition.id} is blocked; {'; '.join(details)}"
        )
    authorize_transition(actor, active.initiative.owner_identity_id, step, transition)
    sequence = active.state.journal_head_sequence + 1
    if transition.destination_state is StepState.IN_PROGRESS:
        if run_id is None:
            raise TransitionError(f"Transition {transition.id} requires a durable run record")
        run = load_record(layout.governed_run_directory / f"{run_id}.json", RunRecord)
        if (
            run.id != run_id
            or run.initiative_id != active.initiative.id
            or run.step_id != step_id
            or run.worker != actor
            or run.status is not RunState.RUNNING
            or run.event_sequence != sequence
        ):
            raise IntegrityError(f"Run record does not authorize transition {transition.id}")
    elif transition.source_state is StepState.IN_PROGRESS:
        if run_id is None or run_id not in active.state.active_run_ids:
            raise TransitionError(f"Transition {transition.id} requires the active step run ID")
        run = load_record(layout.governed_run_directory / f"{run_id}.json", RunRecord)
        if (
            run.initiative_id != active.initiative.id
            or run.step_id != step_id
            or run.worker != actor
            or run.status is not RunState.RUNNING
        ):
            raise IntegrityError(f"Active run does not authorize transition {transition.id}")
    supporting_ids = tuple(
        record_id
        for condition in sorted(condition_record_ids)
        for record_id in condition_record_ids[condition]
    )
    all_affected_ids = tuple(dict.fromkeys((*affected_record_ids, *supporting_ids)))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=utc_now(),
        event_type=STEP_TRANSITIONED,
        actor=actor,
        run_id=run_id,
        authorization_basis=(
            f"actor satisfied locked authority requirement {transition.authority_requirement}"
        ),
        affected_record_ids=all_affected_ids,
        metadata={
            "destination_state": transition.destination_state.value,
            "source_state": transition.source_state.value,
            "step_id": step.id,
            "transition_id": transition.id,
            "verified_conditions": sorted(condition_record_ids),
            "condition_record_ids": {
                condition: [str(record_id) for record_id in record_ids]
                for condition, record_ids in sorted(condition_record_ids.items())
            },
        },
    )
    state = append_event_and_update_snapshot(
        layout.event_journal_file,
        layout.state_file,
        event,
        active.reducer,
    )
    return TransitionResult(state, event)


def begin_manual_run(
    layout: RepositoryLayout,
    *,
    step_id: str,
    actor: Actor,
    side_effect_class: SideEffectClass = SideEffectClass.REPOSITORY_WRITE,
) -> ManualRunResult:
    active = load_active_initiative(layout)
    current = active.state.step_states.get(step_id)
    if current is None:
        raise TransitionError(f"Unknown workflow step {step_id!r}")
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise TransitionError(f"Unknown workflow step {step_id!r}")
    begin_transition = next(
        (
            transition
            for transition in active.workflow.transitions
            if transition.source_state is current
            and transition.destination_state is StepState.IN_PROGRESS
            and transition.id in step.allowed_transitions
        ),
        None,
    )
    if begin_transition is None:
        raise TransitionError(f"Step {step_id} cannot begin from state {current.value}")
    run_id = uuid4()
    next_sequence = active.state.journal_head_sequence + 1
    run = RunRecord(
        id=run_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=utc_now(),
        event_sequence=next_sequence,
        authorization_basis="manual participant began an eligible workflow step",
        affected_record_ids=(run_id,),
        step_id=step_id,
        worker=actor,
        side_effect_class=side_effect_class,
        status=RunState.RUNNING,
        started_at=utc_now(),
        input_context_digest=_input_context_digest(active, step_id),
        exit_metadata={},
    )
    runs_created = False
    if not layout.governed_run_directory.exists():
        try:
            layout.governed_run_directory.mkdir()
        except OSError as error:
            raise IntegrityError(f"Cannot create governed run directory: {error}") from error
        runs_created = True
    run_path = layout.governed_run_directory / f"{run_id}.json"
    write_record(run_path, run)
    try:
        transition = transition_step(
            layout,
            step_id=step_id,
            transition_id=begin_transition.id,
            actor=actor,
            run_id=run_id,
            affected_record_ids=(run_id,),
        )
    except Exception:
        events = read_journal(layout.event_journal_file)
        if len(events) < next_sequence:
            run_path.unlink(missing_ok=True)
            if runs_created:
                with suppress(OSError):
                    layout.governed_run_directory.rmdir()
        raise
    refreshed = load_active_initiative(layout)
    return ManualRunResult(refreshed, run, transition)
