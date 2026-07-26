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
from forge.core.overrides import record_emergency_override
from forge.core.risk_acceptances import (
    list_risk_acceptances,
    record_risk_acceptance,
    revoke_risk_acceptance,
    show_risk_acceptance,
)
from forge.core.scope_amendments import amend_scope
from forge.core.status import inspect_status
from forge.errors import AuthorizationError, ConflictError, IntegrityError
from forge.storage.objects import canonical_json_digest
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Exercise exact residual-risk governance",
        declared_scope_summary="Risk acceptance without workflow waiver",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _override(initialized: InitializationResult, actor: Actor):
    return record_emergency_override(
        initialized.layout,
        requirement_id="declared-checks",
        gate_id=None,
        rationale="An emergency requires a documented exception",
        residual_risk="The declared checks remain incomplete",
        permanence="temporary",
        review_requirement="Review after the emergency condition ends",
        actor=actor,
    ).override


def _accept(initialized: InitializationResult, actor: Actor, override_id: UUID):
    return record_risk_acceptance(
        initialized.layout,
        override_id=override_id,
        rationale="The owner accepts this exact bounded residual risk",
        residual_impact="Closure may retain the documented incomplete-check exposure",
        review_condition="Review if the governing requirement changes",
        actor=actor,
    )


def test_risk_acceptance_is_owner_only_exact_bound_and_state_neutral(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    before = load_active_initiative(initialized.layout).state
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        _accept(initialized, outsider, override.id)
    with pytest.raises(ConflictError, match="Unknown emergency override"):
        _accept(initialized, actor, uuid4())

    result = _accept(initialized, actor, override.id)
    after = load_active_initiative(initialized.layout).state
    assert result.acceptance.risk == override.residual_risk
    assert result.acceptance.affected_record_ids == (override.id,)
    assert result.acceptance.affected_digests[0] == canonical_json_digest(
        override.model_dump(mode="json")
    )
    assert after.step_states == before.step_states
    assert after.active_run_ids == before.active_run_ids
    assert after.open_gate_ids == before.open_gate_ids
    assert after.open_decision_ids == before.open_decision_ids
    assert after.stale_record_ids == before.stale_record_ids
    assert show_risk_acceptance(
        initialized.layout, result.acceptance.id
    ).acceptance == result.acceptance
    with pytest.raises(ConflictError, match="already has a current"):
        _accept(initialized, actor, override.id)


def test_acceptance_resolves_only_exact_override_closure_blocker(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    before = inspect_status(initialized.layout)
    assert f"risk-accept:{override.id}" in before.next_actions
    assert any(str(override.id) in blocker for blocker in before.blockers)

    acceptance = _accept(initialized, actor, override.id).acceptance
    after = inspect_status(initialized.layout)
    assert after.risk_acceptance_ids == (acceptance.id,)
    assert f"risk-accept:{override.id}" not in after.next_actions
    assert not any(str(override.id) in blocker for blocker in after.blockers)
    with pytest.raises(ConflictError, match="every workflow step"):
        close_initiative(
            initialized.layout,
            closing_summary="Risk acceptance cannot fabricate workflow completion",
            actor=actor,
        )


def test_scope_change_stales_override_and_acceptance_together(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    acceptance = _accept(initialized, actor, override.id).acceptance

    amend_scope(
        initialized.layout,
        changed_scope="The declared-checks requirement now has changed governing meaning",
        rationale="Changed requirements must invalidate prior exception review",
        affected_requirements=("declared-checks",),
        affected_artifact_ids=(),
        workflow_return_step_id="discover",
        actor=actor,
    )

    active = load_active_initiative(initialized.layout)
    assert {override.id, acceptance.id}.issubset(active.state.stale_record_ids)
    view = show_risk_acceptance(initialized.layout, acceptance.id)
    assert view.stale
    report = inspect_status(initialized.layout)
    assert f"risk-accept:{override.id}" not in report.next_actions
    with pytest.raises(ConflictError, match="is stale"):
        _accept(initialized, actor, override.id)


def test_cli_idempotency_show_and_restart_tamper_detection(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    arguments = [
        "risk",
        "accept",
        str(override.id),
        "--rationale",
        "Accept exact override risk",
        "--residual-impact",
        "Documented incomplete-check exposure remains",
        "--review-condition",
        "Review on scope change",
        "--idempotency-key",
        "risk-accept-1",
        "-C",
        str(tmp_path),
    ]
    first = runner.invoke(app, arguments)
    assert first.exit_code == 0, first.stdout
    acceptance_id = UUID(
        next(
            line.rsplit(" ", 1)[-1]
            for line in first.stdout.splitlines()
            if line.startswith("Recorded risk acceptance ")
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
        ["risk", "show", str(acceptance_id), "-C", str(tmp_path)],
    )
    assert shown.exit_code == 0, shown.stdout
    assert f"override={override.id} status=current" in shown.stdout
    assert "Progression authority: none" in shown.stdout

    path = (
        tmp_path
        / ".forge"
        / "active"
        / "risk-acceptances"
        / f"{acceptance_id}.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["risk"] = "Tampered risk"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Risk acceptance"):
        load_active_initiative(initialized.layout)


def test_abandonment_archive_preserves_override_and_acceptance_history(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    acceptance = _accept(initialized, actor, override.id).acceptance
    abandoned = abandon_initiative(
        initialized.layout,
        reason="Owner stopped with explicitly accepted residual risk",
        unfinished_work_summary="The workflow remains incomplete",
        unresolved_risks=(override.residual_risk,),
        actor=actor,
    )
    archived = load_archive(initialized.layout, abandoned.abandonment.initiative_id)
    views = list_risk_acceptances(archived.active.layout)
    assert tuple(item.acceptance for item in views) == (acceptance,)


def test_risk_acceptance_revocation_is_owner_only_append_only_and_state_neutral(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    acceptance = _accept(initialized, actor, override.id).acceptance
    acceptance_path = (
        initialized.layout.risk_acceptance_directory / f"{acceptance.id}.json"
    )
    original = acceptance_path.read_bytes()
    before = load_active_initiative(initialized.layout).state
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        revoke_risk_acceptance(
            initialized.layout,
            acceptance_id=acceptance.id,
            reason="Contributor cannot withdraw owner authority",
            actor=outsider,
        )

    result = revoke_risk_acceptance(
        initialized.layout,
        acceptance_id=acceptance.id,
        reason="The owner no longer accepts this residual risk",
        actor=actor,
    )
    after = load_active_initiative(initialized.layout).state
    assert acceptance_path.read_bytes() == original
    assert result.revocation.approval_id == acceptance.id
    assert result.revocation.affected_record_ids == (acceptance.id, override.id)
    assert result.revocation.affected_digests[0] == canonical_json_digest(
        acceptance.model_dump(mode="json")
    )
    assert after.step_states == before.step_states
    assert after.active_run_ids == before.active_run_ids
    assert after.open_gate_ids == before.open_gate_ids
    assert after.open_decision_ids == before.open_decision_ids
    assert after.stale_record_ids == before.stale_record_ids
    assert show_risk_acceptance(
        initialized.layout, acceptance.id
    ).revocation == result.revocation
    with pytest.raises(ConflictError, match="already revoked"):
        revoke_risk_acceptance(
            initialized.layout,
            acceptance_id=acceptance.id,
            reason="Duplicate revocation",
            actor=actor,
        )


def test_revocation_reopens_only_override_blocker_and_allows_fresh_acceptance(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    acceptance = _accept(initialized, actor, override.id).acceptance
    revoke_risk_acceptance(
        initialized.layout,
        acceptance_id=acceptance.id,
        reason="Reconsider the unresolved exposure",
        actor=actor,
    )

    reopened = inspect_status(initialized.layout)
    assert f"risk-accept:{override.id}" in reopened.next_actions
    assert any(str(override.id) in blocker for blocker in reopened.blockers)
    with pytest.raises(ConflictError, match="explicit risk acceptance"):
        close_initiative(
            initialized.layout,
            closing_summary="Revoked authority cannot support closure",
            actor=actor,
        )

    replacement = _accept(initialized, actor, override.id).acceptance
    resolved = inspect_status(initialized.layout)
    assert replacement.id != acceptance.id
    assert f"risk-accept:{override.id}" not in resolved.next_actions
    assert not any(str(override.id) in blocker for blocker in resolved.blockers)


def test_scope_stale_risk_acceptance_cannot_be_revoked(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    acceptance = _accept(initialized, actor, override.id).acceptance
    amend_scope(
        initialized.layout,
        changed_scope="The declared-checks requirement has changed",
        rationale="Prior exception authority no longer governs",
        affected_requirements=("declared-checks",),
        affected_artifact_ids=(),
        workflow_return_step_id="discover",
        actor=actor,
    )

    with pytest.raises(ConflictError, match="is stale"):
        revoke_risk_acceptance(
            initialized.layout,
            acceptance_id=acceptance.id,
            reason="Stale authority already resolves nothing",
            actor=actor,
        )


def test_risk_revocation_cli_is_idempotent_and_restart_detects_tampering(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    acceptance = _accept(initialized, actor, override.id).acceptance
    arguments = [
        "risk",
        "revoke",
        str(acceptance.id),
        "--reason",
        "Owner withdrew exact residual-risk acceptance",
        "--idempotency-key",
        "risk-revoke-1",
        "-C",
        str(tmp_path),
    ]
    first = runner.invoke(app, arguments)
    assert first.exit_code == 0, first.stdout
    revocation_id = UUID(
        next(
            line.rsplit(" ", 1)[-1]
            for line in first.stdout.splitlines()
            if line.startswith("Recorded risk-acceptance revocation ")
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
        ["risk", "show", str(acceptance.id), "-C", str(tmp_path)],
    )
    assert shown.exit_code == 0, shown.stdout
    assert f"status=revoked by {revocation_id}" in shown.stdout

    path = (
        tmp_path / ".forge" / "active" / "revocations" / f"{revocation_id}.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["reason"] = "Tampered revocation reason"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Risk-acceptance revocation"):
        load_active_initiative(initialized.layout)


def test_abandonment_archive_preserves_risk_revocation_history(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    override = _override(initialized, actor)
    acceptance = _accept(initialized, actor, override.id).acceptance
    revocation = revoke_risk_acceptance(
        initialized.layout,
        acceptance_id=acceptance.id,
        reason="Owner withdrew closure authority",
        actor=actor,
    ).revocation
    abandoned = abandon_initiative(
        initialized.layout,
        reason="Owner stopped after revoking risk acceptance",
        unfinished_work_summary="The workflow and override risk remain unresolved",
        unresolved_risks=(override.residual_risk,),
        actor=actor,
    )
    archived = load_archive(initialized.layout, abandoned.abandonment.initiative_id)
    view = show_risk_acceptance(archived.active.layout, acceptance.id)
    assert view.revocation == revocation
