import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.core.archival import abandon_initiative, close_initiative, load_archive
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative, load_active_initiative
from forge.core.overrides import (
    list_emergency_overrides,
    record_emergency_override,
    show_emergency_override,
)
from forge.core.status import inspect_status
from forge.errors import (
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    IntegrityError,
)
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Exercise explicit emergency governance",
        declared_scope_summary="Emergency override declaration only",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _record(initialized: InitializationResult, actor: Actor):
    return record_emergency_override(
        initialized.layout,
        requirement_id="declared-checks",
        gate_id=None,
        rationale="An external emergency requires a documented exception",
        residual_risk="The affected check still has no current passing result",
        permanence="temporary",
        review_requirement="Reassess after the emergency condition ends",
        actor=actor,
    )


def test_override_is_owner_only_target_validated_and_state_neutral(
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
    with pytest.raises(ConfigurationError, match="exactly one"):
        record_emergency_override(
            initialized.layout,
            requirement_id=None,
            gate_id=None,
            rationale="Missing target",
            residual_risk="Unknown",
            permanence="temporary",
            review_requirement="Review",
            actor=actor,
        )
    with pytest.raises(ConfigurationError, match="exactly one"):
        record_emergency_override(
            initialized.layout,
            requirement_id="declared-checks",
            gate_id="release",
            rationale="Ambiguous target",
            residual_risk="Unknown",
            permanence="temporary",
            review_requirement="Review",
            actor=actor,
        )
    with pytest.raises(ConflictError, match="Unknown locked-workflow requirement"):
        record_emergency_override(
            initialized.layout,
            requirement_id="invented-requirement",
            gate_id=None,
            rationale="Invalid target",
            residual_risk="Unknown",
            permanence="temporary",
            review_requirement="Review",
            actor=actor,
        )
    with pytest.raises(ConflictError, match="Unknown locked-workflow gate"):
        record_emergency_override(
            initialized.layout,
            requirement_id=None,
            gate_id="invented-gate",
            rationale="Invalid gate",
            residual_risk="Unknown",
            permanence="temporary",
            review_requirement="Review",
            actor=actor,
        )
    with pytest.raises(ConfigurationError, match=r"temporary.*permanent"):
        record_emergency_override(
            initialized.layout,
            requirement_id="declared-checks",
            gate_id=None,
            rationale="Invalid permanence",
            residual_risk="Unknown",
            permanence="forever",
            review_requirement="Review",
            actor=actor,
        )

    result = _record(initialized, actor)
    after = load_active_initiative(initialized.layout).state
    assert result.override.affected_requirement_or_gate == "requirement:declared-checks"
    assert after.step_states == before.step_states
    assert after.active_run_ids == before.active_run_ids
    assert after.open_gate_ids == before.open_gate_ids
    assert after.open_decision_ids == before.open_decision_ids
    assert after.stale_record_ids == before.stale_record_ids
    assert show_emergency_override(initialized.layout, result.override.id) == result.override


def test_override_is_visible_and_blocks_successful_closure_without_fabricating_support(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    result = _record(initialized, actor)
    report = inspect_status(initialized.layout)
    assert report.emergency_override_ids == (result.override.id,)
    assert any(str(result.override.id) in blocker for blocker in report.blockers)
    assert f"risk-accept:{result.override.id}" in report.next_actions
    active = load_active_initiative(initialized.layout)
    assert not active.state.stale_record_ids
    assert not active.state.active_run_ids
    with pytest.raises(ConflictError, match="explicit risk acceptance"):
        close_initiative(
            initialized.layout,
            closing_summary="An override cannot silently authorize closure",
            actor=actor,
        )


def test_cli_is_idempotent_and_restart_validation_detects_tampering(
    tmp_path: Path,
) -> None:
    initialized, _ = _initiative(tmp_path)
    arguments = [
        "override",
        "record",
        "--requirement",
        "declared-checks",
        "--rationale",
        "Document emergency exception",
        "--residual-risk",
        "No passing check exists",
        "--permanence",
        "permanent",
        "--review-requirement",
        "Require explicit risk acceptance",
        "--idempotency-key",
        "override-record-1",
        "-C",
        str(tmp_path),
    ]
    first = runner.invoke(app, arguments)
    assert first.exit_code == 0, first.stdout
    override_id = UUID(
        next(
            line.rsplit(" ", 1)[-1]
            for line in first.stdout.splitlines()
            if line.startswith("Recorded emergency override ")
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
    shown = runner.invoke(
        app,
        ["override", "show", str(override_id), "-C", str(tmp_path)],
    )
    assert shown.exit_code == 0, shown.stdout
    assert "target=requirement:declared-checks permanence=permanent" in shown.stdout
    assert "Progression authority: none" in shown.stdout

    path = tmp_path / ".forge" / "active" / "emergency-overrides" / f"{override_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["residual_risk"] = "Tampered residual risk"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Emergency override"):
        load_active_initiative(initialized.layout)


def test_abandonment_archive_preserves_unresolved_override_history(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _record(initialized, actor).override
    abandoned = abandon_initiative(
        initialized.layout,
        reason="Owner stopped rather than bypassing governed completion",
        unfinished_work_summary="The workflow remains incomplete",
        unresolved_risks=(override.residual_risk,),
        actor=actor,
    )
    archived = load_archive(initialized.layout, abandoned.abandonment.initiative_id)
    assert list_emergency_overrides(archived.active.layout) == (override,)
