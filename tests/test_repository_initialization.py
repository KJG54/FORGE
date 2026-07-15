import os
from pathlib import Path

import pytest

from forge.contracts.state import ExplanationProfile
from forge.errors import ConfigurationError, ConflictError, SecurityError
from forge.storage.configuration import load_configuration
from forge.storage.repository import GITIGNORE_BLOCK, discover_repository, initialize_repository


def test_init_preserves_existing_content_and_bootstraps_owner(tmp_path: Path) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    unrelated = repository / "project.txt"
    unrelated.write_bytes(b"unchanged\r\n")
    gitignore = repository / ".gitignore"
    gitignore.write_bytes(b"dist/\r\ncustom-rule")

    result = initialize_repository(repository, owner_display_name="Repository Owner")

    assert result.created is True
    assert result.gitignore_changed is True
    assert unrelated.read_bytes() == b"unchanged\r\n"
    assert gitignore.read_bytes().startswith(b"dist/\r\ncustom-rule\r\n")
    assert gitignore.read_bytes().endswith(b".forge/local/\r\n")
    assert b"!/forge.yaml\r\n" in gitignore.read_bytes()
    assert b"!/.forge/**\r\n" in gitignore.read_bytes()
    assert result.configuration.owner.display_name == "Repository Owner"
    assert result.configuration.behavior.explanation_profile is ExplanationProfile.STANDARD
    assert load_configuration(repository / "forge.yaml") == result.configuration

    for directory in result.layout.required_directories:
        assert directory.is_dir()
    assert not any(result.layout.active_directory.iterdir())
    assert not (result.layout.active_directory / "events.jsonl").exists()
    assert not (result.layout.active_directory / "state.json").exists()


def test_init_is_idempotent_and_does_not_replace_identity(tmp_path: Path) -> None:
    first = initialize_repository(tmp_path, owner_display_name="First Owner")
    config_bytes = first.layout.configuration_file.read_bytes()
    gitignore_bytes = (tmp_path / ".gitignore").read_bytes()

    second = initialize_repository(tmp_path, owner_display_name="Different Owner")

    assert second.created is False
    assert second.gitignore_changed is False
    assert second.configuration.project_id == first.configuration.project_id
    assert second.configuration.owner.id == first.configuration.owner.id
    assert second.configuration.owner.display_name == "First Owner"
    assert first.layout.configuration_file.read_bytes() == config_bytes
    assert (tmp_path / ".gitignore").read_bytes() == gitignore_bytes


def test_init_respects_existing_equivalent_gitignore_rule(tmp_path: Path) -> None:
    gitignore = tmp_path / ".gitignore"
    policy = "\n".join(GITIGNORE_BLOCK) + "\n"
    gitignore.write_text(policy, encoding="utf-8")
    result = initialize_repository(tmp_path, owner_display_name="Owner")
    assert result.gitignore_changed is False
    assert gitignore.read_text(encoding="utf-8") == policy


def test_init_upgrades_legacy_local_only_gitignore_rule(tmp_path: Path) -> None:
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("/.forge/local/\n", encoding="utf-8")

    result = initialize_repository(tmp_path, owner_display_name="Owner")

    assert result.gitignore_changed is True
    assert gitignore.read_text(encoding="utf-8").startswith("/.forge/local/\n")
    assert "!/forge.yaml\n" in gitignore.read_text(encoding="utf-8")


def test_init_refuses_to_adopt_nonempty_forge_directory(tmp_path: Path) -> None:
    forge_directory = tmp_path / ".forge"
    forge_directory.mkdir()
    existing = forge_directory / "unrelated.txt"
    existing.write_text("preserve me", encoding="utf-8")

    with pytest.raises(ConflictError, match="Refusing to adopt"):
        initialize_repository(tmp_path, owner_display_name="Owner")
    assert existing.read_text(encoding="utf-8") == "preserve me"
    assert not (tmp_path / "forge.yaml").exists()


def test_discovery_finds_nearest_initialized_repository(tmp_path: Path) -> None:
    initialize_repository(tmp_path, owner_display_name="Owner")
    child = tmp_path / "src" / "nested"
    child.mkdir(parents=True)
    assert discover_repository(child).root == tmp_path.resolve()


def test_configuration_rejects_unknown_and_future_fields(tmp_path: Path) -> None:
    configuration = tmp_path / "forge.yaml"
    configuration.write_text("schema_version: '2.0'\nunknown: true\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Invalid FORGE configuration"):
        load_configuration(configuration)


def test_configuration_rejects_recognizable_credentials(tmp_path: Path) -> None:
    result = initialize_repository(tmp_path, owner_display_name="Owner")
    text = result.layout.configuration_file.read_text(encoding="utf-8")
    result.layout.configuration_file.write_text(
        text.replace(
            "preferred_adapter: null",
            "preferred_adapter: ghp_abcdefghijklmnopqrstuvwxyz",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="appears to contain a credential"):
        load_configuration(result.layout.configuration_file)


def test_configuration_rejects_yaml_anchors_and_aliases(tmp_path: Path) -> None:
    configuration = tmp_path / "forge.yaml"
    configuration.write_text(
        "schema_version: '1.0'\nproject_id: &id value\nowner:\n  id: *id\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="must not contain YAML anchors or aliases"):
        load_configuration(configuration)


def test_init_does_not_write_recognizable_credentials(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="Refusing to write a recognizable credential"):
        initialize_repository(
            tmp_path,
            owner_display_name="ghp_abcdefghijklmnopqrstuvwxyz",
        )
    assert not (tmp_path / "forge.yaml").exists()


def test_discovery_rejects_replaced_managed_directory_symlink(tmp_path: Path) -> None:
    result = initialize_repository(tmp_path, owner_display_name="Owner")
    outside = tmp_path / "outside"
    outside.mkdir()
    result.layout.active_directory.rmdir()
    try:
        os.symlink(outside, result.layout.active_directory, target_is_directory=True)
    except OSError as error:
        result.layout.active_directory.mkdir()
        pytest.skip(f"symlink creation is unavailable: {error}")

    with pytest.raises(SecurityError, match="symbolic link"):
        discover_repository(tmp_path)


def test_init_validates_packs_before_writing_repository_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_packs(*_: object) -> tuple[object, ...]:
        raise ConfigurationError("simulated invalid bundled pack")

    monkeypatch.setattr("forge.packs.loader.available_packs", reject_packs)

    with pytest.raises(ConfigurationError, match="invalid bundled pack"):
        initialize_repository(tmp_path, owner_display_name="Owner")
    assert not (tmp_path / "forge.yaml").exists()
    assert not (tmp_path / ".forge").exists()
    assert not (tmp_path / ".gitignore").exists()
