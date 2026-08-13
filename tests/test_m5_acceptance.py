from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from conftest import PROJECT_BASIC_VERSION, RESEARCH_BASIC_VERSION, SOFTWARE_BASIC_VERSION

from forge.contracts import CONTRACT_MODELS
from forge.contracts.actors import ActorType
from forge.contracts.configuration import PackConfiguration
from forge.contracts.state import ExplanationProfile, StepState
from forge.contracts.workflows import WorkflowDefinition
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative, load_active_initiative
from forge.packs.loader import load_pack
from forge.packs.validation import calculate_pack_digest, validate_pack
from forge.storage.configuration import (
    load_configuration,
    render_configuration,
)
from forge.storage.repository import RepositoryLayout, initialize_repository

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_PACK_ROOT = PROJECT_ROOT / "src" / "forge" / "packs" / "bundled"
DATA_ONLY_PACK_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "packs" / "community-research"
BUNDLED_PACK_IDS = ("project-basic", "software-basic", "research-basic")
EXPECTED_ACTORS = (
    ActorType.OWNER,
    ActorType.HUMAN_CONTRIBUTOR,
    ActorType.AGENT_ADAPTER,
)
EXPECTED_TRANSITIONS = (
    (
        "begin",
        StepState.READY,
        StepState.IN_PROGRESS,
        (),
        "participant",
    ),
    (
        "submit",
        StepState.IN_PROGRESS,
        StepState.AWAITING_VERIFICATION,
        ("claim-recorded",),
        "participant",
    ),
    (
        "rework",
        StepState.INVALIDATED,
        StepState.IN_PROGRESS,
        (),
        "participant",
    ),
    (
        "verify",
        StepState.AWAITING_VERIFICATION,
        StepState.AWAITING_ACCEPTANCE,
        ("required-checks-passed", "required-evidence-registered"),
        "forge-cli",
    ),
    (
        "accept",
        StepState.AWAITING_ACCEPTANCE,
        StepState.COMPLETED,
        ("owner-acceptance-recorded",),
        "owner",
    ),
)


def _ancestor_step_ids(workflow: WorkflowDefinition, step_id: str) -> set[str]:
    by_id = {step.id: step for step in workflow.steps}
    ancestors: set[str] = set()
    pending = list(by_id[step_id].prerequisites)
    while pending:
        prerequisite = pending.pop()
        if prerequisite in ancestors:
            continue
        ancestors.add(prerequisite)
        pending.extend(by_id[prerequisite].prerequisites)
    return ancestors


@pytest.mark.parametrize("pack_id", BUNDLED_PACK_IDS)
def test_bundled_packs_pass_one_shared_conformance_contract(
    tmp_path: Path,
    pack_id: str,
) -> None:
    pack = load_pack(BUNDLED_PACK_ROOT / pack_id, bundled=True)
    validate_pack(pack)
    workflow = pack.workflow()

    assert pack.manifest.id == pack_id
    expected_version = {
        "project-basic": PROJECT_BASIC_VERSION,
        "software-basic": SOFTWARE_BASIC_VERSION,
        "research-basic": RESEARCH_BASIC_VERSION,
    }[pack_id]
    assert pack.manifest.version == workflow.version == expected_version
    assert pack.manifest.provided_workflow_ids == (workflow.id,)
    assert pack.manifest.declared_capability_ids == ()
    assert pack.manifest.explanation_paths == ()
    assert pack.manifest.schema_compatibility == ("forge-contracts-1",)
    assert workflow.pack_id == pack.manifest.id
    assert workflow.compatibility_constraints == ("forge-contracts-1",)
    assert set(workflow.explanation_content) == {
        profile.value for profile in ExplanationProfile
    }
    assert (
        calculate_pack_digest(pack.manifest, pack.workflows, pack.resources)
        == pack.manifest.integrity_digest
    )
    assert tuple(
        (
            transition.id,
            transition.source_state,
            transition.destination_state,
            transition.conditions,
            transition.authority_requirement,
        )
        for transition in workflow.transitions
    ) == EXPECTED_TRANSITIONS

    producers = {
        output: step.id
        for step in workflow.steps
        for output in step.required_outputs
    }
    for step in workflow.steps:
        assert step.required_outputs
        assert step.claim_requirements == ("outputs-produced",)
        assert step.check_requirements
        assert step.acceptance_requirements == ("owner-acceptance",)
        assert step.allowed_actors == EXPECTED_ACTORS
        assert step.allowed_transitions == (
            "begin",
            "rework",
            "submit",
            "verify",
            "accept",
        )
        assert step.context_selection_rules
        ancestors = _ancestor_step_ids(workflow, step.id)
        assert all(
            required_input in producers
            and producers[required_input] in ancestors
            for required_input in step.required_inputs
    )

    repository = tmp_path / pack_id
    repository.mkdir()
    initialized = initialize_repository(
        repository,
        owner_display_name="Shared Conformance Owner",
    )
    create_initiative(
        initialized.layout,
        objective=f"Exercise {pack_id} through shared core services",
        declared_scope_summary="M5 bundled-pack conformance only",
        actor=owner_actor(initialized.configuration.owner),
        pack_id=pack_id,
        workflow_id=workflow.id,
        trust_pack_data=True,
    )
    active = load_active_initiative(initialized.layout)
    assert active.pack_manifest.id == pack_id
    assert active.workflow.id == workflow.id
    assert active.state.current_step_id == workflow.steps[0].id
    assert active.state.step_states[workflow.steps[0].id] is StepState.READY
    assert all(
        active.state.step_states[step.id] is StepState.PENDING
        for step in workflow.steps[1:]
    )


def test_public_contract_fields_remain_domain_neutral() -> None:
    forbidden_domain_terms = {"software", "research"}
    for contract_name, model in CONTRACT_MODELS.items():
        assert forbidden_domain_terms.isdisjoint(contract_name.lower().split("-"))
        for field_name, field in model.model_fields.items():
            schema_name = field.alias or field_name
            field_terms = schema_name.lower().replace("_", "-").split("-")
            assert forbidden_domain_terms.isdisjoint(field_terms), (
                f"{contract_name}.{schema_name} is domain-specific"
            )


def test_data_only_local_pack_validates_and_creates_without_python_content(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "local-pack-repository"
    repository.mkdir()
    initialized = initialize_repository(
        repository,
        owner_display_name="Local Pack Owner",
    )
    local_pack = repository / "packs" / "community-research"
    shutil.copytree(DATA_ONLY_PACK_ROOT, local_pack)
    inventory = tuple(path for path in local_pack.rglob("*") if path.is_file())
    assert inventory
    assert all(path.suffix in {".yaml", ".md"} for path in inventory)
    assert not any(path.suffix == ".py" for path in inventory)

    configuration = load_configuration(initialized.layout.configuration_file)
    configured = configuration.model_copy(
        update={
            "packs": PackConfiguration(
                local_paths=("packs/community-research",),
            )
        }
    )
    initialized.layout.configuration_file.write_bytes(render_configuration(configured))

    pack = load_pack(local_pack)
    validate_pack(pack)
    assert not pack.bundled
    assert pack.manifest.declared_capability_ids == ()
    create_initiative(
        initialized.layout,
        objective="Validate a local data-authored community research workflow",
        declared_scope_summary="Data-only local pack conformance",
        actor=owner_actor(configured.owner),
        pack_id=pack.manifest.id,
        workflow_id=pack.workflow().id,
        trust_pack_data=True,
    )
    active = load_active_initiative(RepositoryLayout.at(repository))
    assert active.pack_manifest.id == "community-research-test"
    assert active.workflow.id == "community-research"
    assert active.state.current_step_id == "frame"
    assert active.state.step_states["frame"] is StepState.READY
