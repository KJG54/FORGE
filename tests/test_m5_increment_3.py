from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.state import StepState
from forge.contracts.verification import CheckOutcome
from forge.core.acceptance import record_acceptance
from forge.core.artifacts import add_artifact
from forge.core.authorization import owner_actor
from forge.core.lifecycle import (
    begin_manual_run,
    create_initiative,
    load_active_initiative,
)
from forge.core.structural_validation import execute_structural_check
from forge.core.verification import (
    complete_step,
    list_checks,
    list_claims,
    list_evidence,
    record_check,
    record_evidence,
    verify_step,
)
from forge.errors import ConfigurationError, IntegrityError
from forge.packs.loader import load_pack
from forge.packs.validation import (
    PackResourceKind,
    ValidatedPack,
    calculate_pack_digest,
    validate_pack,
)
from forge.storage.repository import InitializationResult, initialize_repository

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_PACK_ROOT = (
    PROJECT_ROOT / "src" / "forge" / "packs" / "bundled" / "research-basic"
)
EVIDENCE_VALIDATOR = "research-evidence-register-structure"
CITATION_VALIDATOR = "research-citation-record-structure"
EVIDENCE_CHECK = "evidence-register-structure"
CITATION_CHECK = "citation-record-structure"
TEMPLATE_ONLY_RESEARCH_DIGEST = (
    "sha256:e382de4b8ebff10c583fdb976750cd69169ee1ed4e31a727c647a118cedb4563"
)

runner = CliRunner()


def _advance_manually(
    initialized: InitializationResult,
    actor: Actor,
    *,
    step_id: str,
    outputs: tuple[str, ...],
) -> None:
    begin_manual_run(initialized.layout, step_id=step_id, actor=actor)
    revision_ids: list[UUID] = []
    for role in outputs:
        path = initialized.layout.root / f"{step_id}-{role}.md"
        path.write_text(f"# {role}\n\nBounded content.\n", encoding="utf-8")
        result = add_artifact(
            initialized.layout,
            path=path.name,
            role=role,
            title=role,
            actor=actor,
            media_type="text/markdown",
        )
        revision_ids.append(result.revision.id)
    claim = complete_step(
        initialized.layout,
        step_id=step_id,
        assertion=f"Declared {step_id} outputs were produced",
        actor=actor,
    ).claim
    active = load_active_initiative(initialized.layout)
    step = next(item for item in active.workflow.steps if item.id == step_id)
    check_ids: list[UUID] = []
    for check_id in step.check_requirements:
        check = record_check(
            initialized.layout,
            step_id=step_id,
            check_id=check_id,
            check_version="1",
            invocation_metadata={"invocation": "bounded fixture", "mode": "manual-record"},
            outcome=CheckOutcome.PASSED,
            actor=actor,
            limitations=("Manual structure review does not establish factual truth",),
        ).check
        check_ids.append(check.id)
    record_evidence(
        initialized.layout,
        step_id=step_id,
        purpose=f"Support {step_id} fixture progression",
        actor=actor,
        artifact_revision_ids=tuple(revision_ids),
        check_result_ids=tuple(check_ids),
        claim_ids=(claim.id,),
        limitations=("Fixture evidence is not owner acceptance",),
    )
    verify_step(initialized.layout, step_id=step_id)
    record_acceptance(
        initialized.layout,
        step_id=step_id,
        accepted_scope=f"Exact {step_id} fixture outputs",
        actor=actor,
        known_limitations=("Fixture acceptance does not establish factual truth",),
        residual_risks=("Research content may remain incomplete",),
    )


def _collect_awaiting_verification(
    tmp_path: Path,
    *,
    populated: bool,
) -> tuple[InitializationResult, Actor, tuple[UUID, UUID]]:
    initialized = initialize_repository(tmp_path, owner_display_name="Research Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Exercise data-only research structure checks",
        declared_scope_summary="M5 Increment 3 structural validation only",
        actor=actor,
        trust_pack_data=True,
        pack_id="research-basic",
    )
    _advance_manually(
        initialized,
        actor,
        step_id="frame",
        outputs=("research-question", "research-boundaries"),
    )
    _advance_manually(
        initialized,
        actor,
        step_id="plan",
        outputs=("research-plan", "evidence-criteria"),
    )
    begin_manual_run(initialized.layout, step_id="collect", actor=actor)

    source_register = tmp_path / "source-register.md"
    research_notes = tmp_path / "research-notes.md"
    if populated:
        source_register.write_text(
            """# Research Evidence Register

## Governed context

## Evidence entries

### Evidence ID: evidence-1

- Citation ID: citation-1
- Source type: primary document
- Stable locator, DOI, or URL: https://example.invalid/source
- Relevant research question or subquestion: bounded question
- Claim(s) this evidence may support: bounded claim
- Direct observation, quotation, paraphrase, or inference: observation
- Known limitations: fixture only

## Coverage and gaps

## Boundary
""",
            encoding="utf-8",
        )
        research_notes.write_text(
            """# Research Citation Record

## Identity

- Citation ID: citation-1
- Source type: primary document
- Author or creator: Example Author
- Title: Example Source
- Stable URL or repository-relative locator: https://example.invalid/source

## Exact locator

## Research relationship

- Evidence ID: evidence-1
- Claim(s) associated with this citation: bounded claim

## Review

- Details that could not be confirmed: none recorded
- Source-quality limitations: fixture only

## Boundary
""",
            encoding="utf-8",
        )
    else:
        source_register.write_text(
            "# Research Evidence Register\n\n## Evidence entries\n\n- Citation ID:\n",
            encoding="utf-8",
        )
        research_notes.write_text("# Research Citation Record\n", encoding="utf-8")

    source = add_artifact(
        initialized.layout,
        path=source_register.name,
        role="source-register",
        title="Source register",
        actor=actor,
        media_type="text/markdown",
    )
    notes = add_artifact(
        initialized.layout,
        path=research_notes.name,
        role="research-notes",
        title="Research notes",
        actor=actor,
        media_type="text/markdown",
    )
    complete_step(
        initialized.layout,
        step_id="collect",
        assertion="Current evidence and citation structures were produced",
        actor=actor,
        limitations=("Structure does not establish factual truth",),
    )
    return initialized, actor, (source.revision.id, notes.revision.id)


def test_research_structural_validators_are_data_only_digest_bound_and_compatible(
    tmp_path: Path,
) -> None:
    pack = load_pack(RESEARCH_PACK_ROOT, bundled=True)
    validators = tuple(
        resource
        for resource in pack.resources
        if resource.kind is PackResourceKind.STRUCTURAL_VALIDATOR
    )

    assert pack.manifest.version == "0.3.0"
    assert [resource.definition.id for resource in validators if resource.definition] == [
        EVIDENCE_VALIDATOR,
        CITATION_VALIDATOR,
    ]
    assert all(resource.definition is not None for resource in validators)
    assert pack.manifest.declared_capability_ids == ()
    assert {item.definition.check_id for item in validators if item.definition} == {
        EVIDENCE_CHECK,
        CITATION_CHECK,
    }

    template_resources = tuple(
        resource
        for resource in pack.resources
        if resource.kind is PackResourceKind.TEMPLATE
    )
    legacy_steps = tuple(
        step.model_copy(
            update={
                "check_requirements": ("evidence-register-structure-reviewed",)
            }
        )
        if step.id == "collect"
        else step
        for step in pack.workflow().steps
    )
    legacy_manifest = pack.manifest.model_copy(
        update={
            "version": "0.2.0",
            "data_resource_paths": (),
            "integrity_digest": TEMPLATE_ONLY_RESEARCH_DIGEST,
        }
    )
    legacy_workflow = pack.workflow().model_copy(
        update={"version": "0.2.0", "steps": legacy_steps}
    )
    legacy_pack = ValidatedPack(
        RESEARCH_PACK_ROOT,
        legacy_manifest,
        (legacy_workflow,),
        template_resources,
    )
    assert (
        calculate_pack_digest(
            legacy_manifest,
            (legacy_workflow,),
            template_resources,
        )
        == TEMPLATE_ONLY_RESEARCH_DIGEST
    )
    validate_pack(legacy_pack)

    changed = tmp_path / "changed-pack"
    shutil.copytree(RESEARCH_PACK_ROOT, changed)
    validator = changed / "validators" / "evidence-register-structure.yaml"
    validator.write_text(
        validator.read_text(encoding="utf-8") + "\n# changed\n",
        encoding="utf-8",
    )
    with pytest.raises(IntegrityError, match="integrity digest mismatch"):
        load_pack(changed)

    executable = tmp_path / "executable-pack"
    shutil.copytree(RESEARCH_PACK_ROOT, executable)
    definition = executable / "validators" / "citation-record-structure.yaml"
    definition.write_text(
        definition.read_text(encoding="utf-8") + "\nexecutable: python\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="Invalid structural validator definition"):
        load_pack(executable)


def test_structural_checks_pass_without_process_and_remain_separate_from_evidence(
    tmp_path: Path,
) -> None:
    initialized, actor, revision_ids = _collect_awaiting_verification(
        tmp_path,
        populated=True,
    )

    evidence_result = execute_structural_check(
        initialized.layout,
        step_id="collect",
        check_id=EVIDENCE_CHECK,
        validator_id=EVIDENCE_VALIDATOR,
    )
    citation_result = execute_structural_check(
        initialized.layout,
        step_id="collect",
        check_id=CITATION_CHECK,
        validator_id=CITATION_VALIDATOR,
    )
    cli_result = runner.invoke(
        app,
        [
            "check",
            "structure",
            "collect",
            EVIDENCE_CHECK,
            "--validator",
            EVIDENCE_VALIDATOR,
            "-C",
            str(tmp_path),
        ],
    )
    assert cli_result.exit_code == 0, cli_result.stderr
    assert "Recorded check result" in cli_result.stdout
    assert "Structural findings: none" in cli_result.stdout
    assert "No process or executable capability was started" in cli_result.stdout
    cli_check = list_checks(initialized.layout)[-1]
    assert cli_check.check_id == EVIDENCE_CHECK

    assert evidence_result.recording.check.outcome is CheckOutcome.PASSED
    assert citation_result.recording.check.outcome is CheckOutcome.PASSED
    assert evidence_result.findings == ()
    assert citation_result.findings == ()
    for result in (evidence_result, citation_result):
        check = result.recording.check
        assert check.actor.actor_type is ActorType.FORGE_CLI
        assert check.capability_id is None
        assert check.run_id is None
        assert check.exit_status is None
        assert set(check.target_artifact_revision_ids) == set(revision_ids)
        assert "factual truth" in check.limitations[0]

    active = load_active_initiative(initialized.layout)
    assert active.state.step_states["collect"] is StepState.AWAITING_VERIFICATION
    assert active.state.active_run_ids == ()
    historical_evidence = list_evidence(initialized.layout)
    assert len(historical_evidence) == 2
    assert all(
        evidence_result.recording.check.id not in packet.check_result_ids
        and citation_result.recording.check.id not in packet.check_result_ids
        for packet in historical_evidence
    )

    claim_id = list_claims(initialized.layout)[-1].id
    record_evidence(
        initialized.layout,
        step_id="collect",
        purpose="Bind exact structural check support",
        actor=actor,
            artifact_revision_ids=revision_ids,
            check_result_ids=(
                cli_check.id,
                citation_result.recording.check.id,
            ),
        claim_ids=(claim_id,),
        limitations=("Structural support does not establish factual truth",),
    )
    verified = verify_step(initialized.layout, step_id="collect")
    assert verified.state.step_states["collect"] is StepState.AWAITING_ACCEPTANCE


def test_structural_nonconformance_records_failed_check_without_other_authority(
    tmp_path: Path,
) -> None:
    initialized, _actor, _revision_ids = _collect_awaiting_verification(
        tmp_path,
        populated=False,
    )

    result = execute_structural_check(
        initialized.layout,
        step_id="collect",
        check_id=EVIDENCE_CHECK,
        validator_id=EVIDENCE_VALIDATOR,
    )

    assert result.recording.check.outcome is CheckOutcome.FAILED
    assert result.findings
    assert any("missing-heading" in finding for finding in result.findings)
    assert any("empty-field" in finding for finding in result.findings)
    restarted = load_active_initiative(initialized.layout)
    assert restarted.state.step_states["collect"] is StepState.AWAITING_VERIFICATION
    assert restarted.state.active_run_ids == ()
    checks = list_checks(initialized.layout)
    assert len(checks) == 3
    assert checks[-1] == result.recording.check
    assert len(list_evidence(initialized.layout)) == 2

    check_path = (
        initialized.layout.check_directory / f"{result.recording.check.id}.json"
    )
    raw_payload = cast(object, json.loads(check_path.read_text(encoding="utf-8")))
    assert isinstance(raw_payload, dict)
    payload = cast("dict[str, object]", raw_payload)
    affected_value = payload["affected_digests"]
    assert isinstance(affected_value, list)
    affected_digests = cast("list[str]", affected_value)
    payload["affected_digests"] = affected_digests[1:]
    check_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    with pytest.raises(IntegrityError, match="Check result does not match event"):
        load_active_initiative(initialized.layout)


def test_structural_validator_cli_inspection_is_read_only_and_locked(
    tmp_path: Path,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="CLI Owner")
    before = runner.invoke(
        app,
        ["pack", "validator", "list", "research-basic", "-C", str(tmp_path)],
    )
    assert before.exit_code == 0, before.stderr
    assert "available research-basic@0.3.0" in before.stdout
    assert EVIDENCE_VALIDATOR in before.stdout
    assert CITATION_VALIDATOR in before.stdout

    shown = runner.invoke(
        app,
        [
            "pack",
            "validator",
            "show",
            "research-basic",
            EVIDENCE_VALIDATOR,
            "-C",
            str(tmp_path),
        ],
    )
    assert shown.exit_code == 0, shown.stderr
    assert shown.stdout == (
        RESEARCH_PACK_ROOT / "validators" / "evidence-register-structure.yaml"
    ).read_text(encoding="utf-8")

    create_initiative(
        initialized.layout,
        objective="Lock structural validators",
        declared_scope_summary="Read-only validator inspection",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
        pack_id="research-basic",
    )
    event_bytes = initialized.layout.event_journal_file.read_bytes()
    locked = runner.invoke(
        app,
        ["pack", "validator", "list", "research-basic", "-C", str(tmp_path)],
    )
    assert locked.exit_code == 0, locked.stderr
    assert "locked research-basic@0.3.0" in locked.stdout
    assert initialized.layout.event_journal_file.read_bytes() == event_bytes

    locked_resource = (
        initialized.layout.pack_resource_directory
        / "validators"
        / "evidence-register-structure.yaml"
    )
    locked_resource.write_text(
        locked_resource.read_text(encoding="utf-8") + "\n# tampered\n",
        encoding="utf-8",
    )
    with pytest.raises(IntegrityError, match="integrity digest mismatch"):
        load_active_initiative(initialized.layout)
