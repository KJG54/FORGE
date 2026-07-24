from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.state import StepState
from forge.contracts.verification import CheckOutcome
from forge.contracts.workflows import StepDefinition
from forge.core.acceptance import AcceptanceRecordingResult, record_acceptance
from forge.core.agent_context import build_agent_context
from forge.core.archival import abandon_initiative, load_archive
from forge.core.artifacts import ArtifactMutationResult, add_artifact
from forge.core.authorization import owner_actor
from forge.core.lifecycle import (
    begin_manual_run,
    create_initiative,
    load_active_initiative,
)
from forge.core.runs import cancel_run
from forge.core.scope_amendments import (
    ScopeAmendmentResult,
    amend_scope,
    list_scope_amendments,
    show_scope_amendment,
)
from forge.core.verification import (
    CompletionResult,
    EvidenceRecordingResult,
    complete_step,
    record_check,
    record_evidence,
    verify_step,
)
from forge.errors import (
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    IntegrityError,
    TransitionError,
)
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Deliver governed work under an amendable scope",
        declared_scope_summary="Original bounded scope",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _accept_discover(
    initialized: InitializationResult,
    actor: Actor,
) -> tuple[
    CompletionResult,
    EvidenceRecordingResult,
    AcceptanceRecordingResult,
    StepDefinition,
    tuple[ArtifactMutationResult, ...],
]:
    layout = initialized.layout
    active = load_active_initiative(layout)
    step = next(item for item in active.workflow.steps if item.id == "discover")
    begin_manual_run(layout, step_id=step.id, actor=actor)
    artifact_results: list[ArtifactMutationResult] = []
    for role in step.required_outputs:
        relative = f"{role}.md"
        (layout.root / relative).write_text(f"# {role}\n\nGoverned fixture.\n", encoding="utf-8")
        artifact_results.append(
            add_artifact(
                layout,
                path=relative,
                role=role,
                title=role.replace("-", " ").title(),
                media_type="text/markdown",
                actor=actor,
            )
        )
    completion = complete_step(
        layout,
        step_id=step.id,
        assertion="All declared discovery outputs are present",
        actor=actor,
    )
    checks = tuple(
        record_check(
            layout,
            step_id=step.id,
            check_id=check_id,
            check_version="1.0.0",
            invocation_metadata={"method": "manual fixture inspection"},
            outcome=CheckOutcome.PASSED,
            exit_status=0,
            actor=actor,
        )
        for check_id in step.check_requirements
    )
    revision_ids = tuple(item.revision.id for item in artifact_results)
    evidence = record_evidence(
        layout,
        step_id=step.id,
        purpose="Bind the current discovery claim, checks, and revisions",
        artifact_revision_ids=revision_ids,
        check_result_ids=tuple(item.check.id for item in checks),
        claim_ids=(completion.claim.id,),
        actor=actor,
    )
    verify_step(layout, step_id=step.id)
    acceptance = record_acceptance(
        layout,
        step_id=step.id,
        accepted_scope="Current discovery outputs only",
        actor=actor,
    )
    return completion, evidence, acceptance, step, tuple(artifact_results)


def test_scope_amendment_derives_staleness_and_returns_work_without_waiver(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    completion, evidence, acceptance, _, artifacts = _accept_discover(initialized, actor)
    check_id = acceptance.acceptance.accepted_check_result_ids[0]
    requirements_artifact = next(
        item for item in artifacts if item.artifact.role == "requirements"
    )

    result = amend_scope(
        initialized.layout,
        changed_scope="Revised scope requiring an explicit compatibility constraint",
        rationale="The owner added a material requirement after discovery acceptance",
        affected_requirements=("requirements", "outputs-present"),
        affected_artifact_ids=(requirements_artifact.artifact.id,),
        workflow_return_step_id="discover",
        actor=actor,
    )

    active = load_active_initiative(initialized.layout)
    assert active.state.step_states["discover"] is StepState.INVALIDATED
    assert all(
        active.state.step_states[step.id] is StepState.PENDING
        for step in active.workflow.steps
        if step.id != "discover"
    )
    expected_stale = {
        completion.claim.id,
        check_id,
        evidence.evidence.id,
        acceptance.acceptance.id,
    }
    assert expected_stale.issubset(active.state.stale_record_ids)
    assert result.amendment.invalidated_check_ids == (check_id,)
    assert result.amendment.invalidated_acceptance_ids == (
        acceptance.acceptance.id,
    )
    assert result.amendment.affected_artifact_ids == (
        requirements_artifact.artifact.id,
    )
    assert build_agent_context(initialized.layout).approved_scope == (
        "Revised scope requiring an explicit compatibility constraint"
    )
    assert show_scope_amendment(initialized.layout, result.amendment.id) == result.amendment
    assert list_scope_amendments(initialized.layout) == (result.amendment,)

    with pytest.raises(ConflictError, match="not awaiting verification"):
        verify_step(initialized.layout, step_id="discover")
    with pytest.raises(ConflictError, match="not awaiting acceptance"):
        record_acceptance(
            initialized.layout,
            step_id="discover",
            accepted_scope="Amendment cannot waive renewed support",
            actor=actor,
        )
    restarted = begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    assert restarted.transition.state.step_states["discover"] is StepState.IN_PROGRESS


def _simple_amendment(
    initialized: InitializationResult,
    actor: Actor,
    *,
    affected_requirements: tuple[str, ...] = ("requirements",),
) -> ScopeAmendmentResult:
    return amend_scope(
        initialized.layout,
        changed_scope="Revised bounded scope",
        rationale="Material requirement changed",
        affected_requirements=affected_requirements,
        affected_artifact_ids=(),
        workflow_return_step_id="discover",
        actor=actor,
    )


def test_scope_amendment_requires_owner_known_requirements_and_no_active_run(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        _simple_amendment(initialized, outsider)
    with pytest.raises(ConfigurationError, match="Unknown affected"):
        _simple_amendment(
            initialized,
            actor,
            affected_requirements=("not-in-workflow",),
        )

    run = begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    with pytest.raises(ConflictError, match="cancel them first"):
        _simple_amendment(initialized, actor)
    cancel_run(
        initialized.layout,
        run_id=run.run.id,
        reason="Release work before changing its governing scope",
        actor=actor,
    )
    amended = _simple_amendment(initialized, actor)
    assert amended.amendment.workflow_return_step_id == "discover"
    assert load_active_initiative(initialized.layout).state.step_states[
        "discover"
    ] is StepState.INVALIDATED


def test_scope_cli_is_idempotent_and_restart_validation_detects_tampering(
    tmp_path: Path,
) -> None:
    initialized, _ = _initiative(tmp_path)
    arguments = [
        "scope",
        "amend",
        "--scope",
        "CLI-amended effective scope",
        "--rationale",
        "Owner changed the discovery boundary",
        "--return-to",
        "discover",
        "--requirement",
        "requirements",
        "--idempotency-key",
        "scope-amendment-fixture",
        "-C",
        str(initialized.layout.root),
    ]
    first = runner.invoke(app, arguments)
    assert first.exit_code == 0, first.stdout
    replay = runner.invoke(app, arguments)
    assert replay.exit_code == 0, replay.stdout
    amendments = list_scope_amendments(initialized.layout)
    assert len(amendments) == 1
    shown = runner.invoke(
        app,
        [
            "scope",
            "show",
            str(amendments[0].id),
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert shown.exit_code == 0, shown.stdout
    assert "CLI-amended effective scope" in shown.stdout
    status = runner.invoke(
        app,
        ["status", "-C", str(initialized.layout.root)],
    )
    assert status.exit_code == 0, status.stdout
    assert "Declared scope: Original bounded scope" in status.stdout
    assert "Effective scope: CLI-amended effective scope" in status.stdout

    path = initialized.layout.scope_amendment_directory / f"{amendments[0].id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["changed_scope"] = "Forged broader scope"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Scope amendment does not match"):
        load_active_initiative(initialized.layout)


def test_scope_amendment_is_preserved_in_terminal_archive(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    amendment = _simple_amendment(initialized, actor).amendment
    abandoned = abandon_initiative(
        initialized.layout,
        reason="Stop after recording the amended boundary",
        unfinished_work_summary="All workflow work remains unfinished",
        unresolved_risks=("The amended outcome was not delivered",),
        actor=actor,
    )

    archive = load_archive(initialized.layout, abandoned.abandonment.initiative_id)
    path = archive.layout.scope_amendment_directory / f"{amendment.id}.json"
    assert path.is_file()
    assert archive.active.state.step_states["discover"] is StepState.INVALIDATED


def test_scope_amendment_does_not_unlock_a_pending_return_step(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    amended = amend_scope(
        initialized.layout,
        changed_scope="Execution scope changed before planning completed",
        rationale="Record the change without bypassing workflow prerequisites",
        affected_requirements=("project-artifacts",),
        affected_artifact_ids=(),
        workflow_return_step_id="execute",
        actor=actor,
    )

    active = load_active_initiative(initialized.layout)
    assert amended.amendment.workflow_return_step_id == "execute"
    assert active.state.step_states["execute"] is StepState.PENDING
    assert "begin:execute" not in active.state.permitted_next_actions
    with pytest.raises(TransitionError, match="cannot begin from state pending"):
        begin_manual_run(initialized.layout, step_id="execute", actor=actor)
