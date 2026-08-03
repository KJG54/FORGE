from __future__ import annotations

import hashlib
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import cast

import pytest

from tools.local_candidate import (
    CandidateError,
    inspect_candidate,
    validate_manifest_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_candidate_artifacts(directory: Path) -> None:
    wheel = directory / "forge_governance-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "forge_governance-1.0.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: forge-governance\nVersion: 1.0.0\n",
        )
    sdist = directory / "forge_governance-1.0.0.tar.gz"
    payload = b"Metadata-Version: 2.1\nName: forge-governance\nVersion: 1.0.0\n"
    with tarfile.open(sdist, "w:gz") as archive:
        info = tarfile.TarInfo("forge_governance-1.0.0/PKG-INFO")
        info.size = len(payload)
        archive.addfile(info, BytesIO(payload))


def test_candidate_inspection_binds_exact_names_metadata_and_bytes(tmp_path: Path) -> None:
    _write_candidate_artifacts(tmp_path)

    report = inspect_candidate(tmp_path)

    assert report["distribution"] == "forge-governance"
    assert report["version"] == "1.0.0"
    artifacts = report["artifacts"]
    assert {entry["type"] for entry in artifacts} == {"wheel", "sdist"}
    for entry in artifacts:
        path = tmp_path / entry["filename"]
        assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert entry["size_bytes"] == path.stat().st_size


def test_candidate_inspection_refuses_extra_distribution(tmp_path: Path) -> None:
    _write_candidate_artifacts(tmp_path)
    (tmp_path / "forge_governance-1.0.0-1-py3-none-any.whl").write_bytes(b"other")

    with pytest.raises(CandidateError, match="Expected only"):
        inspect_candidate(tmp_path)


def test_tracked_candidate_identity_is_internally_consistent() -> None:
    manifest = validate_manifest_contract()

    assert manifest["status"] == "unpublished-local-candidate"
    assert manifest["publication"] == {"authorized": False, "tag_created": False}
    validation = cast("dict[str, object]", manifest["validation"])
    assert validation["complete_phase"] == "L8 candidate integration"
    assert validation["next_phase"] == "L9 candidate validation"


def test_owner_guide_covers_every_required_local_journey() -> None:
    guide = (
        ROOT / "release" / "local-production-v1" / "owner-test-guide.md"
    ).read_text(encoding="utf-8")
    for number, journey in enumerate(
        (
            "New empty software project",
            "Existing documentation project",
            "Research project",
            "Warm resume after a day or more",
            "Formal pause/resume with working drift",
            "Rejection after claim",
            "Mid-milestone plan revision",
            "DoD scope amendment",
            "Interrupted recovery",
            "Abandonment",
            "Closure and archive",
            "New-agent successor without chat",
            "Backup and restore on the actual machine",
        ),
        start=1,
    ):
        assert f"{number}. **{journey}:**" in guide


def test_current_candidate_docs_do_not_authorize_publication() -> None:
    documents = (
        ROOT / "README.md",
        ROOT / "docs" / "installation.md",
        ROOT / "release" / "local-production-v1" / "README.md",
        ROOT / "release" / "local-production-v1" / "known-limitations.md",
        ROOT / "release" / "local-production-v1" / "residual-risks.md",
        ROOT / "release" / "local-production-v1" / "owner-test-guide.md",
    )
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in documents)

    assert "unpublished local" in combined
    assert "does not define or authorize a public release" in combined
    assert "extended owner testing" in combined
