from pathlib import Path
from uuid import UUID

from forge.contracts.packs import PackTrustState
from forge.contracts.state import InitiativeLifecycleState
from forge.core.archival import load_archive
from forge.core.lifecycle import load_active_initiative
from forge.storage.repository import RepositoryLayout

ROOT = Path(__file__).resolve().parents[1]
M6_INITIATIVE_ID = UUID("ea57c39e-98a9-475f-bb60-bb41f7e90f7c")
PUBLIC_M7_INITIATIVE_ID = UUID("d57d380f-a51a-4786-a5e3-eb80d7888cb3")
LOCAL_V1_INITIATIVE_ID = UUID("26c0c628-cc77-478c-b77b-0c1d703891ac")


def test_local_v1_contract_supersedes_public_execution_without_rewriting_history() -> None:
    adr = (
        ROOT
        / "docs"
        / "history"
        / "adr"
        / "ADR-0061-local-production-v1-conversational-candidate.md"
    ).read_text(encoding="utf-8")
    scope = (
        ROOT / "release" / "local-production-v1" / "change-scope.md"
    ).read_text(encoding="utf-8")
    requirements = (
        ROOT / "release" / "local-production-v1" / "release-requirements.md"
    ).read_text(encoding="utf-8")

    assert "**Status:** Accepted" in adr
    assert "supersedes ADR-0059" in adr
    assert "retains ADR-0060" in adr
    assert "No public tag" in adr
    assert "same-user" in adr
    assert "final Production-v1 acceptance" in scope
    assert "PyPI or TestPyPI publication" in scope
    assert "one byte-identical local wheel" in scope
    assert "65,536" in requirements
    assert "forge agent protocol" in requirements
    assert "forge recap" in requirements
    assert "forge successor brief --archive <id>" in requirements
    assert "Recorded ->" in requirements
    assert "Means    ->" in requirements


def test_local_v1_successor_preserves_distinct_predecessor_outcomes() -> None:
    layout = RepositoryLayout.at(ROOT)
    active = load_active_initiative(layout)
    m6 = load_archive(layout, M6_INITIATIVE_ID)
    public_m7 = load_archive(layout, PUBLIC_M7_INITIATIVE_ID)

    assert active.initiative.id == LOCAL_V1_INITIATIVE_ID
    assert {
        reference.initiative_id
        for reference in active.initiative.predecessor_references
    } == {M6_INITIATIVE_ID, PUBLIC_M7_INITIATIVE_ID}
    assert active.pack_manifest.id == "forge-framework-change"
    assert active.workflow.id == "framework-change"
    assert active.pack_trust.trust_state is PackTrustState.TRUSTED_DATA
    assert active.state.lifecycle_state is InitiativeLifecycleState.ACTIVE
    assert m6.active.state.lifecycle_state is InitiativeLifecycleState.CLOSED
    assert public_m7.active.state.lifecycle_state is InitiativeLifecycleState.ABANDONED
    assert m6.manifest.archive_digest == (
        "sha256:5a25afde013b3013752b97db88587eb6808cd583ddd05439a293b59085750325"
    )
    assert public_m7.manifest.archive_digest == (
        "sha256:a27c24c252a01cd6c5b5ba07860dbb1217de3d8f3b7c79897415cdc5123900b0"
    )
