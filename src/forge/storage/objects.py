"""Immutable SHA-256 object preservation for governed file revisions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.canonical import canonical_json_digest as _canonical_json_digest
from forge.storage.canonical import sha256_digest
from forge.storage.repository import RepositoryLayout


@dataclass(frozen=True)
class PreservedObject:
    digest: str
    byte_size: int
    repository_path: str
    filesystem_path: Path
    created: bool


def canonical_json_digest(payload: object) -> str:
    """Compatibility export for existing core callers."""
    return _canonical_json_digest(payload)


def _object_location(layout: RepositoryLayout, digest: str) -> tuple[Path, str]:
    hexadecimal = digest.removeprefix("sha256:")
    destination = layout.object_directory / hexadecimal[:2] / hexadecimal[2:]
    return destination, destination.relative_to(layout.root).as_posix()


def preserve_bytes(
    layout: RepositoryLayout,
    content: bytes,
    *,
    max_bytes: int,
) -> PreservedObject:
    """Store exact bytes once and verify any existing content-addressed object."""
    if len(content) > max_bytes:
        raise ConflictError(
            f"Artifact is {len(content)} bytes, exceeding the configured preserved-object "
            f"limit of {max_bytes} bytes; split or reduce it before registration because "
            "large-artifact backends are deferred until after v1"
        )
    digest = sha256_digest(content)
    destination, repository_path = _object_location(layout, digest)
    parent = destination.parent
    if parent.is_symlink() or destination.is_symlink():
        raise SecurityError(f"Refusing to preserve bytes through a symbolic link: {destination}")
    if parent.exists() and not parent.is_dir():
        raise IntegrityError(f"Preserved-object prefix is not a directory: {parent}")
    if not parent.exists():
        try:
            parent.mkdir()
        except OSError as error:
            raise IntegrityError(
                f"Cannot create preserved-object prefix {parent}: {error}"
            ) from error
    if destination.exists():
        if not destination.is_file():
            raise IntegrityError(f"Preserved object is not a regular file: {destination}")
        try:
            if destination.stat().st_size != len(content):
                raise IntegrityError(
                    f"Preserved object does not match its SHA-256 path: {destination}"
                )
            existing = destination.read_bytes()
        except OSError as error:
            raise IntegrityError(f"Cannot read preserved object {destination}: {error}") from error
        if existing != content or sha256_digest(existing) != digest:
            raise IntegrityError(f"Preserved object does not match its SHA-256 path: {destination}")
        return PreservedObject(digest, len(content), repository_path, destination, False)

    atomic_write_bytes(destination, content)
    return PreservedObject(digest, len(content), repository_path, destination, True)


def verify_preserved_object(
    layout: RepositoryLayout,
    *,
    repository_path: str,
    expected_digest: str,
    expected_size: int,
) -> None:
    destination, expected_path = _object_location(layout, expected_digest)
    if repository_path != expected_path:
        raise IntegrityError(
            f"Preserved-object reference {repository_path!r} does not match digest path "
            f"{expected_path!r}"
        )
    if destination.is_symlink() or not destination.is_file():
        raise IntegrityError(f"Preserved object is missing or not a regular file: {destination}")
    try:
        if destination.stat().st_size != expected_size:
            raise IntegrityError(
                f"Preserved object failed size or digest verification: {destination}"
            )
        content = destination.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read preserved object {destination}: {error}") from error
    if len(content) != expected_size or sha256_digest(content) != expected_digest:
        raise IntegrityError(f"Preserved object failed size or digest verification: {destination}")
