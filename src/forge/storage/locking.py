"""Cross-process repository mutation lock with explicit stale diagnostics."""

from __future__ import annotations

import json
import os
import socket
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.repository import RepositoryLayout

LOCK_NAME = "mutation.lock"


@dataclass(frozen=True)
class LockOwner:
    token: str
    pid: int
    hostname: str
    command: str
    created_at: str


def _path(layout: RepositoryLayout) -> Path:
    return layout.lock_directory / LOCK_NAME


def _read(path: Path) -> LockOwner:
    if path.is_symlink() or not path.is_file():
        raise SecurityError(f"Mutation lock is missing, irregular, or symbolic: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return LockOwner(**value)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise IntegrityError(f"Mutation lock metadata is invalid: {path}: {error}") from error


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def lock_diagnostic(layout: RepositoryLayout) -> str | None:
    path = _path(layout)
    if not path.exists():
        return None
    owner = _read(path)
    status = "live" if owner.hostname == socket.gethostname() and _alive(owner.pid) else "stale"
    return (
        f"{status} mutation lock: pid={owner.pid} host={owner.hostname} "
        f"command={owner.command!r} created={owner.created_at}; never delete locks silently"
    )


@contextmanager
def repository_mutation_lock(
    layout: RepositoryLayout, *, command: str
) -> Generator[LockOwner]:
    path = _path(layout)
    owner = LockOwner(
        token=str(uuid4()),
        pid=os.getpid(),
        hostname=socket.gethostname(),
        command=command,
        created_at=datetime.now(UTC).isoformat(),
    )
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(asdict(owner), stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as error:
        detail = lock_diagnostic(layout)
        raise ConflictError(f"Repository mutation is locked; {detail}") from error
    except OSError as error:
        raise IntegrityError(f"Cannot create repository mutation lock: {error}") from error
    try:
        yield owner
    finally:
        current = _read(path)
        if current.token != owner.token:
            raise IntegrityError("Mutation lock ownership changed while command was running")
        try:
            path.unlink()
        except OSError as error:
            raise IntegrityError(f"Cannot release repository mutation lock: {error}") from error
