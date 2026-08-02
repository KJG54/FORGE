from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.state import ExplanationProfile
from forge.contracts.workflows import StepDefinition
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative, load_active_initiative
from forge.errors import ConfigurationError
from forge.packs.loader import load_pack
from forge.packs.validation import ValidatedPack, calculate_pack_digest, validate_pack
from forge.storage.repository import initialize_repository

ROOT = Path(__file__).resolve().parents[1]
BUNDLED = ROOT / "src" / "forge" / "packs" / "bundled"
SOFTWARE = BUNDLED / "software-basic"
OLD_SOFTWARE_DIGEST = (
    "sha256:0559e70639e2a8ae586d708d67c5b437defb1168d9b6561e01543fab188367bf"
)

runner = CliRunner()


def _create(
    root: Path,
    *,
    pack_id: str = "software-basic",
    profile: ExplanationProfile = ExplanationProfile.MENTORED,
):  # type: ignore[no-untyped-def]
    initialized = initialize_repository(root, owner_display_name="L5 Owner")
    created = create_initiative(
        initialized.layout,
        objective="Exercise step-aware mentoring",
        declared_scope_summary="Advisory explanations only",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
        pack_id=pack_id,
        explanation_profile=profile,
    )
    return initialized, created


def test_step_explanation_is_an_additive_defaulted_schema_field() -> None:
    current = load_pack(SOFTWARE, bundled=True).workflow().steps[0]
    old_payload = current.model_dump(mode="json", exclude={"explanation_content"})

    restored = StepDefinition.model_validate(old_payload)
    schema = StepDefinition.model_json_schema(mode="validation")

    assert restored.explanation_content == {}
    assert "explanation_content" in schema["properties"]
    assert "explanation_content" not in schema["required"]


def test_software_authors_one_mentored_path_and_research_uses_fallback() -> None:
    software = load_pack(SOFTWARE, bundled=True)
    research = load_pack(BUNDLED / "research-basic", bundled=True)

    assert software.manifest.version == software.workflow().version == "0.5.0"
    assert all(set(step.explanation_content) == {"mentored"} for step in software.workflow().steps)
    assert len({step.explanation_content["mentored"] for step in software.workflow().steps}) == 6
    assert all(not step.explanation_content for step in research.workflow().steps)
    assert calculate_pack_digest(software.manifest, software.workflows) == (
        software.manifest.integrity_digest
    )


def test_active_step_precedes_fallback_and_novelty_is_journal_derived(
    tmp_path: Path,
) -> None:
    initialized, created = _create(tmp_path)
    guidance = created.active.explanation_guidance

    assert guidance.source == "step"
    assert guidance.step_id == "discover"
    assert guidance.first_step_encounter is True
    assert guidance.content == created.active.workflow.steps[0].explanation_content["mentored"]
    assert created.active.explanation == guidance.content

    begun = runner.invoke(app, ["begin", "discover", "-C", str(tmp_path)])
    assert begun.exit_code == 0, begun.output
    after_begin = load_active_initiative(initialized.layout).explanation_guidance
    assert after_begin.first_step_encounter is False

    research_root = tmp_path / "research"
    research_root.mkdir()
    _, research_created = _create(research_root, pack_id="research-basic")
    fallback = research_created.active.explanation_guidance
    assert fallback.source == "workflow"
    assert fallback.content == research_created.active.workflow.explanation_content["mentored"]


def test_recap_surfaces_skippable_step_guidance_as_a_warm_session_trigger(
    tmp_path: Path,
) -> None:
    _create(tmp_path)

    recap = runner.invoke(app, ["recap", "-C", str(tmp_path)])

    assert recap.exit_code == 0, recap.output
    assert "Mentoring (mentored, step discover; advisory and skippable)" in recap.stdout
    assert "Reason: warm recap, first encounter with this step" in recap.stdout
    assert "Guidance: Before building anything" in recap.stdout


def test_pre_l5_pack_digest_and_raw_workflow_lock_remain_compatible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = load_pack(SOFTWARE, bundled=True)
    old_workflow = current.workflow().model_copy(
        update={
            "version": "0.4.0",
            "steps": tuple(
                step.model_copy(update={"explanation_content": {}})
                for step in current.workflow().steps
            ),
        }
    )
    old_manifest = current.manifest.model_copy(
        update={"version": "0.4.0", "integrity_digest": OLD_SOFTWARE_DIGEST}
    )
    old_pack = ValidatedPack(SOFTWARE, old_manifest, (old_workflow,), bundled=True)

    assert calculate_pack_digest(old_manifest, (old_workflow,)) == OLD_SOFTWARE_DIGEST
    validate_pack(old_pack)
    monkeypatch.setattr("forge.core.lifecycle.find_pack", lambda *_args: old_pack)

    initialized, _ = _create(tmp_path)
    lock_payload = json.loads(initialized.layout.workflow_lock_file.read_text(encoding="utf-8"))
    for step in lock_payload["steps"]:
        step.pop("explanation_content")
    initialized.layout.workflow_lock_file.write_text(
        json.dumps(lock_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    loaded = load_active_initiative(initialized.layout)
    assert loaded.pack_manifest.version == "0.4.0"
    assert loaded.explanation_guidance.source == "workflow"
    assert loaded.explanation == old_workflow.explanation_content["mentored"]


def test_pack_validation_requires_a_workflow_fallback_for_every_step_profile() -> None:
    current = load_pack(SOFTWARE, bundled=True)
    first = current.workflow().steps[0].model_copy(
        update={"explanation_content": {"unavailable": "Orphan guidance"}}
    )
    changed = current.workflow().model_copy(
        update={"steps": (first, *current.workflow().steps[1:])}
    )
    invalid = ValidatedPack(SOFTWARE, current.manifest, (changed,), bundled=True)

    with pytest.raises(ConfigurationError, match="without workflow-level fallbacks"):
        validate_pack(invalid)
