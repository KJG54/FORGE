import json
from pathlib import Path
from uuid import uuid4

import pytest

from forge.contracts.actors import Actor, ActorType
from forge.contracts.packs import PackTrustState
from forge.contracts.runs import RunRecord
from forge.contracts.state import IntegrityState, RunState, StepState
from forge.core.authorization import owner_actor
from forge.core.lifecycle import (
    begin_manual_run,
    create_initiative,
    load_active_initiative,
    transition_step,
)
from forge.core.status import inspect_status
from forge.errors import AuthorizationError, ConflictError, IntegrityError, TransitionError
from forge.storage.journal import read_journal
from forge.storage.records import load_record
from forge.storage.repository import InitializationResult, initialize_repository


def _initialized(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    result = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    return result, owner_actor(result.configuration.owner)


def _create(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized, actor = _initialized(tmp_path)
    create_initiative(
        initialized.layout,
        objective="Deliver a small governed change",
        declared_scope_summary="One bounded local change",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _agent_actor() -> Actor:
    return Actor(
        id=uuid4(),
        actor_type=ActorType.AGENT_ADAPTER,
        display_label="Untrusted agent adapter",
        tool_reference="example-agent",
    )


def test_create_requires_explicit_pack_trust_and_owner_authority(tmp_path: Path) -> None:
    initialized, actor = _initialized(tmp_path)
    with pytest.raises(AuthorizationError, match="explicit owner confirmation"):
        create_initiative(
            initialized.layout,
            objective="Objective",
            declared_scope_summary="Scope",
            actor=actor,
            trust_pack_data=False,
        )
    assert not any(initialized.layout.active_directory.iterdir())

    with pytest.raises(AuthorizationError, match="Only configured owner"):
        create_initiative(
            initialized.layout,
            objective="Objective",
            declared_scope_summary="Scope",
            actor=_agent_actor(),
            trust_pack_data=True,
        )
    assert not any(initialized.layout.active_directory.iterdir())


def test_create_locks_pack_and_workflow_and_reloads_from_disk(tmp_path: Path) -> None:
    initialized, actor = _initialized(tmp_path)
    result = create_initiative(
        initialized.layout,
        objective="Deliver a small governed change",
        declared_scope_summary="One bounded local change",
        actor=actor,
        trust_pack_data=True,
    )

    assert result.active.pack_trust.trust_state is PackTrustState.TRUSTED_DATA
    assert result.active.state.step_states["discover"] is StepState.READY
    assert result.active.state.step_states["plan"] is StepState.PENDING
    assert result.active.state.permitted_next_actions == ("begin:discover",)
    assert result.active.layout.initiative_file.is_file()
    assert result.active.layout.pack_lock_file.is_file()
    assert result.active.layout.pack_trust_file.is_file()
    assert result.active.layout.workflow_lock_file.is_file()
    assert read_journal(result.active.layout.event_journal_file) == (
        result.creation_event,
    )

    restarted = load_active_initiative(initialized.layout)
    assert restarted.initiative == result.active.initiative
    assert restarted.workflow == result.active.workflow
    assert restarted.state == result.active.state
    status = inspect_status(initialized.layout)
    assert status.integrity_state is IntegrityState.HEALTHY
    assert status.next_actions == ("begin:discover",)

    with pytest.raises(ConflictError, match="already exists"):
        create_initiative(
            initialized.layout,
            objective="Second initiative",
            declared_scope_summary="Not allowed concurrently",
            actor=actor,
            trust_pack_data=True,
        )


def test_manual_begin_enforces_readiness_actor_rules_and_restart(tmp_path: Path) -> None:
    initialized, actor = _create(tmp_path)
    with pytest.raises(TransitionError, match="durable run record"):
        transition_step(
            initialized.layout,
            step_id="discover",
            transition_id="begin",
            actor=actor,
        )
    with pytest.raises(TransitionError, match="cannot begin from state pending"):
        begin_manual_run(initialized.layout, step_id="plan", actor=actor)
    with pytest.raises(AuthorizationError, match="not allowed"):
        begin_manual_run(
            initialized.layout,
            step_id="discover",
            actor=_agent_actor().model_copy(
                update={"actor_type": ActorType.EXTERNAL_TOOL}
            ),
        )
    assert not initialized.layout.governed_run_directory.exists()

    result = begin_manual_run(initialized.layout, step_id="discover", actor=actor)

    assert result.run.status is RunState.RUNNING
    assert result.transition.state.step_states["discover"] is StepState.IN_PROGRESS
    assert result.run.id in result.transition.state.active_run_ids
    assert result.transition.state.permitted_next_actions == ("complete:discover",)
    assert len(read_journal(initialized.layout.event_journal_file)) == 2
    run_path = initialized.layout.governed_run_directory / f"{result.run.id}.json"
    assert load_record(run_path, RunRecord) == result.run

    restarted = load_active_initiative(initialized.layout)
    assert restarted.state == result.transition.state
    assert inspect_status(initialized.layout).next_actions == ("complete:discover",)


def test_transition_conditions_cannot_be_asserted_by_omission(tmp_path: Path) -> None:
    initialized, actor = _create(tmp_path)
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)

    with pytest.raises(TransitionError, match="claim-recorded"):
        transition_step(
            initialized.layout,
            step_id="discover",
            transition_id="submit",
            actor=actor,
        )
    assert len(read_journal(initialized.layout.event_journal_file)) == 2


def test_changed_workflow_lock_is_an_integrity_error_and_blocks_mutation(
    tmp_path: Path,
) -> None:
    initialized, actor = _create(tmp_path)
    lock = initialized.layout.workflow_lock_file
    payload = json.loads(lock.read_text(encoding="utf-8"))
    payload["name"] = "Tampered workflow"
    lock.write_text(json.dumps(payload), encoding="utf-8")

    report = inspect_status(initialized.layout)
    assert report.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert "digest mismatch" in report.blockers[0]
    with pytest.raises(IntegrityError, match="digest mismatch"):
        begin_manual_run(initialized.layout, step_id="discover", actor=actor)


def test_missing_active_run_record_is_an_integrity_error(tmp_path: Path) -> None:
    initialized, actor = _create(tmp_path)
    result = begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    run_path = initialized.layout.governed_run_directory / f"{result.run.id}.json"
    run_path.unlink()

    report = inspect_status(initialized.layout)

    assert report.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert "Governed record is missing" in report.blockers[0]
