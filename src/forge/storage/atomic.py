"""Same-filesystem atomic replacement for governed files."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from pathlib import Path

from forge.errors import ConflictError, IntegrityError, SecurityError

AtomicValidator = Callable[[Path], None]


def _sync_directory(directory: Path) -> None:
    """Synchronize directory metadata where the platform exposes that operation."""
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(
    destination: Path,
    content: bytes,
    *,
    validator: AtomicValidator | None = None,
) -> None:
    """Validate and atomically replace a file with exact bytes.

    The temporary file is created beside the destination so ``os.replace`` remains a
    same-filesystem operation. The caller owns any higher-level journal transaction.
    """
    parent = destination.parent
    if not parent.is_dir():
        raise ConflictError(f"Atomic-write parent directory does not exist: {parent}")
    if parent.is_symlink() or destination.is_symlink():
        raise SecurityError(f"Refusing an atomic write through a symbolic link: {destination}")
    if destination.exists() and not destination.is_file():
        raise ConflictError(f"Atomic-write destination is not a file: {destination}")

    descriptor, temporary_name = tempfile.mkstemp(
        dir=parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if validator is not None:
            validator(temporary)
        os.replace(temporary, destination)
        _sync_directory(parent)
        if destination.read_bytes() != content:
            raise IntegrityError(
                f"Atomic-write verification failed for governed file: {destination}"
            )
    except (ConflictError, IntegrityError, SecurityError):
        raise
    except OSError as error:
        raise IntegrityError(f"Atomic write failed for {destination}: {error}") from error
    finally:
        temporary.unlink(missing_ok=True)
