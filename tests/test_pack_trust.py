import json
from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.packs import PackTrustDecision, PackTrustState
from forge.contracts.state import InitiativeLifecycleState
from forge.core.archival import abandon_initiative, load_archive
from forge.core.authorization import owner_actor
from forge.core.continuity import pause_initiative
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.pack_trust import change_pack_trust, pack_trust_history
from forge.core.runs import cancel_run, list_runs
from forge.core.status import inspect_status
from forge.errors import AuthorizationError, ConflictError, IntegrityError
from forge.storage.journal import read_journal
from forge.storage.records import load_record
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _new_initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Exercise the pack data-trust lifecycle",
        declared_scope_summary="One exact locked declarative pack",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _change(
    initialized: InitializationResult,
    actor: Actor,
    state: PackTrustState,
    rationale: str,
):
    return change_pack_trust(
        initialized.layout,
        pack_id="software-basic",
        trust_state=state,
        rationale=rationale,
        actor=actor,
    )


def test_owner_untrust_blocks_workflow_and_retrust_restores_it(tmp_path: Path) -> None:
    initialized, actor = _new_initiative(tmp_path)
    initial_bytes = initialized.layout.pack_trust_file.read_bytes()
    initial = load_record(initialized.layout.pack_trust_file, PackTrustDecision)

    withdrawn = _change(
        initialized,
        actor,
        PackTrustState.UNTRUSTED,
        "Owner is re-evaluating the locked workflow data",
    )

    assert initialized.layout.pack_trust_file.read_bytes() == initial_bytes
    assert withdrawn.event.event_type == "pack-trust-changed"
    assert withdrawn.decision.affected_record_ids == (initial.id,)
    with pytest.raises(ConflictError, match="is untrusted"):
        load_active_initiative(initialized.layout)
    with pytest.raises(ConflictError, match="is untrusted"):
        begin_manual_run(initialized.layout, step_id="discover", actor=actor)

    report = inspect_status(initialized.layout)
    assert report.pack_trust_state is PackTrustState.UNTRUSTED
    assert report.next_actions == ("pack-trust:software-basic", "abandon")
    assert "workflow-dependent mutation is disabled" in report.blockers[0]
    untrusted = load_active_initiative(
        initialized.layout,
        allow_untrusted_pack=True,
    )
    assert untrusted.pack_trust == withdrawn.decision
    assert pack_trust_history(
        initialized.layout,
        initial,
        read_journal(initialized.layout.event_journal_file),
    ) == (initial, withdrawn.decision)

    with pytest.raises(ConflictError, match="already untrusted"):
        _change(initialized, actor, PackTrustState.UNTRUSTED, "Duplicate withdrawal")

    restored = _change(
        initialized,
        actor,
        PackTrustState.TRUSTED_DATA,
        "Owner revalidated the exact locked digest",
    )
    restarted = load_active_initiative(initialized.layout)
    assert restarted.pack_trust == restored.decision
    assert begin_manual_run(
        initialized.layout,
        step_id="discover",
        actor=actor,
    ).run.step_id == "discover"


def test_pack_trust_change_is_owner_only_and_exact_pack_scoped(tmp_path: Path) -> None:
    initialized, _ = _new_initiative(tmp_path)
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        _change(
            initialized,
            outsider,
            PackTrustState.UNTRUSTED,
            "Contributor cannot withdraw owner trust",
        )
    with pytest.raises(ConflictError, match="locks 'software-basic'"):
        change_pack_trust(
            initialized.layout,
            pack_id="another-pack",
            trust_state=PackTrustState.UNTRUSTED,
            rationale="Wrong pack",
            actor=owner_actor(initialized.configuration.owner),
        )


def test_cli_previews_exact_data_only_boundary_and_records_history(tmp_path: Path) -> None:
    initialized, _ = _new_initiative(tmp_path)
    event_count = len(read_journal(initialized.layout.event_journal_file))
    arguments = [
        "pack",
        "untrust",
        "software-basic",
        "--rationale",
        "Review the locked data again",
        "-C",
        str(tmp_path),
    ]

    preview = runner.invoke(app, arguments)

    assert preview.exit_code == 0, preview.stderr
    assert "Locked pack: software-basic@0.3.0" in preview.stdout
    assert "Trust boundary: validated declarative data only; never executable authority" in (
        preview.stdout
    )
    assert "Preview only" in preview.stdout
    assert len(read_journal(initialized.layout.event_journal_file)) == event_count
    assert not initialized.layout.pack_trust_decision_directory.exists()

    applied = runner.invoke(app, [*arguments, "--apply"])
    assert applied.exit_code == 0, applied.stderr
    assert "Idempotency key:" in applied.stdout
    assert "Pack trust decision recorded:" in applied.stdout

    inspected = runner.invoke(
        app,
        ["pack", "inspect", "software-basic", "-C", str(tmp_path)],
    )
    assert inspected.exit_code == 0, inspected.stderr
    assert "Current data trust: untrusted" in inspected.stdout
    assert "Trust history:" in inspected.stdout
    assert "trusted-data" in inspected.stdout
    assert "untrusted" in inspected.stdout

    status = runner.invoke(app, ["status", "-C", str(tmp_path)])
    assert status.exit_code == 0, status.stderr
    assert "Pack data trust: untrusted" in status.stdout
    assert "Next: pack-trust:software-basic" in status.stdout


def test_pack_trust_history_is_tamper_evident(tmp_path: Path) -> None:
    initialized, actor = _new_initiative(tmp_path)
    result = _change(
        initialized,
        actor,
        PackTrustState.UNTRUSTED,
        "Record an immutable withdrawal",
    )
    path = initialized.layout.pack_trust_decision_directory / f"{result.decision.id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rationale"] = "Tampered rationale"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(IntegrityError, match="does not match event"):
        load_active_initiative(initialized.layout, allow_untrusted_pack=True)


def test_active_run_remains_visible_and_cancellable_after_untrust(tmp_path: Path) -> None:
    initialized, actor = _new_initiative(tmp_path)
    started = begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    _change(
        initialized,
        actor,
        PackTrustState.UNTRUSTED,
        "Stop new workflow use while retaining run governance",
    )

    assert list_runs(initialized.layout)[0].record.id == started.run.id
    report = inspect_status(initialized.layout)
    assert report.next_actions == (
        "pack-trust:software-basic",
        f"run-cancel:{started.run.id}",
    )
    cancelled = cancel_run(
        initialized.layout,
        run_id=started.run.id,
        reason="Pack data trust was withdrawn",
        actor=actor,
    )
    assert cancelled.run.record.id == started.run.id
    assert inspect_status(initialized.layout).next_actions == (
        "pack-trust:software-basic",
        "abandon",
    )


def test_untrusted_or_paused_initiative_can_be_retrusted_or_abandoned(
    tmp_path: Path,
) -> None:
    initialized, actor = _new_initiative(tmp_path)
    pause_initiative(
        initialized.layout,
        actor=actor,
        reason="Pause while reassessing pack data",
    )
    _change(initialized, actor, PackTrustState.UNTRUSTED, "Pause trust during review")
    restored = _change(
        initialized,
        actor,
        PackTrustState.TRUSTED_DATA,
        "The exact locked data was reviewed",
    )
    assert restored.decision.trust_state is PackTrustState.TRUSTED_DATA

    _change(initialized, actor, PackTrustState.UNTRUSTED, "Stop using this pack")
    abandoned = abandon_initiative(
        initialized.layout,
        reason="Owner no longer trusts the workflow data",
        unfinished_work_summary="No workflow steps were completed",
        unresolved_risks=("The objective remains undelivered",),
        actor=actor,
    )
    archive = load_archive(initialized.layout, abandoned.abandonment.initiative_id)
    assert archive.active.state.lifecycle_state is InitiativeLifecycleState.ABANDONED
    assert archive.active.pack_trust.trust_state is PackTrustState.UNTRUSTED


def test_interrupted_untrust_receipt_is_recoverable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, _ = _new_initiative(tmp_path)
    arguments = [
        "pack",
        "untrust",
        "software-basic",
        "--rationale",
        "Review after a receipt interruption",
        "--apply",
        "--idempotency-key",
        "interrupted-untrust",
        "-C",
        str(tmp_path),
    ]

    def fail_receipt(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated receipt failure")

    with monkeypatch.context() as context:
        context.setattr("forge.storage.idempotency.write_record", fail_receipt)
        interrupted = runner.invoke(app, arguments)
    assert interrupted.exit_code == 30
    assert load_active_initiative(
        initialized.layout,
        allow_untrusted_pack=True,
    ).pack_trust.trust_state is PackTrustState.UNTRUSTED

    recovered = runner.invoke(
        app,
        [
            "recover-command",
            "interrupted-untrust",
            "--reason",
            "Trust event committed before its receipt",
            "--idempotency-key",
            "recover-untrust",
            "-C",
            str(tmp_path),
        ],
    )
    assert recovered.exit_code == 0, recovered.stderr
    assert "Recovered event(s): 1" in recovered.stdout

    replayed = runner.invoke(app, arguments)
    assert replayed.exit_code == 0, replayed.stderr
    assert "Idempotent replay" in replayed.stdout
