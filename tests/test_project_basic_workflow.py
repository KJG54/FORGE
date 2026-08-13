"""Lifecycle and read-only-template coverage for the bundled project workflow."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.state import StepState
from forge.contracts.verification import CheckOutcome
from forge.core.acceptance import record_acceptance
from forge.core.artifacts import add_artifact, list_artifacts, revise_artifact
from forge.core.authorization import owner_actor
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.verification import complete_step, record_check, record_evidence, verify_step
from forge.storage.repository import initialize_repository

PROJECT_TEMPLATES = (
    "templates/human-vision-brief.md",
    "templates/owner-context-and-learning-profile.md",
    "templates/context-readiness-report.md",
    "templates/project-research.md",
    "templates/project-plan.md",
    "templates/task-map.md",
    "templates/acceptance-criteria.md",
    "templates/evaluation-report.md",
    "templates/review-report.md",
    "templates/lessons.md",
    "templates/closure-record.md",
)

runner = CliRunner()


def test_project_templates_are_read_only_before_and_after_lock(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Project Template Owner")
    available = runner.invoke(
        app, ["pack", "template", "list", "project-basic", "-C", str(tmp_path)]
    )
    assert available.exit_code == 0, available.stderr
    assert "Templates from available project-basic@0.1.0" in available.stdout
    assert all(template in available.stdout for template in PROJECT_TEMPLATES)

    shown = runner.invoke(
        app,
        [
            "pack",
            "template",
            "show",
            "project-basic",
            "templates/evaluation-report.md",
            "-C",
            str(tmp_path),
        ],
    )
    assert shown.exit_code == 0, shown.stderr
    assert "Created-work artifact revision ID" in shown.stdout
    assert "Acceptance-criteria artifact revision ID" in shown.stdout

    create_initiative(
        initialized.layout,
        objective="Exercise project templates",
        declared_scope_summary="Read-only template inspection",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
        pack_id="project-basic",
    )
    locked = runner.invoke(
        app, ["pack", "template", "list", "project-basic", "-C", str(tmp_path)]
    )
    assert locked.exit_code == 0, locked.stderr
    assert "Templates from locked project-basic@0.1.0" in locked.stdout


def test_project_workflow_completes_then_revising_created_work_requires_rework(
    tmp_path: Path,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Project Lifecycle Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Exercise all project-basic phases",
        declared_scope_summary="Temporary lifecycle coverage only",
        actor=actor,
        trust_pack_data=True,
        pack_id="project-basic",
    )
    workflow = load_active_initiative(initialized.layout).workflow
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()

    for step in workflow.steps:
        begin_manual_run(initialized.layout, step_id=step.id, actor=actor)
        revision_ids: list[UUID] = []
        for role in step.required_outputs:
            path = artifact_root / f"{role}.md"
            path.write_text(f"{role} for {step.id}\n", encoding="utf-8")
            added = add_artifact(
                initialized.layout,
                path=path.relative_to(tmp_path).as_posix(),
                role=role,
                title=role.replace("-", " ").title(),
                actor=actor,
            )
            revision_ids.append(added.revision.id)
        claim = complete_step(
            initialized.layout,
            step_id=step.id,
            assertion=f"Temporary {step.id} outputs produced",
            actor=actor,
        )
        check_ids: list[UUID] = []
        for check_id in step.check_requirements:
            check = record_check(
                initialized.layout,
                step_id=step.id,
                check_id=check_id,
                check_version="1",
                invocation_metadata={"invocation": "temporary project lifecycle review"},
                outcome=CheckOutcome.PASSED,
                actor=actor,
                exit_status=0,
            )
            check_ids.append(check.check.id)
        record_evidence(
            initialized.layout,
            step_id=step.id,
            purpose=f"Bind temporary {step.id} support",
            actor=actor,
            artifact_revision_ids=tuple(revision_ids),
            check_result_ids=tuple(check_ids),
            claim_ids=(claim.claim.id,),
        )
        verify_step(initialized.layout, step_id=step.id)
        record_acceptance(
            initialized.layout,
            step_id=step.id,
            accepted_scope=f"Temporary {step.id} outputs",
            actor=actor,
        )

    active = load_active_initiative(initialized.layout)
    assert all(state is StepState.COMPLETED for state in active.state.step_states.values())
    created = next(
        artifact
        for artifact in list_artifacts(initialized.layout)
        if artifact.artifact.role == "created-work"
    )
    created_path = artifact_root / "created-work.md"
    created_path.write_text("revised created work\n", encoding="utf-8")
    revise_artifact(
        initialized.layout,
        artifact_id=created.artifact.id,
        path=created_path.relative_to(tmp_path).as_posix(),
        actor=actor,
    )

    invalidated = load_active_initiative(initialized.layout)
    assert invalidated.state.step_states["create"] is StepState.INVALIDATED
    assert invalidated.state.step_states["evaluate"] is StepState.INVALIDATED
    assert invalidated.state.step_states["review"] is StepState.INVALIDATED
    assert invalidated.state.step_states["close"] is StepState.INVALIDATED
    rework = begin_manual_run(initialized.layout, step_id="create", actor=actor)
    assert rework.transition.state.step_states["create"] is StepState.IN_PROGRESS
