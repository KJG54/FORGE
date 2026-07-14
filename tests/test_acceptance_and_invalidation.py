import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from forge.contracts.actors import Actor, ActorType
from forge.contracts.state import IntegrityState, StepState
from forge.contracts.verification import CheckOutcome
from forge.core.acceptance import (
    list_acceptances,
    record_acceptance,
    revoke_acceptance,
    show_acceptance,
)
from forge.core.artifacts import add_artifact, list_artifacts, revise_artifact
from forge.core.authorization import owner_actor
from forge.core.decisions import list_decisions, record_decision
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.status import inspect_status
from forge.core.verification import complete_step, record_check, record_evidence, verify_step
from forge.errors import AuthorizationError, IntegrityError
from forge.storage.repository import InitializationResult, initialize_repository


def _awaiting_acceptance(
    tmp_path: Path,
) -> tuple[InitializationResult, Actor, tuple[UUID, ...], UUID, UUID, UUID]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Deliver governed discovery outputs",
        declared_scope_summary="Discovery only",
        actor=actor,
        trust_pack_data=True,
    )
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    (tmp_path / "objective.md").write_text("Objective", encoding="utf-8")
    (tmp_path / "requirements.md").write_text("Requirements", encoding="utf-8")
    objective = add_artifact(
        initialized.layout,
        path="objective.md",
        role="objective-and-constraints",
        title="Objective",
        actor=actor,
    )
    requirements = add_artifact(
        initialized.layout,
        path="requirements.md",
        role="requirements",
        title="Requirements",
        actor=actor,
    )
    revisions = (objective.revision.id, requirements.revision.id)
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
        invocation_metadata={"invocation": "manual review"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
        exit_status=0,
    )
    evidence = record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Bind discovery verification",
        actor=actor,
        artifact_revision_ids=revisions,
        check_result_ids=(check.check.id,),
        claim_ids=(claim.claim.id,),
    )
    verify_step(initialized.layout, step_id="discover")
    return (
        initialized,
        actor,
        revisions,
        claim.claim.id,
        check.check.id,
        evidence.evidence.id,
    )


def test_owner_acceptance_binds_exact_current_support_and_survives_restart(
    tmp_path: Path,
) -> None:
    initialized, actor, revisions, _, check_id, evidence_id = _awaiting_acceptance(tmp_path)
    result = record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Discovery outputs only",
        actor=actor,
        known_limitations=("Presence check only",),
        residual_risks=("Semantic review remains owner judgment",),
    )

    assert set(result.acceptance.accepted_artifact_revision_ids) == set(revisions)
    assert result.acceptance.accepted_check_result_ids == (check_id,)
    assert result.acceptance.accepted_evidence_ids == (evidence_id,)
    assert result.transition.state.step_states["discover"] is StepState.COMPLETED
    assert result.transition.state.step_states["plan"] is StepState.READY
    restarted = load_active_initiative(initialized.layout)
    assert restarted.state == result.transition.state
    view = show_acceptance(initialized.layout, result.acceptance.id)
    assert view.revocation is None
    assert not view.stale


def test_acceptance_and_revocation_require_the_configured_owner(tmp_path: Path) -> None:
    initialized, actor, *_ = _awaiting_acceptance(tmp_path)
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        record_acceptance(
            initialized.layout,
            step_id="discover",
            accepted_scope="Discovery",
            actor=outsider,
        )
    accepted = record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Discovery",
        actor=actor,
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        revoke_acceptance(
            initialized.layout,
            acceptance_id=accepted.acceptance.id,
            reason="Owner review required",
            actor=outsider,
        )


def test_revocation_is_append_only_and_invalidates_progression(tmp_path: Path) -> None:
    initialized, actor, *_ = _awaiting_acceptance(tmp_path)
    accepted = record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Discovery",
        actor=actor,
    )
    acceptance_path = (
        initialized.layout.acceptance_directory / f"{accepted.acceptance.id}.json"
    )
    original = acceptance_path.read_bytes()
    revoked = revoke_acceptance(
        initialized.layout,
        acceptance_id=accepted.acceptance.id,
        reason="Requirements changed",
        actor=actor,
    )

    assert acceptance_path.read_bytes() == original
    active = load_active_initiative(initialized.layout)
    assert active.state.step_states["discover"] is StepState.INVALIDATED
    assert active.state.step_states["plan"] is StepState.PENDING
    assert accepted.acceptance.id in active.state.stale_record_ids
    view = show_acceptance(initialized.layout, accepted.acceptance.id)
    assert view.revocation == revoked.revocation
    assert view.stale
    assert list_acceptances(initialized.layout) == (view,)

    rework = begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    assert rework.transition.state.step_states["discover"] is StepState.IN_PROGRESS


def test_artifact_revision_stales_acceptance_and_all_dependency_records(
    tmp_path: Path,
) -> None:
    initialized, actor, revisions, claim_id, check_id, evidence_id = _awaiting_acceptance(
        tmp_path
    )
    accepted = record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Discovery",
        actor=actor,
    )
    objective = next(
        item for item in list_artifacts(initialized.layout)
        if item.current_revision.id == revisions[0]
    )
    decision = record_decision(
        initialized.layout,
        decision_type="revision-assumption",
        question="Which objective revision governs?",
        considered_options=("Current revision",),
        chosen_outcome="Current revision",
        rationale="Bind the accepted objective bytes",
        actor=actor,
        bound_digests=(objective.current_revision.content_digest,),
    )
    (tmp_path / "objective.md").write_text("Revised objective", encoding="utf-8")
    revised = revise_artifact(
        initialized.layout,
        artifact_id=objective.artifact.id,
        path="objective.md",
        actor=actor,
    )

    expected = {
        revisions[0],
        claim_id,
        check_id,
        evidence_id,
        accepted.acceptance.id,
        decision.decision.id,
    }
    assert expected.issubset(revised.revision.stale_dependency_effects)
    active = load_active_initiative(initialized.layout)
    assert active.state.step_states["discover"] is StepState.INVALIDATED
    assert active.state.step_states["plan"] is StepState.PENDING
    assert expected.issubset(active.state.stale_record_ids)
    assert decision.decision.id not in active.state.open_decision_ids


def test_decision_supersession_preserves_history_and_replaces_open_decision(
    tmp_path: Path,
) -> None:
    initialized, actor, *_ = _awaiting_acceptance(tmp_path)
    first = record_decision(
        initialized.layout,
        decision_type="scope-choice",
        question="Which boundary applies?",
        considered_options=("Narrow", "Broad"),
        chosen_outcome="Narrow",
        rationale="Minimize risk",
        actor=actor,
    )
    first_path = initialized.layout.decision_directory / f"{first.decision.id}.json"
    original = first_path.read_bytes()
    second = record_decision(
        initialized.layout,
        decision_type="scope-choice",
        question="Which revised boundary applies?",
        considered_options=("Narrow", "Medium"),
        chosen_outcome="Medium",
        rationale="New evidence supports expansion",
        actor=actor,
        supersedes=first.decision.id,
    )

    assert first_path.read_bytes() == original
    assert second.supersession is not None
    active = load_active_initiative(initialized.layout)
    assert active.state.open_decision_ids == (second.decision.id,)
    assert first.decision.id in active.state.stale_record_ids
    assert list_decisions(initialized.layout) == (first.decision, second.decision)


def test_tampered_acceptance_is_reported_as_integrity_failure(tmp_path: Path) -> None:
    initialized, actor, *_ = _awaiting_acceptance(tmp_path)
    accepted = record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Discovery",
        actor=actor,
    )
    path = initialized.layout.acceptance_directory / f"{accepted.acceptance.id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["accepted_scope"] = "Tampered scope"
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = inspect_status(initialized.layout)
    assert report.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert "Acceptance record" in report.blockers[0]
    with pytest.raises(IntegrityError):
        load_active_initiative(initialized.layout)
