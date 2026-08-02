from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.configuration import ProjectConfiguration
from forge.contracts.state import ExplanationProfile
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative, load_active_initiative
from forge.errors import ConfigurationError
from forge.packs.loader import load_pack
from forge.packs.validation import ValidatedPack, calculate_pack_digest, validate_pack
from forge.storage.repository import RepositoryLayout, initialize_repository

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_PACK_ROOT = PROJECT_ROOT / "src" / "forge" / "packs" / "bundled"
SOFTWARE_PACK_ROOT = BUNDLED_PACK_ROOT / "software-basic"
LEGACY_SOFTWARE_DIGEST = (
    "sha256:17e757327c92ae38f904cfdef4389ab16ef0a883d6b4493aaac375717bca0708"
)
ALL_PROFILES = tuple(ExplanationProfile)

runner = CliRunner()


@pytest.mark.parametrize("pack_id", ("software-basic", "research-basic"))
def test_bundled_packs_supply_exactly_four_digest_bound_profiles(
    pack_id: str,
) -> None:
    pack = load_pack(BUNDLED_PACK_ROOT / pack_id, bundled=True)
    workflow = pack.workflow()

    expected_version = "0.5.0" if pack_id == "software-basic" else "0.4.0"
    assert pack.manifest.version == expected_version
    assert workflow.version == expected_version
    assert set(workflow.explanation_content) == {
        profile.value for profile in ALL_PROFILES
    }
    assert len(set(workflow.explanation_content.values())) == len(ALL_PROFILES)
    assert pack.manifest.explanation_paths == ()
    assert pack.manifest.declared_capability_ids == ()
    assert (
        calculate_pack_digest(pack.manifest, pack.workflows, pack.resources)
        == pack.manifest.integrity_digest
    )


@pytest.mark.parametrize("pack_id", ("software-basic", "research-basic"))
def test_profiles_change_only_locked_presentation_not_governance(
    tmp_path: Path,
    pack_id: str,
) -> None:
    baseline_governance: dict[str, object] | None = None
    baseline_state: tuple[object, ...] | None = None
    explanations: set[str] = set()

    for profile in ALL_PROFILES:
        repository = tmp_path / f"{pack_id}-{profile.value}"
        repository.mkdir()
        initialized = initialize_repository(
            repository,
            owner_display_name="Profile Owner",
        )
        created = create_initiative(
            initialized.layout,
            objective="Compare presentation-only profiles",
            declared_scope_summary="Identical governance under different educational detail",
            actor=owner_actor(initialized.configuration.owner),
            trust_pack_data=True,
            pack_id=pack_id,
            explanation_profile=profile,
        )
        active = load_active_initiative(initialized.layout)

        assert created.active.initiative.explanation_profile is profile
        assert active.initiative.explanation_profile is profile
        selected_step = next(
            step for step in active.workflow.steps if step.id == active.state.current_step_id
        )
        expected = selected_step.explanation_content.get(
            profile.value,
            active.workflow.explanation_content[profile.value],
        )
        assert active.explanation == expected
        explanations.add(active.explanation)

        governance = active.workflow.model_dump(exclude={"explanation_content"})
        state = (
            active.state.lifecycle_state,
            active.state.integrity_state,
            active.state.current_step_id,
            active.state.step_states,
            active.state.open_gate_ids,
            active.state.permitted_next_actions,
        )
        if baseline_governance is None:
            baseline_governance = governance
            baseline_state = state
        else:
            assert governance == baseline_governance
            assert state == baseline_state

    assert len(explanations) == len(ALL_PROFILES)


@pytest.mark.parametrize(
    ("pack_id", "profile"),
    (
        ("software-basic", ExplanationProfile.MINIMAL),
        ("research-basic", ExplanationProfile.MENTORED),
    ),
)
def test_cli_selects_new_profiles_and_reports_canonical_receipt(
    tmp_path: Path,
    pack_id: str,
    profile: ExplanationProfile,
) -> None:
    repository = tmp_path / f"{pack_id}-{profile.value}"
    repository.mkdir()
    initialized = initialize_repository(
        repository,
        owner_display_name="CLI Profile Owner",
    )

    result = runner.invoke(
        app,
        [
            "create",
            "Exercise a new explanation profile",
            "--scope",
            "Presentation-only CLI selection",
            "--pack",
            pack_id,
            "--explanation",
            profile.value,
            "--trust-pack-data",
            "-C",
            str(repository),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Recorded -> initiative-created" in result.stdout
    assert "Means    ->" in result.stdout
    active = load_active_initiative(initialized.layout)
    assert active.initiative.explanation_profile is profile
    assert active.explanation


def test_two_profile_pack_remains_valid_and_unavailable_profile_fails_precommit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = load_pack(SOFTWARE_PACK_ROOT, bundled=True)
    legacy_workflow = current.workflow().model_copy(
        update={
            "version": "0.3.0",
            "steps": tuple(
                step.model_copy(update={"explanation_content": {}})
                for step in current.workflow().steps
            ),
            "explanation_content": {
                key: value
                for key, value in current.workflow().explanation_content.items()
                if key in {"standard", "guided"}
            },
        }
    )
    legacy_manifest = current.manifest.model_copy(
        update={
            "version": "0.3.0",
            "integrity_digest": LEGACY_SOFTWARE_DIGEST,
        }
    )
    legacy_pack = ValidatedPack(
        SOFTWARE_PACK_ROOT,
        legacy_manifest,
        (legacy_workflow,),
        bundled=True,
    )
    assert (
        calculate_pack_digest(legacy_manifest, (legacy_workflow,))
        == LEGACY_SOFTWARE_DIGEST
    )
    validate_pack(legacy_pack)

    def find_legacy_pack(
        _layout: RepositoryLayout,
        _configuration: ProjectConfiguration,
        _pack_id: str,
    ) -> ValidatedPack:
        return legacy_pack

    monkeypatch.setattr(
        "forge.core.lifecycle.find_pack",
        find_legacy_pack,
    )

    supported_root = tmp_path / "supported"
    supported_root.mkdir()
    supported = initialize_repository(
        supported_root,
        owner_display_name="Legacy Profile Owner",
    )
    created = create_initiative(
        supported.layout,
        objective="Use a legacy profile",
        declared_scope_summary="Existing two-profile pack compatibility",
        actor=owner_actor(supported.configuration.owner),
        trust_pack_data=True,
        explanation_profile=ExplanationProfile.STANDARD,
    )
    assert created.active.pack_manifest.version == "0.3.0"
    assert load_active_initiative(supported.layout).explanation == (
        legacy_workflow.explanation_content["standard"]
    )

    unsupported_root = tmp_path / "unsupported"
    unsupported_root.mkdir()
    unsupported = initialize_repository(
        unsupported_root,
        owner_display_name="Legacy Profile Owner",
    )
    with pytest.raises(ConfigurationError, match=r"does not provide.*minimal"):
        create_initiative(
            unsupported.layout,
            objective="Reject an unavailable profile",
            declared_scope_summary="Fail before initiative persistence",
            actor=owner_actor(unsupported.configuration.owner),
            trust_pack_data=True,
            explanation_profile=ExplanationProfile.MINIMAL,
        )
    assert not any(unsupported.layout.active_directory.iterdir())
