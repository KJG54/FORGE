import json
from pathlib import Path
from uuid import UUID

import pytest

from forge.contracts.actors import Actor
from forge.contracts.state import IntegrityState, StepState
from forge.contracts.verification import CheckOutcome
from forge.core.artifacts import (
    add_artifact,
    list_artifacts,
    revise_artifact,
    show_artifact,
)
from forge.core.authorization import owner_actor
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.status import inspect_status
from forge.core.verification import (
    complete_step,
    dependency_references,
    list_checks,
    list_claims,
    list_evidence,
    record_check,
    record_evidence,
    verify_step,
)
from forge.errors import ConflictError, SecurityError
from forge.storage.repository import InitializationResult, initialize_repository


def _started(tmp_path: Path) -> tuple[InitializationResult, Actor]:
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
    return initialized, actor


def _register_discovery_outputs(
    initialized: InitializationResult,
    actor: Actor,
) -> tuple[UUID, UUID]:
    objective = initialized.layout.root / "objective.md"
    requirements = initialized.layout.root / "requirements.md"
    objective.write_text("# Objective\nBounded work.\n", encoding="utf-8")
    requirements.write_text("# Requirements\n- Preserve evidence.\n", encoding="utf-8")
    first = add_artifact(
        initialized.layout,
        path="objective.md",
        role="objective-and-constraints",
        title="Objective and constraints",
        actor=actor,
        media_type="text/markdown",
    )
    second = add_artifact(
        initialized.layout,
        path="requirements.md",
        role="requirements",
        title="Requirements",
        actor=actor,
        media_type="text/markdown",
    )
    return first.revision.id, second.revision.id


def test_artifact_revisions_preserve_exact_bytes_and_restart(tmp_path: Path) -> None:
    initialized, actor = _started(tmp_path)
    first_revision_id, _ = _register_discovery_outputs(initialized, actor)

    views = list_artifacts(initialized.layout)
    assert len(views) == 2
    objective = next(view for view in views if view.artifact.role == "objective-and-constraints")
    assert objective.current_revision.id == first_revision_id
    assert objective.current_revision.preservation_status == "preserved"
    preserved_path = objective.current_revision.preserved_object_path
    assert preserved_path is not None
    object_path = initialized.layout.root / preserved_path
    assert object_path.read_bytes() == (tmp_path / "objective.md").read_bytes()
    original_bytes = object_path.read_bytes()
    assert objective.working_copy_matches

    (tmp_path / "objective.md").write_text("# Objective\nRevised scope.\n", encoding="utf-8")
    revised = revise_artifact(
        initialized.layout,
        artifact_id=objective.artifact.id,
        path="objective.md",
        actor=actor,
    )

    restarted = load_active_initiative(initialized.layout)
    assert restarted.state.current_artifact_revisions[objective.artifact.id] == 2
    history = show_artifact(initialized.layout, objective.artifact.id)
    assert [revision.revision_number for revision in history.revisions] == [1, 2]
    assert object_path.read_bytes() == original_bytes
    assert revised.revision.stale_dependency_effects == ()
    assert restarted.state.stale_record_ids == ()


def test_complete_requires_declared_current_outputs(tmp_path: Path) -> None:
    initialized, actor = _started(tmp_path)
    (tmp_path / "objective.md").write_text("Objective", encoding="utf-8")
    add_artifact(
        initialized.layout,
        path="objective.md",
        role="objective-and-constraints",
        title="Objective",
        actor=actor,
    )

    with pytest.raises(ConflictError, match="requirements"):
        complete_step(
            initialized.layout,
            step_id="discover",
            assertion="Outputs are complete",
            actor=actor,
        )

    (tmp_path / "objective.md").write_text("Changed without revision", encoding="utf-8")
    (tmp_path / "requirements.md").write_text("Requirements", encoding="utf-8")
    add_artifact(
        initialized.layout,
        path="requirements.md",
        role="requirements",
        title="Requirements",
        actor=actor,
    )
    report = inspect_status(initialized.layout)
    assert report.integrity_state is IntegrityState.HEALTHY
    assert report.next_actions[0].startswith("artifact-revise:")
    assert "Working copy changed" in report.blockers[0]
    with pytest.raises(ConflictError, match="explicit revision"):
        complete_step(
            initialized.layout,
            step_id="discover",
            assertion="Outputs are complete",
            actor=actor,
        )


def test_claim_check_evidence_and_verify_remain_separate(tmp_path: Path) -> None:
    initialized, actor = _started(tmp_path)
    revision_ids = _register_discovery_outputs(initialized, actor)
    completed = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Both declared discovery outputs were produced",
        actor=actor,
        limitations=("Manual review remains required",),
    )
    assert completed.transition.state.step_states["discover"] is StepState.AWAITING_VERIFICATION
    assert completed.transition.state.active_run_ids == ()
    assert list_claims(initialized.layout) == (completed.claim,)

    with pytest.raises(ConflictError, match="no passing result"):
        verify_step(initialized.layout, step_id="discover")

    check = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"invocation": "manual file review", "mode": "manual-record"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
        exit_status=0,
        limitations=("Presence only; semantic quality not established",),
    )
    with pytest.raises(ConflictError, match="No evidence packet"):
        verify_step(initialized.layout, step_id="discover")

    evidence = record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Support the output-presence check",
        actor=actor,
        artifact_revision_ids=revision_ids,
        check_result_ids=(check.check.id,),
        claim_ids=(completed.claim.id,),
        limitations=("Does not establish owner acceptance",),
    )
    assert list_checks(initialized.layout) == (check.check,)
    assert list_evidence(initialized.layout) == (evidence.evidence,)
    for revision_id in revision_ids:
        assert set(dependency_references(initialized.layout, revision_id)) == {
            completed.claim.id,
            check.check.id,
            evidence.evidence.id,
        }

    verified = verify_step(initialized.layout, step_id="discover")
    assert verified.state.step_states["discover"] is StepState.AWAITING_ACCEPTANCE
    assert verified.state.permitted_next_actions == ("acceptance-record:discover",)
    restarted = load_active_initiative(initialized.layout)
    assert restarted.state == verified.state


def test_failed_check_and_new_revision_cannot_satisfy_verification(tmp_path: Path) -> None:
    initialized, actor = _started(tmp_path)
    _register_discovery_outputs(initialized, actor)
    completed = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Initial outputs produced",
        actor=actor,
    )
    failed = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"invocation": "manual review"},
        outcome=CheckOutcome.FAILED,
        actor=actor,
        exit_status=1,
    )
    record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Document the failed check",
        actor=actor,
        artifact_revision_ids=failed.check.target_artifact_revision_ids,
        check_result_ids=(failed.check.id,),
        claim_ids=(completed.claim.id,),
    )
    with pytest.raises(ConflictError, match="no passing result"):
        verify_step(initialized.layout, step_id="discover")

    objective = next(
        view
        for view in list_artifacts(initialized.layout)
        if view.artifact.role == "objective-and-constraints"
    )
    (tmp_path / "objective.md").write_text("Revised objective", encoding="utf-8")
    revise_artifact(
        initialized.layout,
        artifact_id=objective.artifact.id,
        path="objective.md",
        actor=actor,
    )
    passing = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"invocation": "manual review after revision"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
        exit_status=0,
    )
    record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Support the revised check",
        actor=actor,
        artifact_revision_ids=passing.check.target_artifact_revision_ids,
        check_result_ids=(passing.check.id,),
        claim_ids=(completed.claim.id,),
    )
    with pytest.raises(ConflictError, match="No current worker claim"):
        verify_step(initialized.layout, step_id="discover")


def test_preserved_object_tampering_is_an_integrity_error(tmp_path: Path) -> None:
    initialized, actor = _started(tmp_path)
    _register_discovery_outputs(initialized, actor)
    view = list_artifacts(initialized.layout)[0]
    preserved_path = view.current_revision.preserved_object_path
    assert preserved_path is not None
    object_path = initialized.layout.root / preserved_path
    object_path.write_bytes(b"tampered")

    report = inspect_status(initialized.layout)
    assert report.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert "failed size or digest" in report.blockers[0]


def test_artifact_registration_blocks_secret_locations_and_patterns(tmp_path: Path) -> None:
    initialized, actor = _started(tmp_path)
    with pytest.raises(SecurityError, match="must not traverse"):
        add_artifact(
            initialized.layout,
            path="../outside.txt",
            role="requirements",
            title="Traversal attempt",
            actor=actor,
        )

    (tmp_path / ".env").write_text("NORMAL=value", encoding="utf-8")
    with pytest.raises(SecurityError, match="secret location"):
        add_artifact(
            initialized.layout,
            path=".env",
            role="requirements",
            title="Unsafe environment file",
            actor=actor,
        )

    (tmp_path / "credential.txt").write_text(
        "api_key = '0123456789abcdefghijklmnop'",
        encoding="utf-8",
    )
    with pytest.raises(SecurityError, match="credential pattern"):
        add_artifact(
            initialized.layout,
            path="credential.txt",
            role="requirements",
            title="Unsafe credential file",
            actor=actor,
        )


def test_tampered_evidence_record_is_reported_without_repair(tmp_path: Path) -> None:
    initialized, actor = _started(tmp_path)
    revision_ids = _register_discovery_outputs(initialized, actor)
    completed = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Outputs produced",
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
    )
    evidence = record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Original evidence purpose",
        actor=actor,
        artifact_revision_ids=revision_ids,
        check_result_ids=(check.check.id,),
        claim_ids=(completed.claim.id,),
    )
    path = initialized.layout.evidence_directory / f"{evidence.evidence.id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["purpose"] = "Tampered purpose"
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = inspect_status(initialized.layout)
    assert report.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert "Evidence packet does not match" in report.blockers[0]
