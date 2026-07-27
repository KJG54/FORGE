"""Bounded safe-YAML loading for bundled and repository-local data packs."""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast

import yaml
from pydantic import ValidationError
from yaml.tokens import AliasToken, AnchorToken

from forge.contracts.configuration import ProjectConfiguration
from forge.contracts.packs import PackManifest
from forge.contracts.workflows import WorkflowDefinition
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.packs.validation import (
    PackResource,
    PackResourceKind,
    ValidatedPack,
    validate_pack,
)
from forge.security.paths import resolve_repository_path
from forge.storage.atomic import atomic_write_bytes, sync_directory
from forge.storage.repository import RepositoryLayout

MAX_PACK_FILE_BYTES = 1_048_576
MAX_PACK_TOTAL_BYTES = 10_485_760
MAX_PACK_RESOURCE_BYTES = 1_048_576
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


def _template_resource(path: Path, relative: str) -> PackResource:
    if path.is_symlink() or not path.is_file():
        raise SecurityError(f"Pack template is missing, irregular, or symbolic: {path}")
    if path.suffix.lower() in _EXECUTABLE_SUFFIXES:
        raise SecurityError(f"Pack template has an executable suffix: {relative}")
    try:
        content = path.read_bytes()
    except OSError as error:
        raise ConfigurationError(f"Cannot read pack template {path}: {error}") from error
    if len(content) > MAX_PACK_RESOURCE_BYTES:
        raise ConfigurationError(
            f"Pack template exceeds {MAX_PACK_RESOURCE_BYTES} bytes: {path}"
        )
    try:
        content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ConfigurationError(f"Pack templates must be UTF-8 text: {path}") from error
    return PackResource(
        path=relative,
        kind=PackResourceKind.TEMPLATE,
        content=content,
        content_digest=f"sha256:{hashlib.sha256(content).hexdigest()}",
    )


def _load_template_resources(
    root: Path,
    paths: tuple[str, ...],
) -> tuple[PackResource, ...]:
    resources: list[PackResource] = []
    total_bytes = 0
    for relative in paths:
        resource = _template_resource(root / relative, relative)
        total_bytes += len(resource.content)
        if total_bytes > MAX_PACK_TOTAL_BYTES:
            raise ConfigurationError(
                f"Pack template resources exceed {MAX_PACK_TOTAL_BYTES} aggregate bytes: {root}"
            )
        resources.append(resource)
    return tuple(resources)


def load_pack_resources(root: Path, manifest: PackManifest) -> tuple[PackResource, ...]:
    """Load declared source-pack templates after the complete inventory is validated."""
    return _load_template_resources(root, manifest.template_paths)


def _expected_resource_directories(paths: tuple[str, ...]) -> set[str]:
    expected: set[str] = set()
    for relative in paths:
        parent = Path(relative).parent
        while parent != Path("."):
            expected.add(parent.as_posix())
            parent = parent.parent
    return expected


def load_locked_pack_resources(
    root: Path,
    manifest: PackManifest,
) -> tuple[PackResource, ...]:
    """Load exact governed template copies without consulting the source pack."""
    try:
        expected_files = set(manifest.template_paths)
        if not expected_files:
            if root.exists():
                raise ConfigurationError(
                    "Locked pack has no declared templates but pack-resources exists"
                )
            return ()
        if root.is_symlink() or not root.is_dir():
            raise ConfigurationError(
                "Locked pack-resources directory is missing or unsafe"
            )
        expected_directories = _expected_resource_directories(manifest.template_paths)
        actual_files: set[str] = set()
        actual_directories: set[str] = set()
        for candidate in root.rglob("*"):
            if candidate.is_symlink():
                raise SecurityError(
                    f"Locked pack resources contain a symbolic link: {candidate}"
                )
            relative = candidate.relative_to(root).as_posix()
            if candidate.is_dir():
                actual_directories.add(relative)
            elif candidate.is_file():
                actual_files.add(relative)
            else:
                raise ConfigurationError(
                    f"Locked pack resources contain an irregular entry: {candidate}"
                )
        if actual_files != expected_files or actual_directories != expected_directories:
            raise ConfigurationError(
                "Locked pack resource inventory does not match the exact declared template paths"
            )
        return _load_template_resources(root, manifest.template_paths)
    except (ConfigurationError, SecurityError) as error:
        raise IntegrityError(f"Invalid locked pack resources: {error}") from error


def persist_locked_pack_resources(
    destination: Path,
    pack: ValidatedPack,
) -> bool:
    """Persist exact resource bytes before the initiative creation event commits."""
    if not pack.resources:
        return False
    if destination.exists():
        raise ConflictError(f"Refusing to overwrite locked pack resources: {destination}")
    try:
        destination.mkdir()
        sync_directory(destination.parent)
        for resource in pack.resources:
            target = destination / resource.path
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_bytes(target, resource.content)
        restored = load_locked_pack_resources(destination, pack.manifest)
        if restored != pack.resources:
            raise ConfigurationError(
                "Locked pack resources did not reproduce the validated source bytes"
            )
        return True
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def discard_locked_pack_resources(destination: Path) -> None:
    """Remove only a pre-commit resource tree created by initiative creation."""
    if destination.exists():
        shutil.rmtree(destination)


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
    resources = load_pack_resources(root, manifest)
    pack = ValidatedPack(
        root,
        manifest,
        tuple(workflows),
        resources,
        bundled,
    )
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
