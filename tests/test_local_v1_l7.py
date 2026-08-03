import shutil
import subprocess
from pathlib import Path
from uuid import UUID

from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor
from forge.contracts.verification import CheckOutcome
from forge.core.acceptance import record_acceptance
from forge.core.archival import abandon_initiative, close_initiative
from forge.core.artifacts import add_artifact
from forge.core.authorization import owner_actor
from forge.core.decisions import record_decision
from forge.core.lifecycle import begin_manual_run, create_initiative
from forge.core.successor_briefs import build_successor_brief
from forge.core.verification import (
    complete_step,
    record_check,
    record_evidence,
    verify_step,
)
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _run_git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


def _closed_initiative(
    root: Path,
) -> tuple[InitializationResult, Actor, UUID, UUID]:
    initialized = initialize_repository(root, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    created = create_initiative(
        initialized.layout,
        objective="Ship a governed predecessor with durable transition material",
        declared_scope_summary="Produce accepted work, support, risk, and lessons",
        actor=actor,
        trust_pack_data=True,
    )
    decision = record_decision(
        initialized.layout,
        decision_type="successor-direction",
        question="Which boundary should the next milestone preserve?",
        considered_options=("Preserve exact bytes", "Recreate from chat memory"),
        chosen_outcome="Preserve exact bytes",
        rationale="Exact governed revisions are durable and independently verifiable",
        actor=actor,
    )
    for step in created.active.workflow.steps:
        begin_manual_run(initialized.layout, step_id=step.id, actor=actor)
        revision_ids: list[UUID] = []
        for role in step.required_outputs:
            path = f"outputs/{role}.md"
            target = root / path
            target.parent.mkdir(exist_ok=True)
            target.write_text(f"# {role}\nDurable output for {step.id}.\n", encoding="utf-8")
            added = add_artifact(
                initialized.layout,
                path=path,
                role=role,
                title=f"{role} output",
                actor=actor,
                media_type="text/markdown",
            )
            revision_ids.append(added.revision.id)
        claim = complete_step(
            initialized.layout,
            step_id=step.id,
            assertion=f"Produced declared outputs for {step.id}",
            actor=actor,
        )
        is_closeout = step.id == "close"
        check = record_check(
            initialized.layout,
            step_id=step.id,
            check_id=step.check_requirements[0],
            check_version="1",
            invocation_metadata={"invocation": "manual governed review"},
            outcome=CheckOutcome.PASSED,
            actor=actor,
            exit_status=0,
            limitations=("Privileged symbolic links were not exercised",)
            if is_closeout
            else (),
        )
        record_evidence(
            initialized.layout,
            step_id=step.id,
            purpose=f"Bind current outputs and check for {step.id}",
            actor=actor,
            artifact_revision_ids=tuple(revision_ids),
            check_result_ids=(check.check.id,),
            claim_ids=(claim.claim.id,),
            limitations=("Owner-observed behavior remains separate",)
            if is_closeout
            else (),
        )
        verify_step(initialized.layout, step_id=step.id)
        record_acceptance(
            initialized.layout,
            step_id=step.id,
            accepted_scope=f"Current {step.id} outputs",
            actor=actor,
            known_limitations=("Local-only operation",) if is_closeout else (),
            residual_risks=("Future dependencies may change",) if is_closeout else (),
        )
    closed = close_initiative(
        initialized.layout,
        closing_summary="Accepted work and lessons are ready for a distinct successor",
        actor=actor,
    )
    return initialized, actor, closed.closure.initiative_id, decision.decision.id


def test_successor_brief_survives_clean_archive_only_checkout_and_new_successor(
    tmp_path: Path,
) -> None:
    initialized, actor, archive_id, decision_id = _closed_initiative(tmp_path)
    archive_root = initialized.layout.archive_directory / str(archive_id)
    archive_bytes = {
        path.relative_to(archive_root): path.read_bytes()
        for path in archive_root.rglob("*")
        if path.is_file()
    }
    initialized.layout.active_directory.rmdir()
    shutil.rmtree(initialized.layout.local_directory)

    _run_git(tmp_path, "init")
    _run_git(tmp_path, "config", "user.name", "FORGE Tests")
    _run_git(tmp_path, "config", "user.email", "forge-tests@example.invalid")
    _run_git(tmp_path, "checkout", "-b", "main")
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-m", "Archive-only predecessor")

    result = runner.invoke(
        app,
        ["successor", "brief", "--archive", str(archive_id), "-C", str(tmp_path)],
    )
    assert result.exit_code == 0, result.stderr
    assert "# FORGE Successor Brief" in result.stdout
    assert "Archive validation: healthy" in result.stdout
    assert "Terminal outcome: `closed`" in result.stdout
    assert "Active initiative: none (archive-only repository state)" in result.stdout
    assert "Git branch: `main`" in result.stdout
    assert "Git worktree: clean" in result.stdout
    assert f"`{decision_id}` [successor-direction]" in result.stdout
    assert "### Accepted checks\n\n- none" not in result.stdout
    assert "### Accepted evidence\n\n- none" not in result.stdout
    assert "Privileged symbolic links were not exercised" in result.stdout
    assert "Future dependencies may change" in result.stdout
    assert "`lessons` - lessons output" in result.stdout
    assert "--predecessor-revision" in result.stdout
    assert not _run_git(tmp_path, "status", "--porcelain=v1").stdout
    assert {
        path.relative_to(archive_root): path.read_bytes()
        for path in archive_root.rglob("*")
        if path.is_file()
    } == archive_bytes

    successor = create_initiative(
        initialized.layout,
        objective="Continue from the validated milestone",
        declared_scope_summary="Fresh successor work only",
        actor=actor,
        trust_pack_data=True,
        predecessor_ids=(archive_id,),
    )
    refreshed = build_successor_brief(initialized.layout, archive_id)
    assert refreshed.observations.active_initiative_id == successor.active.initiative.id
    assert refreshed.observations.selected_archive_is_predecessor
    assert "declares the selected archive as a predecessor" in refreshed.markdown
    assert {
        path.relative_to(archive_root): path.read_bytes()
        for path in archive_root.rglob("*")
        if path.is_file()
    } == archive_bytes


def test_abandoned_successor_brief_preserves_risk_without_claiming_acceptance(
    tmp_path: Path,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Explore work that may stop unfinished",
        declared_scope_summary="Preserve partial bytes honestly",
        actor=actor,
        trust_pack_data=True,
    )
    output = tmp_path / "outputs" / "partial.md"
    output.parent.mkdir()
    output.write_text("Partial governed bytes\n", encoding="utf-8")
    revision = add_artifact(
        initialized.layout,
        path="outputs/partial.md",
        role="project-artifacts",
        title="Partial output",
        actor=actor,
        media_type="text/markdown",
    ).revision
    initialized.layout.scratchpad_file.parent.mkdir(parents=True, exist_ok=True)
    initialized.layout.scratchpad_file.write_text(
        "SECRET LOCAL IDEA THAT MUST NOT TRANSFER\n",
        encoding="utf-8",
    )
    abandoned = abandon_initiative(
        initialized.layout,
        reason="The owner stopped this route",
        unfinished_work_summary="Implementation and review remain unfinished",
        unresolved_risks=("No accepted outcome exists",),
        actor=actor,
    )

    brief = build_successor_brief(
        initialized.layout,
        abandoned.abandonment.initiative_id,
    )
    assert brief.archive.abandonment == abandoned.abandonment
    assert brief.revisions[0].revision.id == revision.id
    assert not brief.revisions[0].accepted
    assert "### Accepted artifacts\n\n- none" in brief.markdown
    assert "[not accepted]" in brief.markdown
    assert "No accepted outcome exists" in brief.markdown
    assert "SECRET LOCAL IDEA THAT MUST NOT TRANSFER" not in brief.markdown
