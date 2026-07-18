import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.state import StepState
from forge.contracts.verification import CheckOutcome
from forge.core.acceptance import record_acceptance
from forge.core.agent_context import (
    AgentContextTarget,
    build_agent_context,
    generate_agent_context,
    load_agent_context,
)
from forge.core.archival import abandon_initiative, load_archive
from forge.core.artifacts import add_artifact
from forge.core.authorization import owner_actor
from forge.core.decisions import record_decision
from forge.core.lifecycle import begin_manual_run, create_initiative
from forge.core.verification import (
    complete_step,
    record_check,
    record_evidence,
    verify_step,
)
from forge.errors import ConfigurationError, SecurityError
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> InitializationResult:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Produce a bounded implementation",
        declared_scope_summary="Only the accepted workflow outputs",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized


def _advance_to_plan(initialized: InitializationResult) -> None:
    actor = owner_actor(initialized.configuration.owner)
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    objective_path = initialized.layout.root / "objective.md"
    requirements_path = initialized.layout.root / "requirements.md"
    objective_path.write_text("NON_SELECTED_OBJECTIVE_SENTINEL", encoding="utf-8")
    requirements_path.write_text("SELECTED_REQUIREMENTS_SENTINEL", encoding="utf-8")
    objective = add_artifact(
        initialized.layout,
        path="objective.md",
        role="objective-and-constraints",
        title="Objective",
        actor=actor,
        media_type="text/markdown",
    )
    requirements = add_artifact(
        initialized.layout,
        path="requirements.md",
        role="requirements",
        title="Requirements",
        actor=actor,
        media_type="text/markdown",
    )
    claim = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Discovery outputs produced",
        actor=actor,
    )
    check = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"invocation": "manual"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
        exit_status=0,
    )
    record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Bind discovery verification",
        actor=actor,
        artifact_revision_ids=(objective.revision.id, requirements.revision.id),
        check_result_ids=(check.check.id,),
        claim_ids=(claim.claim.id,),
    )
    verify_step(initialized.layout, step_id="discover")
    record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Discovery outputs only",
        actor=actor,
    )


def test_neutral_context_is_deterministic_bounded_and_non_governing(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    actor = owner_actor(initialized.configuration.owner)
    (tmp_path / ".env").write_text("ENV_LEAK_SENTINEL", encoding="utf-8")
    secret = initialized.layout.secret_directory / "credential.txt"
    secret.write_text("LOCAL_SECRET_LEAK_SENTINEL", encoding="utf-8")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    (unrelated / "notes.txt").write_text("PROJECT_LEAK_SENTINEL", encoding="utf-8")
    archived = initialized.layout.archive_directory / "unrelated-initiative"
    archived.mkdir()
    (archived / "notes.txt").write_text("ARCHIVE_LEAK_SENTINEL", encoding="utf-8")
    (tmp_path / "requirements.md").write_text(
        "NON_SELECTED_ARTIFACT_SENTINEL", encoding="utf-8"
    )
    add_artifact(
        initialized.layout,
        path="requirements.md",
        role="requirements",
        title="Premature requirements",
        actor=actor,
        media_type="text/markdown",
    )
    decision = record_decision(
        initialized.layout,
        decision_type="scope-choice",
        question="Which boundary applies?",
        considered_options=("Bounded", "Unbounded"),
        chosen_outcome="DECISION_INCLUDED_SENTINEL",
        rationale="Preserve the approved scope",
        actor=actor,
    )
    journal_before = initialized.layout.event_journal_file.read_bytes()

    first = generate_agent_context(initialized.layout)
    first_json = first.json_path.read_bytes()
    first_markdown = first.markdown_path.read_bytes()
    second = generate_agent_context(initialized.layout)

    assert first_json == second.json_path.read_bytes()
    assert first_markdown == second.markdown_path.read_bytes()
    assert initialized.layout.event_journal_file.read_bytes() == journal_before
    assert load_agent_context(initialized.layout) == first.context
    assert first.context.relevant_decisions[0].id == decision.decision.id
    assert set(first.context.model_dump(mode="json")) == {
        "schema_version",
        "objective",
        "active_step",
        "approved_scope",
        "relevant_constraints",
        "relevant_decisions",
        "permitted_actions",
        "prohibited_actions",
        "required_outputs",
        "expected_evidence",
        "return_contract",
        "known_blockers",
    }
    combined = first_json + first_markdown
    for sentinel in (
        b"ENV_LEAK_SENTINEL",
        b"LOCAL_SECRET_LEAK_SENTINEL",
        b"PROJECT_LEAK_SENTINEL",
        b"ARCHIVE_LEAK_SENTINEL",
        b"NON_SELECTED_ARTIFACT_SENTINEL",
    ):
        assert sentinel not in combined
    assert b"DECISION_INCLUDED_SENTINEL" in combined
    assert not initialized.layout.lock_directory.joinpath("mutation.lock").exists()


def test_context_selects_only_active_step_required_input_metadata(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    _advance_to_plan(initialized)

    context = build_agent_context(initialized.layout)

    assert context.active_step.id == "plan"
    assert context.active_step.state is StepState.READY
    assert tuple(item.role for item in context.active_step.required_inputs) == ("requirements",)
    assert context.active_step.required_inputs[0].path == "requirements.md"
    rendered = context.model_dump_json()
    assert "objective.md" not in rendered
    assert "NON_SELECTED_OBJECTIVE_SENTINEL" not in rendered
    assert "SELECTED_REQUIREMENTS_SENTINEL" not in rendered


def test_context_reports_selected_input_drift_as_a_blocker(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    _advance_to_plan(initialized)
    (tmp_path / "requirements.md").write_text("Changed without revision", encoding="utf-8")

    context = build_agent_context(initialized.layout)

    assert context.permitted_actions == ()
    assert any("no longer matches" in blocker for blocker in context.known_blockers)


def test_vendor_targets_require_the_managed_preview_service(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)

    with pytest.raises(ConfigurationError, match="managed vendor preview/apply"):
        generate_agent_context(initialized.layout, target=AgentContextTarget.CODEX)
    assert not initialized.layout.agent_context_directory.exists()


def test_agent_context_cli_generates_tracked_neutral_views(tmp_path: Path) -> None:
    _initiative(tmp_path)

    result = runner.invoke(app, ["agent", "context", "-C", str(tmp_path)])

    assert result.exit_code == 0
    assert "Generated neutral canonical agent context" in result.stdout
    assert (tmp_path / ".forge" / "active" / "context" / "current.json").is_file()
    assert (tmp_path / ".forge" / "active" / "context" / "current.md").is_file()


def test_context_directory_symlink_is_rejected_when_supported(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        os.symlink(outside, initialized.layout.agent_context_directory, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")

    with pytest.raises(SecurityError, match="symbolic-link context"):
        generate_agent_context(initialized.layout)
    assert tuple(outside.iterdir()) == ()


def test_generated_context_is_preserved_and_validated_during_archival(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    actor = owner_actor(initialized.configuration.owner)
    generated = generate_agent_context(initialized.layout)
    json_bytes = generated.json_path.read_bytes()
    markdown_bytes = generated.markdown_path.read_bytes()

    result = abandon_initiative(
        initialized.layout,
        reason="End archival integration smoke",
        unfinished_work_summary="Workflow remains unfinished",
        unresolved_risks=("Objective was not delivered",),
        actor=actor,
    )
    archived = load_archive(initialized.layout, result.abandonment.initiative_id)

    assert archived.layout.current_agent_context_json_file.read_bytes() == json_bytes
    assert archived.layout.current_agent_context_markdown_file.read_bytes() == markdown_bytes
