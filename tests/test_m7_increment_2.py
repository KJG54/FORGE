from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from forge import __version__
from forge.contracts import CONTRACT_MODELS
from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.contracts.base import SCHEMA_VERSION
from forge.contracts.decisions import DecisionRecord, DecisionStatus
from forge.contracts.state import StepState
from forge.core.archival import load_archive
from forge.schemas.export import schema_bundle
from forge.storage.objects import sha256_digest
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout
from tools.version_consistency import VERSION_CONTRACT, validate_version_consistency

ROOT = Path(__file__).resolve().parents[1]
M7_INITIATIVE_ID = UUID("d57d380f-a51a-4786-a5e3-eb80d7888cb3")
PREPARE_RUN_ID = UUID("0fca736a-c6e3-46d1-99db-b2b779ec9596")
COMPATIBILITY_REVISION_ID = UUID("cfe54f78-dbd5-4627-9bc2-e19383f5059d")
VERSION_DECISION_ID = UUID("49bac69f-a2a4-4a70-aa5d-64ec1206a1ad")


def test_frozen_production_v1_contract_matches_every_current_version_boundary() -> None:
    report = validate_version_consistency()

    assert report["status"] == "passed"
    assert report["version"] == __version__ == "1.0.0"
    assert report["contract_schema_version"] == SCHEMA_VERSION == "1.0"
    # 51 -> 53: InterviewGuidanceGroup and PhaseGuidance joined the public contract
    # surface with the additive profile-aware guidance fields, following the existing
    # Gate precedent for nested workflow models. The v1.0.0 distribution is still
    # candidate-unpublished, so this baseline is a candidate pin rather than a shipped
    # compatibility promise.
    assert report["public_model_count"] == len(CONTRACT_MODELS) == 53
    assert report["wheel_filename"] == "forge_governance-1.0.0-py3-none-any.whl"
    assert report["sdist_filename"] == "forge_governance-1.0.0.tar.gz"
    assert report["bundled_packs"] == [
        "project-basic",
        "research-basic",
        "software-basic",
    ]
    assert report["repository_local_packs"] == [
        "forge-framework-change",
        "forge-production-release",
    ]
    assert report["historical_local_candidate_manifest"] == (
        "validated-historical-artifact-only"
    )


def test_schema_index_binds_distribution_contract_and_pack_compatibility() -> None:
    index = json.loads(schema_bundle()["index.json"].decode("utf-8"))

    assert index["forge_version"] == "1.0.0"
    assert index["schema_version"] == "1.0"
    assert index["pack_schema_compatibility"] == "forge-contracts-1"
    assert set(index["schemas"]) == set(CONTRACT_MODELS)


def test_version_freeze_preserves_historical_alpha_evidence() -> None:
    dogfood = (ROOT / "release" / "dogfood" / "verification-report.md").read_text(
        encoding="utf-8"
    )
    frozen_event = (
        ROOT
        / "tests"
        / "fixtures"
        / "compatibility"
        / "m1-unhashed-events.jsonl"
    ).read_text(encoding="utf-8")
    contract = json.loads(VERSION_CONTRACT.read_text(encoding="utf-8"))

    assert "forge_governance-0.1.0a0" in dogfood
    assert "forge 0.1.0a0" in frozen_event
    assert contract["distribution"]["version"] == "1.0.0"
    assert contract["persisted_contracts"]["schema_versions"] == ["1.0"]


def test_compatibility_statement_distinguishes_candidate_from_publication() -> None:
    statement = (
        ROOT / "release" / "production-v1" / "compatibility-statement.md"
    ).read_text(encoding="utf-8")

    assert "candidate" in statement
    assert "is not evidence that Production v1 has been released" in statement
    assert "requires a new distribution major version" in statement
    assert "Exact help, status, diagnostic," in statement
    assert "error prose is not a stable machine interface" in statement


def test_abandoned_public_m7_preserves_unaccepted_increment_2_output() -> None:
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
    compatibility = current_by_role["compatibility-statement"]

    assert active.initiative.id == M7_INITIATIVE_ID
    assert active.state.step_states["scope"] is StepState.COMPLETED
    assert active.state.step_states["prepare"] is StepState.BLOCKED
    assert active.state.active_run_ids == ()
    assert (
        archived_layout.governed_run_directory / f"{PREPARE_RUN_ID}.json"
    ).is_file()
    assert compatibility.id == COMPATIBILITY_REVISION_ID
    assert compatibility.path == "release/production-v1/compatibility-statement.md"
    assert sha256_digest((ROOT / compatibility.path).read_bytes()) == (
        compatibility.content_digest
    )
    assert {
        role
        for role in current_by_role
        if role in active.workflow.steps[1].required_outputs
    } == {"compatibility-statement"}
    decision_paths = tuple(archived_layout.decision_directory.glob("*.json"))
    assert len(decision_paths) == 1
    decision = load_record(decision_paths[0], DecisionRecord)
    assert decision.id == VERSION_DECISION_ID
    assert decision.decision_type == "production-v1-version-contract"
    assert decision.status is DecisionStatus.ACTIVE
    assert decision.affected_record_ids == (COMPATIBILITY_REVISION_ID,)
    assert set(decision.bound_digests) == {
        "sha256:c325414d4cdef1c74c33e520008bbca43ebbc02471616315aaf813f81faaa8a1",
        "sha256:a6eb13ba6b678b6c29d590804c9474fd37a8502b694c2437866ad6c060c3a47f",
        "sha256:eeb28e9903019b0603bbcec26ec70435c47e73fbd7322bb49665f3da8f98c89d",
    }
    assert len(tuple(archived_layout.acceptance_directory.glob("*.json"))) == 1
