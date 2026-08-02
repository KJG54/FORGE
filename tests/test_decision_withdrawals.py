import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.decisions import (
    DECISION_WITHDRAWAL_DECISION_TYPE,
    WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE,
)
from forge.core.archival import abandon_initiative, load_archive
from forge.core.authorization import owner_actor
from forge.core.decisions import (
    list_decision_views,
    record_decision,
    show_decision,
    withdraw_decision,
)
from forge.core.deviations import (
    open_workflow_deviations,
    record_workflow_deviation,
)
from forge.core.lifecycle import create_initiative, load_active_initiative
from forge.errors import AuthorizationError, ConfigurationError, ConflictError, IntegrityError
from forge.storage.objects import canonical_json_digest
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Exercise append-only decision withdrawal",
        declared_scope_summary="Preserve history while removing decision authority",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _decision(initialized: InitializationResult, actor: Actor):
    initiative_id = load_active_initiative(initialized.layout).initiative.id
    return record_decision(
        initialized.layout,
        decision_type="delivery-boundary",
        question="Which delivery boundary governs?",
        considered_options=("Narrow", "Broad"),
        chosen_outcome="Narrow",
        rationale="Limit the initial risk surface",
        actor=actor,
        affected_record_ids=(initiative_id,),
    )


def test_withdrawal_is_owner_only_append_only_and_state_neutral(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    recorded = _decision(initialized, actor)
    decision_path = initialized.layout.decision_directory / f"{recorded.decision.id}.json"
    original_bytes = decision_path.read_bytes()
    before = load_active_initiative(initialized.layout).state
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )

    with pytest.raises(AuthorizationError, match="Only configured owner"):
        withdraw_decision(
            initialized.layout,
            decision_id=recorded.decision.id,
            reason="A contributor cannot withdraw owner authority",
            actor=outsider,
        )

    withdrawn = withdraw_decision(
        initialized.layout,
        decision_id=recorded.decision.id,
        reason="The boundary is no longer supported by current facts",
        actor=actor,
    )
    after = load_active_initiative(initialized.layout).state

    assert decision_path.read_bytes() == original_bytes
    assert withdrawn.supersession is not None
    assert withdrawn.decision.decision_type == DECISION_WITHDRAWAL_DECISION_TYPE
    assert withdrawn.decision.affected_record_ids == (
        recorded.decision.id,
        load_active_initiative(initialized.layout).initiative.id,
    )
    assert withdrawn.decision.bound_digests[0] == canonical_json_digest(
        recorded.decision.model_dump(mode="json")
    )
    assert recorded.decision.id in after.stale_record_ids
    assert recorded.decision.id not in after.open_decision_ids
    assert withdrawn.decision.id in after.open_decision_ids
    assert after.step_states == before.step_states
    assert after.active_run_ids == before.active_run_ids
    assert after.open_gate_ids == before.open_gate_ids

    history = list_decision_views(initialized.layout)
    assert [item.status for item in history] == ["withdrawn", "current"]
    assert history[0].replacement_decision == withdrawn.decision
    assert show_decision(initialized.layout, recorded.decision.id) == history[0]


def test_withdrawal_rejects_noncurrent_targets_and_reserved_forgery(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    recorded = _decision(initialized, actor)
    with pytest.raises(ConfigurationError, match="must exactly bind"):
        record_decision(
            initialized.layout,
            decision_type=DECISION_WITHDRAWAL_DECISION_TYPE,
            question="Can arbitrary text masquerade as a withdrawal?",
            considered_options=("Yes", "No"),
            chosen_outcome="Yes",
            rationale="Attempt reserved-type forgery",
            actor=actor,
            supersedes=recorded.decision.id,
        )
    withdrawn = withdraw_decision(
        initialized.layout,
        decision_id=recorded.decision.id,
        reason="Replace unsupported authority with a withdrawal fact",
        actor=actor,
    )

    with pytest.raises(ConflictError, match="not current for withdrawal"):
        withdraw_decision(
            initialized.layout,
            decision_id=recorded.decision.id,
            reason="A second withdrawal must not rewrite history",
            actor=actor,
        )
    with pytest.raises(ConflictError, match="cannot itself be withdrawn"):
        withdraw_decision(
            initialized.layout,
            decision_id=withdrawn.decision.id,
            reason="Withdrawal records cannot be recursively withdrawn",
            actor=actor,
        )


def test_withdrawing_deviation_review_reopens_its_blocker(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    deviation = record_workflow_deviation(
        initialized.layout,
        declared_behavior="Run every declared verification action",
        actual_behavior="One verification action was omitted",
        rationale="The discrepancy must remain visible",
        review_requirement="Choose rework or abandonment",
        actor=actor,
    ).deviation
    review = record_decision(
        initialized.layout,
        decision_type=WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE,
        question="How is the deviation resolved?",
        considered_options=("Rework", "Abandon"),
        chosen_outcome="Rework",
        rationale="The declared workflow remains governing",
        actor=actor,
        affected_record_ids=(deviation.id,),
        bound_digests=deviation.affected_digests,
    )
    assert not open_workflow_deviations(initialized.layout)

    withdraw_decision(
        initialized.layout,
        decision_id=review.decision.id,
        reason="New evidence requires a fresh review",
        actor=actor,
    )

    assert open_workflow_deviations(initialized.layout)[0].deviation.id == deviation.id


def test_cli_withdrawal_is_idempotent_inspectable_and_tamper_evident(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    recorded = _decision(initialized, actor)
    arguments = [
        "decision",
        "withdraw",
        str(recorded.decision.id),
        "--reason",
        "The governing assumption no longer applies",
        "--idempotency-key",
        "decision-withdraw-1",
        "-C",
        str(tmp_path),
    ]

    first = runner.invoke(app, arguments)
    assert first.exit_code == 0, first.stdout
    withdrawal_id = UUID(
        first.stdout.split("decision_id=", 1)[1].split(";", 1)[0]
    )
    event_count = len(
        initialized.layout.event_journal_file.read_text(encoding="utf-8").splitlines()
    )
    replay = runner.invoke(app, arguments)
    assert replay.exit_code == 0, replay.stdout
    assert "Idempotent replay" in replay.stdout
    assert (
        len(initialized.layout.event_journal_file.read_text(encoding="utf-8").splitlines())
        == event_count
    )

    shown = runner.invoke(
        app,
        ["decision", "show", str(recorded.decision.id), "-C", str(tmp_path)],
    )
    assert shown.exit_code == 0, shown.stdout
    assert "status=withdrawn" in shown.stdout
    assert str(withdrawal_id) in shown.stdout

    path = initialized.layout.decision_directory / f"{withdrawal_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["chosen_outcome"] = "retain prior decision"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Decision record"):
        load_active_initiative(initialized.layout)


def test_interrupted_withdrawal_receipt_has_conservative_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, actor = _initiative(tmp_path)
    recorded = _decision(initialized, actor)
    arguments = [
        "decision",
        "withdraw",
        str(recorded.decision.id),
        "--reason",
        "The receipt write will be interrupted after commit",
        "--idempotency-key",
        "interrupted-decision-withdraw",
        "-C",
        str(tmp_path),
    ]

    def fail_receipt(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated receipt failure")

    with monkeypatch.context() as context:
        context.setattr("forge.storage.idempotency.write_record", fail_receipt)
        interrupted = runner.invoke(app, arguments)
    assert interrupted.exit_code == 30, interrupted.stdout

    recovered = runner.invoke(
        app,
        [
            "recover-command",
            "interrupted-decision-withdraw",
            "--reason",
            "The complete supersession event committed before its receipt",
            "--idempotency-key",
            "recover-decision-withdraw",
            "-C",
            str(tmp_path),
        ],
    )
    assert recovered.exit_code == 0, recovered.stdout
    assert "Completed command receipt recovery" in recovered.stdout

    replay = runner.invoke(app, arguments)
    assert replay.exit_code == 0, replay.stdout
    assert "Idempotent replay" in replay.stdout


def test_terminal_archive_preserves_withdrawal_history(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    recorded = _decision(initialized, actor)
    withdrawn = withdraw_decision(
        initialized.layout,
        decision_id=recorded.decision.id,
        reason="The decision must remain historically visible without authority",
        actor=actor,
    )
    abandoned = abandon_initiative(
        initialized.layout,
        reason="Owner stopped this decision-withdrawal exercise",
        unfinished_work_summary="The workflow was intentionally not completed",
        unresolved_risks=("The objective was not delivered",),
        actor=actor,
    )
    archived = load_archive(initialized.layout, abandoned.abandonment.initiative_id)

    history = list_decision_views(archived.active.layout)
    assert [item.decision.id for item in history] == [
        recorded.decision.id,
        withdrawn.decision.id,
    ]
    assert [item.status for item in history] == ["withdrawn", "current"]
