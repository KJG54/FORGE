import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.decisions import WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE
from forge.core.archival import abandon_initiative, close_initiative, load_archive
from forge.core.authorization import owner_actor
from forge.core.decisions import record_decision
from forge.core.deviations import (
    list_workflow_deviations,
    open_workflow_deviations,
    record_workflow_deviation,
    show_workflow_deviation,
)
from forge.core.lifecycle import create_initiative, load_active_initiative
from forge.core.status import inspect_status
from forge.errors import AuthorizationError, ConflictError, IntegrityError
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Deliver governed work while preserving deviations",
        declared_scope_summary="Exercise explicit deviation review",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _record(initialized: InitializationResult, actor: Actor):
    return record_workflow_deviation(
        initialized.layout,
        declared_behavior="Complete the locked verification sequence",
        actual_behavior="A required verification action was omitted",
        rationale="The omission must remain visible and receive explicit review",
        review_requirement="Decide whether rework or abandonment is required",
        actor=actor,
    )


def test_deviation_is_owner_only_state_neutral_and_closure_blocking(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    before = load_active_initiative(initialized.layout).state
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        _record(initialized, outsider)
    with pytest.raises(ConflictError, match="do not describe a deviation"):
        record_workflow_deviation(
            initialized.layout,
            declared_behavior="Same behavior",
            actual_behavior="Same behavior",
            rationale="No difference exists",
            review_requirement="None",
            actor=actor,
        )

    result = _record(initialized, actor)
    after = load_active_initiative(initialized.layout).state
    assert after.step_states == before.step_states
    assert after.active_run_ids == before.active_run_ids
    assert after.open_gate_ids == before.open_gate_ids
    assert after.open_decision_ids == before.open_decision_ids
    assert show_workflow_deviation(
        initialized.layout, result.deviation.id
    ).review_open
    report = inspect_status(initialized.layout)
    assert report.open_workflow_deviation_ids == (result.deviation.id,)
    assert any(str(result.deviation.id) in blocker for blocker in report.blockers)
    assert f"deviation-review:{result.deviation.id}" in report.next_actions
    with pytest.raises(ConflictError, match="requires a current owner review decision"):
        close_initiative(
            initialized.layout,
            closing_summary="Cannot hide an unresolved deviation",
            actor=actor,
        )


def test_current_review_decision_resolves_and_supersession_can_reopen_deviation(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    deviation = _record(initialized, actor).deviation
    review = record_decision(
        initialized.layout,
        decision_type=WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE,
        question="How is the deviation resolved?",
        considered_options=("Rework", "Accept no waiver and abandon"),
        chosen_outcome="Rework before closure",
        rationale="The declared workflow remains governing",
        actor=actor,
        affected_record_ids=(deviation.id,),
        bound_digests=deviation.affected_digests,
    )
    view = show_workflow_deviation(initialized.layout, deviation.id)
    assert view.review_decision == review.decision
    assert not view.review_open
    assert not open_workflow_deviations(initialized.layout)

    with pytest.raises(ConflictError, match="already has a current review decision"):
        record_decision(
            initialized.layout,
            decision_type=WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE,
            question="Can a second current review replace it silently?",
            considered_options=("No",),
            chosen_outcome="No",
            rationale="Reviews are append-only and explicitly superseded",
            actor=actor,
            affected_record_ids=(deviation.id,),
        )

    replacement = record_decision(
        initialized.layout,
        decision_type="review-withdrawal",
        question="Does the prior deviation review remain current?",
        considered_options=("Retain", "Withdraw"),
        chosen_outcome="Withdraw",
        rationale="New facts require another explicit review",
        actor=actor,
        supersedes=review.decision.id,
    )
    assert replacement.supersession is not None
    assert open_workflow_deviations(initialized.layout)[0].deviation.id == deviation.id
    restarted = load_active_initiative(initialized.layout)
    assert review.decision.id in restarted.state.stale_record_ids


def test_cli_is_idempotent_and_restart_validation_detects_tampering(
    tmp_path: Path,
) -> None:
    initialized, _ = _initiative(tmp_path)
    arguments = [
        "deviation",
        "record",
        "--declared",
        "Run every required check",
        "--actual",
        "One check was skipped",
        "--rationale",
        "Preserve the discrepancy",
        "--review-requirement",
        "Choose rework or abandonment",
        "--idempotency-key",
        "deviation-record-1",
        "-C",
        str(tmp_path),
    ]
    first = runner.invoke(app, arguments)
    assert first.exit_code == 0, first.stdout
    deviation_id = UUID(
        next(
            line.rsplit(" ", 1)[-1]
            for line in first.stdout.splitlines()
            if line.startswith("Recorded workflow deviation ")
        )
    )
    event_count = len(
        (tmp_path / ".forge" / "active" / "events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    replay = runner.invoke(app, arguments)
    assert replay.exit_code == 0, replay.stdout
    assert "Idempotent replay" in replay.stdout
    assert len(
        (tmp_path / ".forge" / "active" / "events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ) == event_count

    review = runner.invoke(
        app,
        [
            "deviation",
            "review",
            str(deviation_id),
            "--option",
            "Rework",
            "--option",
            "Abandon",
            "--outcome",
            "Rework",
            "--rationale",
            "The locked workflow remains required",
            "--idempotency-key",
            "deviation-review-1",
            "-C",
            str(tmp_path),
        ],
    )
    assert review.exit_code == 0, review.stdout
    shown = runner.invoke(
        app,
        ["deviation", "show", str(deviation_id), "-C", str(tmp_path)],
    )
    assert shown.exit_code == 0, shown.stdout
    assert "status=reviewed by" in shown.stdout

    path = tmp_path / ".forge" / "active" / "workflow-deviations" / f"{deviation_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["actual_behavior"] = "Tampered behavior"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Workflow deviation"):
        load_active_initiative(initialized.layout)


def test_terminal_archive_preserves_deviation_and_review_history(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    deviation = _record(initialized, actor).deviation
    review = record_decision(
        initialized.layout,
        decision_type=WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE,
        question="How should terminal history treat this deviation?",
        considered_options=("Preserve",),
        chosen_outcome="Preserve",
        rationale="Abandonment must retain both facts",
        actor=actor,
        affected_record_ids=(deviation.id,),
        bound_digests=deviation.affected_digests,
    )
    abandoned = abandon_initiative(
        initialized.layout,
        reason="Owner stopped the initiative after deviation review",
        unfinished_work_summary="The workflow remains incomplete",
        unresolved_risks=("The intended outcome was not delivered",),
        actor=actor,
    )
    archived = load_archive(initialized.layout, abandoned.abandonment.initiative_id)
    archived_views = list_workflow_deviations(archived.active.layout)
    assert len(archived_views) == 1
    assert archived_views[0].deviation == deviation
    assert archived_views[0].review_decision == review.decision
