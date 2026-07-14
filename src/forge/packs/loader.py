"""Bounded safe-YAML loading for bundled and repository-local data packs."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast

import yaml
from pydantic import ValidationError
from yaml.tokens import AliasToken, AnchorToken

from forge.contracts.configuration import ProjectConfiguration
from forge.contracts.packs import PackManifest
from forge.contracts.workflows import WorkflowDefinition
from forge.errors import ConfigurationError, ConflictError, SecurityError
from forge.packs.validation import ValidatedPack, validate_pack
from forge.security.paths import resolve_repository_path
from forge.storage.repository import RepositoryLayout

MAX_PACK_FILE_BYTES = 1_048_576
MAX_PACK_TOTAL_BYTES = 10_485_760
_EXECUTABLE_SUFFIXES = {
    ".bat",
    ".cmd",
    ".com",
    ".exe",
    ".js",
    ".ps1",
    ".py",
    ".sh",
}


def _load_yaml_mapping(path: Path) -> dict[object, object]:
    if path.is_symlink() or not path.is_file():
        raise SecurityError(f"Pack file is missing, irregular, or symbolic: {path}")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ConfigurationError(f"Cannot read pack file {path}: {error}") from error
    if len(raw) > MAX_PACK_FILE_BYTES:
        raise ConfigurationError(f"Pack file exceeds {MAX_PACK_FILE_BYTES} bytes: {path}")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ConfigurationError(f"Pack files must be UTF-8: {path}") from error
    try:
        scan_yaml = cast(
            "Callable[[str], Iterable[object]]",
            yaml.scan,  # pyright: ignore[reportUnknownMemberType]
        )
        if any(isinstance(token, (AliasToken, AnchorToken)) for token in scan_yaml(text)):
            raise ConfigurationError(f"Pack YAML must not contain anchors or aliases: {path}")
        value = cast(object, yaml.safe_load(text))
    except ConfigurationError:
        raise
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid safe YAML in pack file {path}: {error}") from error
    if not isinstance(value, dict):
        raise ConfigurationError(f"Pack YAML root must be a mapping: {path}")
    return cast("dict[object, object]", value)


def _validate_pack_files(root: Path, manifest: PackManifest) -> None:
    expected = {"manifest.yaml"}
    expected.update(
        f"workflows/{workflow_id}.yaml"
        for workflow_id in manifest.provided_workflow_ids
    )
    expected.update(manifest.template_paths)
    expected.update(manifest.explanation_paths)
    expected.update(manifest.data_resource_paths)
    actual: set[str] = set()
    total_bytes = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SecurityError(f"Pack content must not contain symbolic links: {path}")
        if path.is_dir():
            continue
        relative = path.relative_to(root).as_posix()
        actual.add(relative)
        if path.suffix.lower() in _EXECUTABLE_SUFFIXES:
            raise SecurityError(f"Data pack contains executable content: {relative}")
        total_bytes += path.stat().st_size
    if total_bytes > MAX_PACK_TOTAL_BYTES:
        raise ConfigurationError(f"Pack exceeds {MAX_PACK_TOTAL_BYTES} total bytes: {root}")
    undeclared = actual - expected
    missing = expected - actual
    if undeclared:
        raise SecurityError(f"Pack contains undeclared files: {sorted(undeclared)}")
    if missing:
        raise ConfigurationError(f"Pack is missing declared files: {sorted(missing)}")


def load_pack(path: Path, *, bundled: bool = False) -> ValidatedPack:
    try:
        root = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ConfigurationError(f"Pack directory does not exist: {path}") from error
    if not root.is_dir() or root.is_symlink():
        raise SecurityError(f"Pack location must be a regular directory: {path}")
    try:
        manifest = PackManifest.model_validate(_load_yaml_mapping(root / "manifest.yaml"))
    except ValidationError as error:
        raise ConfigurationError(f"Invalid pack manifest at {root}: {error}") from error
    _validate_pack_files(root, manifest)
    workflows: list[WorkflowDefinition] = []
    for workflow_id in manifest.provided_workflow_ids:
        workflow_path = root / "workflows" / f"{workflow_id}.yaml"
        try:
            workflow = WorkflowDefinition.model_validate(_load_yaml_mapping(workflow_path))
        except ValidationError as error:
            raise ConfigurationError(
                f"Invalid workflow {workflow_id!r} in pack {manifest.id}: {error}"
            ) from error
        workflows.append(workflow)
    pack = ValidatedPack(root, manifest, tuple(workflows), bundled)
    validate_pack(pack)
    return pack


def _bundled_pack_directories() -> tuple[Path, ...]:
    root = Path(__file__).with_name("bundled")
    if not root.is_dir():
        raise ConfigurationError("Bundled pack directory is missing from the installation")
    return tuple(sorted(path for path in root.iterdir() if path.is_dir()))


def available_packs(
    layout: RepositoryLayout,
    configuration: ProjectConfiguration,
) -> tuple[ValidatedPack, ...]:
    packs = [load_pack(path, bundled=True) for path in _bundled_pack_directories()]
    for relative in configuration.packs.local_paths:
        local = resolve_repository_path(layout.root, relative, must_exist=True)
        packs.append(load_pack(local))
    identities: set[tuple[str, str]] = set()
    for pack in packs:
        identity = (pack.manifest.id, pack.manifest.version)
        if identity in identities:
            raise ConflictError(f"Duplicate pack identity discovered: {identity[0]} {identity[1]}")
        identities.add(identity)
    return tuple(packs)


def find_pack(
    layout: RepositoryLayout,
    configuration: ProjectConfiguration,
    pack_id: str,
) -> ValidatedPack:
    matches = [
        pack
        for pack in available_packs(layout, configuration)
        if pack.manifest.id == pack_id
    ]
    if not matches:
        raise ConfigurationError(f"No validated pack named {pack_id!r} is available")
    if len(matches) > 1:
        versions = [pack.manifest.version for pack in matches]
        raise ConflictError(f"Pack {pack_id!r} is ambiguous across versions: {versions}")
    return matches[0]
