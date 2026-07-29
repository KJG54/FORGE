from pathlib import Path
from uuid import UUID

from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.contracts.packs import PackTrustState
from forge.contracts.state import InitiativeLifecycleState, StepState
from forge.core.archival import load_archive
from forge.packs.loader import load_pack
from forge.storage.configuration import load_configuration
from forge.storage.objects import sha256_digest
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout

ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "packs" / "forge-framework-change"
M6_INITIATIVE_ID = UUID("ea57c39e-98a9-475f-bb60-bb41f7e90f7c")


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


def test_repository_dogfood_archive_is_healthy_bound_and_owner_accepted() -> None:
    layout = RepositoryLayout.at(ROOT)
    configuration = load_configuration(layout.configuration_file)
    archive = load_archive(layout, M6_INITIATIVE_ID)
    active = archive.active
    events = archive.events
    artifacts = tuple(
        load_record(path, ArtifactRecord)
        for path in sorted(archive.layout.artifact_record_directory.glob("*.json"))
    )
    revisions = tuple(
        load_record(path, ArtifactRevision)
        for path in sorted(archive.layout.artifact_revision_directory.glob("*.json"))
    )
    current_revisions = tuple(
        revision
        for revision in revisions
        if active.state.current_artifact_revisions.get(revision.artifact_id)
        == revision.revision_number
    )

    assert configuration.behavior.require_clean_git_for_close
    assert "packs/forge-framework-change" in configuration.packs.local_paths
    assert active.pack_manifest.id == "forge-framework-change"
    assert active.pack_trust.trust_state is PackTrustState.TRUSTED_DATA
    assert active.workflow.id == "framework-change"
    assert active.state.lifecycle_state is InitiativeLifecycleState.CLOSED
    assert set(active.state.step_states.values()) == {StepState.COMPLETED}
    assert archive.closure is not None
    assert archive.abandonment is None
    assert not archive.manifest.preliminary

    assert {
        "change-scope",
        "release-requirements",
        "verification-report",
        "friction-report",
        "residual-risk-report",
        "release-readiness-record",
        "lessons",
    } <= {item.role for item in artifacts}
    assert {
        "release/dogfood/change-scope.md",
        "release/dogfood/release-requirements.md",
        "release/dogfood/verification-report.md",
        "release/dogfood/friction-report.md",
        "release/dogfood/residual-risk-report.md",
        "docs/milestones/m6-report.md",
        "release/dogfood/lessons.md",
    } <= {item.path for item in current_revisions}
    assert all(
        sha256_digest((ROOT / revision.path).read_bytes()) == revision.content_digest
        for revision in current_revisions
    )

    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert events[0].previous_event_hash is None
    assert all(event.event_hash is not None for event in events)
    assert all(
        event.previous_event_hash == events[index - 1].event_hash
        for index, event in enumerate(events[1:], start=1)
    )
    assert events[-1].event_hash == active.state.journal_head_hash
    assert events[-1].event_type == "initiative-closed"
    assert len(tuple(archive.layout.acceptance_directory.glob("*.json"))) == len(
        active.workflow.steps
    )
