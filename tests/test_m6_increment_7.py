from pathlib import Path

from forge.contracts.packs import PackTrustState
from forge.contracts.state import InitiativeLifecycleState, StepState
from forge.core.agent_context import load_agent_context
from forge.core.artifacts import list_artifacts
from forge.core.lifecycle import load_active_initiative
from forge.packs.loader import load_pack
from forge.storage.configuration import load_configuration
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout

ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "packs" / "forge-framework-change"


def _prerequisite_steps(step_id: str, prerequisites: dict[str, tuple[str, ...]]) -> set[str]:
    result: set[str] = set()
    pending = list(prerequisites[step_id])
    while pending:
        prerequisite = pending.pop()
        if prerequisite in result:
            continue
        result.add(prerequisite)
        pending.extend(prerequisites[prerequisite])
    return result


def test_framework_change_pack_is_data_only_capability_free_and_complete() -> None:
    pack = load_pack(PACK_ROOT)
    workflow = pack.workflow()
    files = tuple(path for path in PACK_ROOT.rglob("*") if path.is_file())

    assert not pack.bundled
    assert pack.manifest.id == "forge-framework-change"
    assert pack.manifest.declared_capability_ids == ()
    assert files
    assert all(path.suffix == ".yaml" for path in files)
    assert tuple(step.id for step in workflow.steps) == (
        "scope",
        "implement",
        "verify-release",
        "review-risk",
        "closeout",
    )

    prerequisites = {step.id: step.prerequisites for step in workflow.steps}
    outputs = {step.id: set(step.required_outputs) for step in workflow.steps}
    for step in workflow.steps:
        available: set[str] = set()
        for prerequisite in _prerequisite_steps(step.id, prerequisites):
            available.update(outputs[prerequisite])
        assert set(step.required_inputs) <= available


def test_repository_dogfood_state_is_healthy_bound_and_owner_accepted() -> None:
    layout = RepositoryLayout.at(ROOT)
    configuration = load_configuration(layout.configuration_file)
    active = load_active_initiative(layout)
    artifacts = list_artifacts(layout)
    events = read_journal(layout.event_journal_file)
    context = load_agent_context(layout)

    assert configuration.behavior.require_clean_git_for_close
    assert configuration.packs.local_paths == ("packs/forge-framework-change",)
    assert active.pack_manifest.id == "forge-framework-change"
    assert active.pack_trust.trust_state is PackTrustState.TRUSTED_DATA
    assert active.workflow.id == "framework-change"
    assert active.state.lifecycle_state is InitiativeLifecycleState.ACTIVE
    assert active.state.step_states["scope"] is StepState.COMPLETED
    assert active.state.step_states["implement"] in {
        StepState.IN_PROGRESS,
        StepState.AWAITING_VERIFICATION,
        StepState.AWAITING_ACCEPTANCE,
        StepState.COMPLETED,
    }

    assert {
        "change-scope",
        "release-requirements",
    } <= {item.artifact.role for item in artifacts}
    assert {
        "release/dogfood/change-scope.md",
        "release/dogfood/release-requirements.md",
    } <= {item.current_revision.path for item in artifacts}
    assert all(item.working_copy_matches for item in artifacts)

    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert events[0].previous_event_hash is None
    assert all(event.event_hash is not None for event in events)
    assert all(
        event.previous_event_hash == events[index - 1].event_hash
        for index, event in enumerate(events[1:], start=1)
    )
    assert events[-1].event_hash == active.state.journal_head_hash
    assert len(tuple(layout.acceptance_directory.glob("*.json"))) >= 1

    assert context.active_step.id == active.state.current_step_id
    assert context.active_step.state == active.state.step_states[context.active_step.id]
