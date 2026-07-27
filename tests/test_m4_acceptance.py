from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from forge.contracts.actors import Actor
from forge.contracts.agents import AgentResult, ReturnedFile
from forge.contracts.capabilities import (
    CapabilityTrustState,
    LocalValidatorDefinition,
    SideEffectClass,
)
from forge.contracts.decisions import WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE
from forge.contracts.state import StepState
from forge.contracts.verification import (
    AcceptanceRecord,
    CheckOutcome,
    Claim,
    EvidencePacket,
)
from forge.core.acceptance import list_acceptances, record_acceptance, revoke_acceptance
from forge.core.artifacts import add_artifact
from forge.core.authorization import owner_actor
from forge.core.capabilities import approve_capability
from forge.core.decisions import record_decision, withdraw_decision
from forge.core.deviations import open_workflow_deviations, record_workflow_deviation
from forge.core.handoffs import create_handoff
from forge.core.imports import preview_result_import
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.validators import execute_validator_check
from forge.core.verification import (
    complete_step,
    list_evidence,
    record_check,
    record_evidence,
    verify_step,
)
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.packs.loader import load_pack
from forge.security.paths import resolve_repository_path
from forge.storage.configuration import render_configuration
from forge.storage.records import render_record
from forge.storage.repository import InitializationResult, initialize_repository

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = PROJECT_ROOT / "src" / "forge" / "packs" / "bundled" / "software-basic"


def _initiative(path: Path) -> InitializationResult:
    path.mkdir(parents=True, exist_ok=True)
    initialized = initialize_repository(path, owner_display_name="M4 Acceptance Owner")
    create_initiative(
        initialized.layout,
        objective="Prove the cumulative M4 security boundary",
        declared_scope_summary="Exercise adversarial M4 exit criteria",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
    )
    return initialized


def _awaiting_verification(
    initialized: InitializationResult,
) -> tuple[Actor, tuple[UUID, ...], Claim]:
    actor = owner_actor(initialized.configuration.owner)
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    revisions: list[UUID] = []
    for name, role in (
        ("objective.md", "objective-and-constraints"),
        ("requirements.md", "requirements"),
    ):
        (initialized.layout.root / name).write_text(f"# {role}\n", encoding="utf-8")
        revisions.append(
            add_artifact(
                initialized.layout,
                path=name,
                role=role,
                title=role,
                actor=actor,
                media_type="text/markdown",
            ).revision.id
        )
    claim = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Declared discovery outputs were produced",
        actor=actor,
    ).claim
    return actor, tuple(revisions), claim


def _accept_discover(
    initialized: InitializationResult,
) -> tuple[Actor, AcceptanceRecord, EvidencePacket]:
    actor, revisions, claim = _awaiting_verification(initialized)
    check = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"invocation": "M4 closeout review"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
        exit_status=0,
    ).check
    evidence = record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Bind exact current support for the M4 closeout",
        actor=actor,
        artifact_revision_ids=revisions,
        check_result_ids=(check.id,),
        claim_ids=(claim.id,),
    ).evidence
    verify_step(initialized.layout, step_id="discover")
    accepted = record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Exact current discovery outputs",
        actor=actor,
    ).acceptance
    return actor, accepted, evidence


def test_false_completion_and_forged_claims_cannot_reach_acceptance(
    tmp_path: Path,
) -> None:
    initialized = _initiative(tmp_path)
    actor, _, claim = _awaiting_verification(initialized)

    with pytest.raises(ConflictError, match="not awaiting acceptance"):
        record_acceptance(
            initialized.layout,
            step_id="discover",
            accepted_scope="A claim alone must not be accepted",
            actor=actor,
        )
    record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"invocation": "seeded false-completion check"},
        outcome=CheckOutcome.FAILED,
        actor=actor,
        exit_status=1,
    )
    with pytest.raises(ConflictError, match="has no passing result"):
        verify_step(initialized.layout, step_id="discover")

    active = load_active_initiative(initialized.layout)
    assert active.state.step_states["discover"] is StepState.AWAITING_VERIFICATION
    assert active.state.step_states["plan"] is StepState.PENDING
    assert list_acceptances(initialized.layout) == ()

    claim_path = initialized.layout.claim_directory / f"{claim.id}.json"
    forged = json.loads(claim_path.read_text(encoding="utf-8"))
    forged["assertion"] = "Forged completion authority"
    claim_path.write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Claim"):
        load_active_initiative(initialized.layout)


def test_trusted_pack_data_cannot_execute_or_interpret_command_arguments(
    tmp_path: Path,
) -> None:
    script = tmp_path / "literal_arguments.py"
    marker = tmp_path / "shell-injection-marker"
    script.write_text(
        "import json\nimport sys\nprint(json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    validator = LocalValidatorDefinition(
        id="validator.m4.closeout",
        version="1.0.0",
        provider="M4 closeout fixture",
        provider_version="1",
        purpose="Prove trusted data and shell syntax grant no process authority",
        executable=sys.executable,
        arguments=(str(script), "&&", str(marker)),
        timeout_seconds=10,
        expected_outputs=("exit-status", "stdout", "stderr"),
        environment_access=(),
        side_effect_class=SideEffectClass.READ_ONLY,
    )
    repository = tmp_path / "repository"
    repository.mkdir()
    initialized = initialize_repository(repository, owner_display_name="M4 Owner")
    configured = initialized.configuration.model_copy(
        update={
            "capabilities": initialized.configuration.capabilities.model_copy(
                update={"local_validators": (validator,)}
            )
        }
    )
    initialized.layout.configuration_file.write_bytes(render_configuration(configured))
    create_initiative(
        initialized.layout,
        objective="Prove executable trust separation",
        declared_scope_summary="One local validator attempt",
        actor=owner_actor(configured.owner),
        trust_pack_data=True,
    )
    _awaiting_verification(initialized)

    with pytest.raises(ConflictError, match="disabled"):
        execute_validator_check(
            initialized.layout,
            step_id="discover",
            check_id="outputs-present",
            check_version="1",
            capability_id=validator.id,
        )
    assert not initialized.layout.validator_run_directory.exists()
    assert not marker.exists()

    approve_capability(
        initialized.layout,
        capability_id=validator.id,
        scope=CapabilityTrustState.APPROVED_ONCE,
        rationale="Authorize only the exact literal-argument profile",
        actor=owner_actor(configured.owner),
    )
    result = execute_validator_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        capability_id=validator.id,
    )

    assert result.check.outcome is CheckOutcome.PASSED
    assert result.check.stdout_capture_path is not None
    captured = (
        initialized.layout.root / result.check.stdout_capture_path
    ).read_text(encoding="utf-8")
    assert json.loads(captured) == ["&&", str(marker)]
    assert not marker.exists()
    assert list_evidence(initialized.layout) == ()
    assert list_acceptances(initialized.layout) == ()

    profile = validator.model_dump(mode="json")
    profile["command"] = f"{sys.executable} {script} && {marker}"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LocalValidatorDefinition.model_validate(profile)


def test_revoked_acceptance_and_withdrawn_review_remove_current_authority(
    tmp_path: Path,
) -> None:
    initialized = _initiative(tmp_path)
    actor, acceptance, _ = _accept_discover(initialized)
    assert load_active_initiative(initialized.layout).state.step_states[
        "plan"
    ] is StepState.READY

    revoke_acceptance(
        initialized.layout,
        acceptance_id=acceptance.id,
        reason="The accepted support is no longer authorized",
        actor=actor,
    )
    revoked = load_active_initiative(initialized.layout)
    assert revoked.state.step_states["discover"] is StepState.INVALIDATED
    assert revoked.state.step_states["plan"] is StepState.PENDING
    assert acceptance.id in revoked.state.stale_record_ids

    deviation = record_workflow_deviation(
        initialized.layout,
        declared_behavior="Use every locked verification action",
        actual_behavior="One action was omitted",
        rationale="The discrepancy must remain explicit",
        review_requirement="Choose rework or abandonment",
        actor=actor,
    ).deviation
    review = record_decision(
        initialized.layout,
        decision_type=WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE,
        question="How should the deviation be resolved?",
        considered_options=("Rework", "Abandon"),
        chosen_outcome="Rework",
        rationale="No workflow requirement is waived",
        actor=actor,
        affected_record_ids=(deviation.id,),
        bound_digests=deviation.affected_digests,
    ).decision
    assert open_workflow_deviations(initialized.layout) == ()

    withdrawal = withdraw_decision(
        initialized.layout,
        decision_id=review.id,
        reason="New evidence requires a fresh owner review",
        actor=actor,
    )
    reopened = open_workflow_deviations(initialized.layout)
    assert reopened[0].deviation.id == deviation.id
    active = load_active_initiative(initialized.layout)
    assert review.id in active.state.stale_record_ids
    assert withdrawal.decision.id in active.state.open_decision_ids


def test_malicious_packs_hostile_imports_and_path_escape_fail_closed(
    tmp_path: Path,
) -> None:
    malicious_pack = tmp_path / "malicious-pack"
    shutil.copytree(PACK_ROOT, malicious_pack)
    (malicious_pack / "payload.py").write_text(
        "raise SystemExit('must never execute')\n",
        encoding="utf-8",
    )
    with pytest.raises(SecurityError, match="executable content"):
        load_pack(malicious_pack)

    initialized = _initiative(tmp_path / "repository")
    handoff = create_handoff(initialized.layout, step_id="discover")
    before = initialized.layout.event_journal_file.read_bytes()
    bundle = tmp_path / "hostile-import"
    bundle.mkdir()
    (bundle / "objective.md").write_text("# Objective\n", encoding="utf-8")
    (bundle / "undeclared.txt").write_text("unexpected content\n", encoding="utf-8")
    result = AgentResult(
        id=uuid4(),
        source_run_or_handoff_id=handoff.handoff.id,
        worker_claims=("Returned one file",),
        returned_files=(
            ReturnedFile(
                source_path="objective.md",
                proposed_target_path="objective.md",
                media_type="text/markdown",
            ),
        ),
    )
    manifest = bundle / "result.json"
    manifest.write_bytes(render_record(result))
    with pytest.raises(SecurityError, match="inventory"):
        preview_result_import(initialized.layout, manifest_path=manifest)

    escaped = tmp_path / "escaped-import"
    escaped.mkdir()
    payload = result.model_dump(mode="json")
    payload["id"] = str(uuid4())
    payload["returned_files"][0]["source_path"] = "../outside.md"
    escaped_manifest = escaped / "result.json"
    escaped_manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises((ConfigurationError, SecurityError)):
        preview_result_import(initialized.layout, manifest_path=escaped_manifest)

    with pytest.raises(SecurityError, match="must not traverse"):
        resolve_repository_path(initialized.layout.root, "../outside.md")
    assert initialized.layout.event_journal_file.read_bytes() == before
    assert not (initialized.layout.root / "objective.md").exists()


def test_security_documentation_requires_external_hostile_code_isolation() -> None:
    security = " ".join((PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8").split())
    constitution = " ".join(
        (PROJECT_ROOT / "docs" / "constitution.md").read_text(encoding="utf-8").split()
    )
    validators = " ".join(
        (PROJECT_ROOT / "docs" / "validators.md").read_text(encoding="utf-8").split()
    )

    assert "malicious process" in security
    assert "external sandboxing for hostile code" in security
    assert "malicious process" in constitution
    assert "external process or operating-system isolation" in validators
