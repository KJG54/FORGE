import json
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.capabilities import SideEffectClass
from forge.contracts.runs import RunCancellationRecord, RunRecord
from forge.contracts.state import RunState, StepState
from forge.contracts.workflows import CancellationBehavior
from forge.core.archival import abandon_initiative, load_archive
from forge.core.authorization import owner_actor
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.runs import cancel_run, list_runs, show_run
from forge.errors import AuthorizationError, ConflictError, IntegrityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Exercise formal run cancellation",
        declared_scope_summary="Bind cancellation to exact immutable run facts",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def test_manual_cancellation_is_owner_authorized_exact_and_append_only(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    begun = begin_manual_run(
        initialized.layout,
        step_id="discover",
        actor=actor,
        side_effect_class=SideEffectClass.READ_ONLY,
    )
    run_path = initialized.layout.governed_run_directory / f"{begun.run.id}.json"
    original_run = run_path.read_bytes()
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )

    with pytest.raises(AuthorizationError, match="run worker or repository owner"):
        cancel_run(
            initialized.layout,
            run_id=begun.run.id,
            reason="An unrelated actor cannot end this run",
            actor=outsider,
        )

    result = cancel_run(
        initialized.layout,
        run_id=begun.run.id,
        reason="The owner intentionally stopped this attempt",
        actor=actor,
    )

    assert run_path.read_bytes() == original_run
    assert result.cancellation.run_id == begun.run.id
    assert result.cancellation.actor == actor
    assert result.cancellation.source_state is StepState.IN_PROGRESS
    assert result.cancellation.destination_state is StepState.READY
    assert (
        result.cancellation.cancellation_behavior
        is CancellationBehavior.RETURN_TO_READY
    )
    assert result.cancellation.side_effect_class is SideEffectClass.READ_ONLY
    assert result.cancellation.terminal_execution_event_id is None
    assert result.cancellation.terminal_execution_event_hash is None
    assert result.cancellation.affected_record_ids == (begun.run.id,)
    assert result.cancellation.affected_digests == (
        canonical_json_digest(begun.run.model_dump(mode="json")),
    )
    cancellation_payload = result.cancellation.model_dump(
        mode="json",
        exclude={"run_id"},
    )
    with pytest.raises(ValidationError, match="run_id"):
        RunCancellationRecord.model_validate(cancellation_payload)
    with pytest.raises(ValidationError, match="requires a run ID"):
        RunCancellationRecord.model_validate(
            {**cancellation_payload, "run_id": None}
        )
    assert result.event.affected_record_ids == (
        result.cancellation.id,
        begun.run.id,
    )
    assert result.state.step_states["discover"] is StepState.READY
    assert begun.run.id not in result.state.active_run_ids

    shown = show_run(initialized.layout, begun.run.id)
    assert shown.status is RunState.CANCELLED
    assert shown.cancellation == result.cancellation
    assert shown.cancellation_details == result.cancellation.reason
    with pytest.raises(ConflictError, match="is not active"):
        cancel_run(
            initialized.layout,
            run_id=begun.run.id,
            reason="A terminal run cannot be cancelled twice",
            actor=actor,
        )


def test_risky_cancellation_fails_closed_and_archive_preserves_record(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    begun = begin_manual_run(
        initialized.layout,
        step_id="discover",
        actor=actor,
        side_effect_class=SideEffectClass.EXTERNAL_REVERSIBLE,
    )
    result = cancel_run(
        initialized.layout,
        run_id=begun.run.id,
        reason="External effects may need owner remediation",
        actor=actor,
    )
    assert result.cancellation.destination_state is StepState.BLOCKED
    assert result.state.step_states["discover"] is StepState.BLOCKED

    abandoned = abandon_initiative(
        initialized.layout,
        reason="Stop after recording the blocked cancellation",
        unfinished_work_summary="External-effect review remains unfinished",
        unresolved_risks=("External effects may remain",),
        actor=actor,
    )
    archived = load_archive(initialized.layout, abandoned.abandonment.initiative_id)
    archived_view = show_run(archived.active.layout, begun.run.id)
    assert archived_view.cancellation == result.cancellation
    assert list_runs(archived.active.layout) == (archived_view,)


def test_adapter_run_without_terminal_execution_cannot_be_declared_cancelled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, actor = _initiative(tmp_path)
    begun = begin_manual_run(
        initialized.layout,
        step_id="discover",
        actor=actor,
    )
    unproven_adapter_run = begun.run.model_copy(
        update={"adapter_reference": "codex"}
    )

    def load_unproven_adapter_run(
        *_args: object,
        **_kwargs: object,
    ) -> RunRecord:
        return unproven_adapter_run

    monkeypatch.setattr(
        "forge.core.runs.load_record",
        load_unproven_adapter_run,
    )

    with pytest.raises(ConflictError, match="terminal execution event"):
        cancel_run(
            initialized.layout,
            run_id=begun.run.id,
            reason="Do not claim an unproven process has stopped",
            actor=actor,
        )

    active = load_active_initiative(initialized.layout)
    assert begun.run.id in active.state.active_run_ids
    assert active.state.step_states["discover"] is StepState.IN_PROGRESS
    assert not initialized.layout.run_cancellation_directory.exists()


def test_cancellation_record_write_rolls_back_before_event_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, actor = _initiative(tmp_path)
    begun = begin_manual_run(
        initialized.layout,
        step_id="discover",
        actor=actor,
    )

    def fail_append(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated pre-commit append failure")

    monkeypatch.setattr(
        "forge.core.runs.append_event_and_update_snapshot",
        fail_append,
    )
    with pytest.raises(IntegrityError, match="simulated pre-commit"):
        cancel_run(
            initialized.layout,
            run_id=begun.run.id,
            reason="Exercise cancellation rollback",
            actor=actor,
        )

    assert not initialized.layout.run_cancellation_directory.exists()
    active = load_active_initiative(initialized.layout)
    assert begun.run.id in active.state.active_run_ids


def test_cli_cancellation_receipt_recovery_and_tamper_detection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, actor = _initiative(tmp_path)
    begun = begin_manual_run(
        initialized.layout,
        step_id="discover",
        actor=actor,
    )
    arguments = [
        "run",
        "cancel",
        str(begun.run.id),
        "--reason",
        "The receipt write will be interrupted after commit",
        "--idempotency-key",
        "interrupted-formal-cancellation",
        "-C",
        str(tmp_path),
    ]

    def fail_receipt(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated receipt failure")

    with monkeypatch.context() as context:
        context.setattr("forge.storage.idempotency.write_record", fail_receipt)
        interrupted = runner.invoke(app, arguments)
    assert interrupted.exit_code == 30, interrupted.stdout
    cancellation_path = next(
        initialized.layout.run_cancellation_directory.glob("*.json")
    )
    cancellation = load_record(cancellation_path, RunCancellationRecord)

    recovered = runner.invoke(
        app,
        [
            "recover-command",
            "interrupted-formal-cancellation",
            "--reason",
            "The formal cancellation event and record are complete",
            "--idempotency-key",
            "recover-formal-cancellation",
            "-C",
            str(tmp_path),
        ],
    )
    assert recovered.exit_code == 0, recovered.stdout
    replay = runner.invoke(app, arguments)
    assert replay.exit_code == 0, replay.stdout
    assert "Idempotent replay" in replay.stdout

    shown = runner.invoke(
        app,
        ["run", "show", str(begun.run.id), "-C", str(tmp_path)],
    )
    assert shown.exit_code == 0, shown.stdout
    assert f"Cancellation record: {cancellation.id}" in shown.stdout
    assert "Cancellation destination: ready" in shown.stdout

    payload = json.loads(cancellation_path.read_text(encoding="utf-8"))
    payload["reason"] = "Tampered cancellation reason"
    cancellation_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Cancellation event"):
        load_active_initiative(initialized.layout)


def test_cancellation_event_binds_exact_record_digest(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    begun = begin_manual_run(
        initialized.layout,
        step_id="discover",
        actor=actor,
    )
    result = cancel_run(
        initialized.layout,
        run_id=begun.run.id,
        reason="Bind the formal cancellation record",
        actor=actor,
    )
    events = read_journal(initialized.layout.event_journal_file)
    event = events[-1]

    assert event.id == result.event.id
    assert event.metadata["run_cancellation_record_id"] == str(
        result.cancellation.id
    )
    assert event.affected_digests[-1] == canonical_json_digest(
        result.cancellation.model_dump(mode="json")
    )
