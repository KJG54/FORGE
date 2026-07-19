"""Bounded, non-executing staging for untrusted result bundles."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import ValidationError

from forge.contracts.agents import AgentResult, ReturnedFile
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.security.paths import normalize_repository_path, resolve_repository_path
from forge.security.secrets import screen_governed_content
from forge.storage.atomic import atomic_write_bytes
from forge.storage.configuration import load_configuration
from forge.storage.objects import sha256_digest
from forge.storage.records import MAX_RECORD_BYTES
from forge.storage.repository import RepositoryLayout


@dataclass(frozen=True)
class StagedFile:
    declaration: ReturnedFile
    staged_path: Path
    digest: str
    byte_size: int


@dataclass(frozen=True)
class StagedResult:
    result: AgentResult
    directory: Path
    manifest_path: Path
    manifest_digest: str
    files: tuple[StagedFile, ...]


def resolve_import_target(layout: RepositoryLayout, relative_path: str) -> Path:
    """Resolve a target while refusing every symbolic-link path component."""

    normalized = normalize_repository_path(relative_path)
    cursor = layout.root
    for part in normalized.split("/"):
        cursor /= part
        if cursor.is_symlink():
            raise SecurityError(f"Import target path contains a symbolic link: {normalized}")
    return resolve_repository_path(layout.root, normalized, must_exist=False)


def _read_manifest(path: Path) -> bytes:
    if path.is_symlink():
        raise SecurityError(f"Result manifest is a symbolic link: {path}")
    if not path.is_file():
        raise ConfigurationError(f"Result manifest is not a regular file: {path}")
    try:
        size = path.stat().st_size
        if size > MAX_RECORD_BYTES:
            raise ConfigurationError(
                f"Result manifest exceeds the {MAX_RECORD_BYTES}-byte schema limit"
            )
        raw = path.read_bytes()
        if len(raw) > MAX_RECORD_BYTES:
            raise ConfigurationError(
                f"Result manifest exceeds the {MAX_RECORD_BYTES}-byte schema limit"
            )
        return raw
    except OSError as error:
        raise IntegrityError(f"Cannot read result manifest {path}: {error}") from error


def _parse_manifest(raw: bytes, path: Path) -> AgentResult:
    try:
        decoded = json.loads(raw)
        return AgentResult.model_validate(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
        raise ConfigurationError(f"Invalid AgentResult manifest {path}: {error}") from error


def _failed_staging(layout: RepositoryLayout, raw: bytes) -> None:
    configuration = load_configuration(layout.configuration_file)
    if not configuration.imports.preserve_failed_staging:
        return
    directory = layout.import_staging_directory / f"failed-{uuid4()}"
    try:
        directory.mkdir()
        atomic_write_bytes(directory / "manifest.json", raw)
    except OSError as error:
        raise IntegrityError(f"Cannot preserve failed import staging: {error}") from error


def _bundle_inventory(bundle_root: Path, manifest_path: Path) -> set[str]:
    inventory: set[str] = set()
    for path in bundle_root.rglob("*"):
        if path.is_symlink():
            raise SecurityError(f"Result bundle contains a symbolic link: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise SecurityError(f"Result bundle contains a non-regular file: {path}")
        if path == manifest_path:
            continue
        inventory.add(path.relative_to(bundle_root).as_posix())
    return inventory


def _source_file(bundle_root: Path, source_path: str) -> Path:
    normalized = normalize_repository_path(source_path)
    cursor = bundle_root
    for part in normalized.split("/"):
        cursor /= part
        if cursor.is_symlink():
            raise SecurityError(f"Returned source path contains a symbolic link: {normalized}")
    try:
        resolved = cursor.resolve(strict=True)
        root = bundle_root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise SecurityError(f"Returned source path cannot be resolved: {normalized}") from error
    if not resolved.is_relative_to(root):
        raise SecurityError(f"Returned source path escapes its bundle: {normalized}")
    if not resolved.is_file():
        raise SecurityError(f"Returned source path is not a regular file: {normalized}")
    return resolved


def _safe_stage_parent(root: Path, relative_path: str) -> Path:
    parent = (root / relative_path).parent
    cursor = root
    relative_parent = parent.relative_to(root)
    for part in relative_parent.parts:
        cursor /= part
        if cursor.is_symlink():
            raise SecurityError(f"Staging path contains a symbolic link: {cursor}")
        if cursor.exists() and not cursor.is_dir():
            raise ConflictError(f"Staging parent is not a directory: {cursor}")
        if not cursor.exists():
            cursor.mkdir()
    return parent


def _load_existing_stage(
    layout: RepositoryLayout,
    result: AgentResult,
    raw_manifest: bytes,
) -> StagedResult | None:
    configuration = load_configuration(layout.configuration_file)
    directory = layout.import_staging_directory / str(result.id)
    if not directory.exists():
        return None
    if directory.is_symlink() or not directory.is_dir():
        raise SecurityError(f"Import staging is unsafe: {directory}")
    manifest_path = directory / "manifest.json"
    existing_raw = _read_manifest(manifest_path)
    if existing_raw != raw_manifest:
        raise ConflictError(
            f"Staging for result {result.id} exists with a different manifest"
        )
    inventory_path = directory / "inventory.json"
    inventory_raw = _read_manifest(inventory_path)
    try:
        recorded_inventory = json.loads(inventory_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IntegrityError(f"Invalid staged import inventory: {inventory_path}") from error
    staged_files: list[StagedFile] = []
    calculated_inventory: list[dict[str, object]] = []
    total_bytes = 0
    for returned in result.returned_files:
        staged_path = directory / "files" / returned.source_path
        if staged_path.is_symlink() or not staged_path.is_file():
            raise IntegrityError(f"Staged result file is missing or unsafe: {staged_path}")
        try:
            size = staged_path.stat().st_size
            if size > configuration.imports.max_file_bytes:
                raise IntegrityError(f"Staged result file exceeds configured limit: {staged_path}")
            content = staged_path.read_bytes()
        except OSError as error:
            raise IntegrityError(
                f"Cannot read staged result file {staged_path}: {error}"
            ) from error
        digest = sha256_digest(content)
        total_bytes += len(content)
        if (
            len(content) > configuration.imports.max_file_bytes
            or total_bytes > configuration.imports.max_total_bytes
        ):
            raise IntegrityError(f"Staged result files exceed configured limits: {directory}")
        if returned.declared_digest is not None and returned.declared_digest != digest:
            raise IntegrityError(f"Staged result digest no longer matches: {staged_path}")
        resolve_import_target(layout, returned.proposed_target_path)
        screen_governed_content(
            returned.proposed_target_path,
            content,
            secret_path_patterns=configuration.security.secret_path_patterns,
        )
        staged_files.append(StagedFile(returned, staged_path, digest, len(content)))
        calculated_inventory.append(
            {
                "byte_size": len(content),
                "digest": digest,
                "source_path": returned.source_path,
                "target_path": returned.proposed_target_path,
            }
        )
    if recorded_inventory != calculated_inventory:
        raise IntegrityError(f"Staged result inventory no longer matches: {directory}")
    return StagedResult(
        result,
        directory,
        manifest_path,
        sha256_digest(raw_manifest),
        tuple(staged_files),
    )


def stage_result(
    layout: RepositoryLayout,
    manifest_path: Path,
    *,
    expected_source_id: UUID | None = None,
) -> StagedResult:
    """Validate and copy one untrusted result bundle into local staging without execution."""

    configuration = load_configuration(layout.configuration_file)
    raw = _read_manifest(manifest_path)
    try:
        screen_governed_content(
            "agent-result.json",
            raw,
            secret_path_patterns=configuration.security.secret_path_patterns,
        )
        result = _parse_manifest(raw, manifest_path)
    except (ConfigurationError, SecurityError):
        _failed_staging(layout, raw)
        raise
    if (
        expected_source_id is not None
        and result.source_run_or_handoff_id != expected_source_id
    ):
        _failed_staging(layout, raw)
        raise SecurityError(
            "Result manifest source does not match the governed run that produced it"
        )
    existing = _load_existing_stage(layout, result, raw)
    if existing is not None:
        return existing
    if len(result.returned_files) > configuration.imports.max_files:
        _failed_staging(layout, raw)
        raise SecurityError(
            f"Result declares {len(result.returned_files)} files, exceeding configured limit "
            f"{configuration.imports.max_files}"
        )
    sources = [item.source_path for item in result.returned_files]
    targets = [item.proposed_target_path for item in result.returned_files]
    if len(set(sources)) != len(sources):
        _failed_staging(layout, raw)
        raise SecurityError("Result manifest declares duplicate source paths")
    if len(set(targets)) != len(targets):
        _failed_staging(layout, raw)
        raise SecurityError("Result manifest declares duplicate target paths")
    try:
        bundle_root = manifest_path.parent.resolve(strict=True)
        resolved_manifest = manifest_path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        _failed_staging(layout, raw)
        raise SecurityError(f"Result bundle cannot be resolved safely: {manifest_path}") from error
    declared_sources = set(sources)
    try:
        actual_sources = _bundle_inventory(bundle_root, resolved_manifest)
    except SecurityError:
        _failed_staging(layout, raw)
        raise
    if actual_sources != declared_sources:
        _failed_staging(layout, raw)
        raise SecurityError(
            "Result bundle file inventory does not match its manifest: "
            f"undeclared={sorted(actual_sources - declared_sources)}, "
            f"missing={sorted(declared_sources - actual_sources)}"
        )

    directory = layout.import_staging_directory / str(result.id)
    files_root = directory / "files"
    staged: list[StagedFile] = []
    total_bytes = 0
    try:
        directory.mkdir()
        files_root.mkdir()
        atomic_write_bytes(directory / "manifest.json", raw)
        for returned in result.returned_files:
            source = _source_file(bundle_root, returned.source_path)
            try:
                size = source.stat().st_size
                if size > configuration.imports.max_file_bytes:
                    raise SecurityError(
                        f"Returned file {returned.source_path!r} exceeds configured per-file "
                        f"limit {configuration.imports.max_file_bytes}"
                    )
                content = source.read_bytes()
            except OSError as error:
                raise IntegrityError(f"Cannot read returned file {source}: {error}") from error
            if len(content) > configuration.imports.max_file_bytes:
                raise SecurityError(
                    f"Returned file {returned.source_path!r} exceeds configured per-file "
                    f"limit {configuration.imports.max_file_bytes}"
                )
            total_bytes += len(content)
            if total_bytes > configuration.imports.max_total_bytes:
                raise SecurityError(
                    f"Returned files exceed configured total limit "
                    f"{configuration.imports.max_total_bytes}"
                )
            digest = sha256_digest(content)
            if returned.declared_digest is not None and returned.declared_digest != digest:
                raise SecurityError(
                    f"Returned file {returned.source_path!r} does not match its declared digest"
                )
            target = normalize_repository_path(returned.proposed_target_path)
            resolve_import_target(layout, target)
            screen_governed_content(
                target,
                content,
                secret_path_patterns=configuration.security.secret_path_patterns,
            )
            staged_path = files_root / returned.source_path
            _safe_stage_parent(files_root, returned.source_path)
            atomic_write_bytes(staged_path, content)
            staged.append(StagedFile(returned, staged_path, digest, len(content)))
        inventory = [
            {
                "byte_size": item.byte_size,
                "digest": item.digest,
                "source_path": item.declaration.source_path,
                "target_path": item.declaration.proposed_target_path,
            }
            for item in staged
        ]
        inventory_bytes = json.dumps(
            inventory,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8") + b"\n"
        atomic_write_bytes(directory / "inventory.json", inventory_bytes)
    except Exception:
        if not configuration.imports.preserve_failed_staging:
            shutil.rmtree(directory, ignore_errors=True)
        raise
    return StagedResult(
        result,
        directory,
        directory / "manifest.json",
        sha256_digest(raw),
        tuple(staged),
    )
