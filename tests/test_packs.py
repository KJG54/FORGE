import shutil
from pathlib import Path

import pytest

from forge.errors import ConfigurationError, IntegrityError, SecurityError
from forge.packs.loader import load_pack

PACK_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "forge"
    / "packs"
    / "bundled"
    / "software-basic"
)


def test_bundled_software_pack_is_data_only_and_digest_valid() -> None:
    pack = load_pack(PACK_ROOT, bundled=True)

    assert pack.manifest.id == "software-basic"
    assert pack.manifest.declared_capability_ids == ()
    assert pack.workflow().id == "software-basic"
    assert [step.id for step in pack.workflow().steps] == [
        "discover",
        "plan",
        "execute",
        "verify",
        "review",
        "close",
    ]
    assert {"standard", "guided"} <= set(pack.workflow().explanation_content)


def test_pack_loader_rejects_undeclared_executable_content(tmp_path: Path) -> None:
    copied = tmp_path / "pack"
    shutil.copytree(PACK_ROOT, copied)
    (copied / "payload.py").write_text("raise SystemExit\n", encoding="utf-8")

    with pytest.raises(SecurityError, match="executable content"):
        load_pack(copied)


def test_pack_loader_rejects_changed_content_with_stale_digest(tmp_path: Path) -> None:
    copied = tmp_path / "pack"
    shutil.copytree(PACK_ROOT, copied)
    workflow = copied / "workflows" / "software-basic.yaml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "name: Software Basic",
            "name: Modified Software Basic",
        ),
        encoding="utf-8",
    )

    with pytest.raises(IntegrityError, match="integrity digest mismatch"):
        load_pack(copied)


def test_pack_loader_rejects_yaml_anchors_and_aliases(tmp_path: Path) -> None:
    copied = tmp_path / "pack"
    shutil.copytree(PACK_ROOT, copied)
    manifest = copied / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "id: software-basic",
            "id: &pack_id software-basic",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="anchors or aliases"):
        load_pack(copied)


def test_pack_resources_are_refused_until_their_bytes_are_lockable(tmp_path: Path) -> None:
    copied = tmp_path / "pack"
    shutil.copytree(PACK_ROOT, copied)
    resource = copied / "notes.txt"
    resource.write_text("declarative data\n", encoding="utf-8")
    manifest = copied / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "data_resource_paths: []",
            "data_resource_paths: [notes.txt]",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="included in the lock digest"):
        load_pack(copied)
