from pathlib import Path
from uuid import UUID

from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.contracts.packs import PackTrustState
from forge.contracts.state import InitiativeLifecycleState, StepState
from forge.contracts.verification import AcceptanceRecord, CheckResult, Claim, EvidencePacket
from forge.core.archival import load_archive
from forge.packs.loader import load_pack
from forge.packs.validation import calculate_pack_digest
from forge.storage.configuration import load_configuration
from forge.storage.objects import sha256_digest
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout

ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "packs" / "forge-production-release"
M6_INITIATIVE_ID = UUID("ea57c39e-98a9-475f-bb60-bb41f7e90f7c")
M7_INITIATIVE_ID = UUID("d57d380f-a51a-4786-a5e3-eb80d7888cb3")
SCOPE_ACCEPTANCE_ID = UUID("3c058e2a-2676-42e7-8239-1f5818c8eedf")

EXPECTED_STEPS = (
    "scope",
    "prepare",
    "verify-candidate",
    "approve-publication",
    "publish",
    "verify-publication",
    "retrospective",
    "closeout",
)


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


def test_production_release_pack_is_locked_data_only_and_complete() -> None:
    pack = load_pack(PACK_ROOT)
    workflow = pack.workflow()
    files = tuple(path for path in PACK_ROOT.rglob("*") if path.is_file())

    assert not pack.bundled
    assert pack.manifest.id == "forge-production-release"
    assert pack.manifest.version == workflow.version == "0.1.0"
    assert pack.manifest.declared_capability_ids == ()
    assert files
    assert all(path.suffix == ".yaml" for path in files)
    assert calculate_pack_digest(
        pack.manifest,
        pack.workflows,
        pack.resources,
    ) == pack.manifest.integrity_digest
    assert tuple(step.id for step in workflow.steps) == EXPECTED_STEPS
    assert workflow.required_evidence_classes == ("release-evidence",)

    prerequisites = {step.id: step.prerequisites for step in workflow.steps}
    outputs = {step.id: set(step.required_outputs) for step in workflow.steps}
    for step in workflow.steps:
        available: set[str] = set()
        for prerequisite in _prerequisite_steps(step.id, prerequisites):
            available.update(outputs[prerequisite])
        assert step.required_outputs
        assert set(step.required_inputs) <= available
        assert step.claim_requirements == ("outputs-produced",)
        assert step.check_requirements
        assert step.acceptance_requirements == ("owner-acceptance",)

    by_id = {step.id: step for step in workflow.steps}
    assert by_id["publish"].prerequisites == ("approve-publication",)
    assert "publication-authorization-record" in by_id["publish"].required_inputs
    assert by_id["verify-publication"].prerequisites == ("publish",)


def test_repository_configures_both_local_governance_packs() -> None:
    configuration = load_configuration(RepositoryLayout.at(ROOT).configuration_file)

    assert configuration.packs.local_paths == (
        "packs/forge-framework-change",
        "packs/forge-production-release",
    )


def test_increment_1_contract_records_approved_identity_and_stop_point() -> None:
    scope = (ROOT / "release" / "production-v1" / "scope.md").read_text(encoding="utf-8")
    contract = (
        ROOT / "release" / "production-v1" / "naming-and-channel-contract.md"
    ).read_text(encoding="utf-8")
    adr = (
        ROOT
        / "docs"
        / "adr"
        / "ADR-0059-production-v1-identity-version-and-publication-channels.md"
    ).read_text(encoding="utf-8")

    for content in (scope, contract, adr):
        assert "forge-governance" in content
        assert "owner" in content.lower()
    assert "awaiting_acceptance" in scope
    assert "not legal clearance" in adr
    assert "TestPyPI" in contract
    assert "trusted publishing" in contract
    assert "SPDX 2.3 JSON" in contract
    assert "no standalone package-signing key" in contract


def test_abandoned_public_m7_preserves_owner_accepted_scope() -> None:
    layout = RepositoryLayout.at(ROOT)
    archive = load_archive(layout, M7_INITIATIVE_ID)
    active = archive.active
    archived_layout = archive.layout
    artifacts = tuple(
        load_record(path, ArtifactRecord)
        for path in sorted(archived_layout.artifact_record_directory.glob("*.json"))
    )
    revisions = tuple(
        load_record(path, ArtifactRevision)
        for path in sorted(archived_layout.artifact_revision_directory.glob("*.json"))
    )
    current_revisions = {
        revision.artifact_id: revision
        for revision in revisions
        if active.state.current_artifact_revisions.get(revision.artifact_id)
        == revision.revision_number
    }
    current_by_role = {
        artifact.role: current_revisions[artifact.id] for artifact in artifacts
    }

    assert active.initiative.id == M7_INITIATIVE_ID
    assert tuple(
        reference.initiative_id
        for reference in active.initiative.predecessor_references
    ) == (M6_INITIATIVE_ID,)
    assert active.pack_manifest.id == "forge-production-release"
    assert active.pack_manifest.integrity_digest == (
        "sha256:fb23e9b8fb7692db9c277168175c18090f940b9f0a425bb27c80a1013afda497"
    )
    assert active.pack_trust.trust_state is PackTrustState.TRUSTED_DATA
    assert active.workflow.id == "production-v1-release"
    assert active.state.lifecycle_state is InitiativeLifecycleState.ABANDONED
    assert active.state.step_states["scope"] is StepState.COMPLETED
    assert {
        "production-v1-scope",
        "naming-channel-contract",
    } <= set(current_by_role)
    assert {
        "release/production-v1/scope.md",
        "release/production-v1/naming-and-channel-contract.md",
    } <= {revision.path for revision in current_by_role.values()}
    scope_revision_ids = {
        current_by_role[role].id
        for role in ("production-v1-scope", "naming-channel-contract")
    }
    assert all(
        sha256_digest((ROOT / revision.path).read_bytes()) == revision.content_digest
        for revision in current_by_role.values()
    )

    claims = tuple(
        load_record(path, Claim)
        for path in sorted(archived_layout.claim_directory.glob("*.json"))
    )
    checks = tuple(
        load_record(path, CheckResult)
        for path in sorted(archived_layout.check_directory.glob("*.json"))
    )
    evidence = tuple(
        load_record(path, EvidencePacket)
        for path in sorted(archived_layout.evidence_directory.glob("*.json"))
    )
    assert len(claims) == len(checks) == len(evidence) == 1
    assert claims[0].step_id == "scope"
    assert checks[0].check_id == "scope-and-channel-contract-reviewed"
    assert checks[0].outcome.value == "passed"
    assert set(checks[0].target_artifact_revision_ids) == scope_revision_ids
    assert evidence[0].claim_ids == (claims[0].id,)
    assert evidence[0].check_result_ids == (checks[0].id,)
    assert set(evidence[0].artifact_revision_ids) == scope_revision_ids
    acceptance_paths = tuple(archived_layout.acceptance_directory.glob("*.json"))
    assert len(acceptance_paths) == 1
    acceptance = load_record(acceptance_paths[0], AcceptanceRecord)
    assert acceptance.id == SCOPE_ACCEPTANCE_ID
    assert set(acceptance.accepted_artifact_revision_ids) == scope_revision_ids
    assert acceptance.accepted_check_result_ids == (checks[0].id,)
    assert acceptance.accepted_evidence_ids == (evidence[0].id,)
    assert "M7 Increments 1-8" in acceptance.accepted_scope
