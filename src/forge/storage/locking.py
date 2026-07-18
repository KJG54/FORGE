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
from typing import cast
from uuid import uuid4

from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import sync_directory
from forge.storage.repository import RepositoryLayout

LOCK_NAME = "mutation.lock"
REMEDIATION_LOCK_NAME = "stale-lock-remediation.lock"
MAX_LOCK_BYTES = 16_384


@dataclass(frozen=True)
class LockOwner:
    token: str
    pid: int
    hostname: str
    command: str
    created_at: str

    def __post_init__(self) -> None:
        if (
            not self.token.strip()
            or self.pid <= 0
            or not self.hostname.strip()
            or not self.command.strip()
            or not self.created_at.strip()
        ):
            raise ValueError("lock owner fields are invalid")


@dataclass(frozen=True)
class RemediationLockOwner:
    token: str
    pid: int
    hostname: str
    command: str
    created_at: str
    idempotency_key: str

    def __post_init__(self) -> None:
        LockOwner(
            token=self.token,
            pid=self.pid,
            hostname=self.hostname,
            command=self.command,
            created_at=self.created_at,
        )
        if not self.idempotency_key.strip():
            raise ValueError("remediation idempotency key is invalid")


@dataclass(frozen=True)
class LockObservation:
    owner: LockOwner
    content: bytes


def _path(layout: RepositoryLayout) -> Path:
    return layout.lock_directory / LOCK_NAME


def _remediation_path(layout: RepositoryLayout) -> Path:
    return layout.lock_directory / REMEDIATION_LOCK_NAME


def _read_content(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise SecurityError(f"Mutation lock is missing, irregular, or symbolic: {path}")
    try:
        content = path.read_bytes()
        if len(content) > MAX_LOCK_BYTES:
            raise IntegrityError(f"Mutation lock metadata exceeds {MAX_LOCK_BYTES} bytes: {path}")
        return content
    except IntegrityError:
        raise
    except OSError as error:
        raise IntegrityError(f"Cannot read mutation lock metadata: {path}: {error}") from error


def _decode_mapping(content: bytes, path: Path) -> dict[str, object]:
    try:
        value = cast(object, json.loads(content.decode("utf-8")))
        if not isinstance(value, dict):
            raise TypeError("lock metadata must be a JSON object")
        mapping = cast(dict[object, object], value)
        if not all(isinstance(key, str) for key in mapping):
            raise TypeError("lock metadata keys must be text")
        return cast(dict[str, object], mapping)
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IntegrityError(f"Mutation lock metadata is invalid: {path}: {error}") from error


def _text_field(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"lock metadata field {name!r} must be non-empty text")
    return value


def _pid_field(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TypeError("lock metadata field 'pid' must be a positive integer")
    return value


def _decode_owner(content: bytes, path: Path) -> LockOwner:
    try:
        value = _decode_mapping(content, path)
        expected = {"token", "pid", "hostname", "command", "created_at"}
        if set(value) != expected:
            raise TypeError(f"lock metadata fields must be exactly {sorted(expected)}")
        return LockOwner(
            token=_text_field(value["token"], "token"),
            pid=_pid_field(value["pid"]),
            hostname=_text_field(value["hostname"], "hostname"),
            command=_text_field(value["command"], "command"),
            created_at=_text_field(value["created_at"], "created_at"),
        )
    except TypeError as error:
        raise IntegrityError(f"Mutation lock metadata is invalid: {path}: {error}") from error


def _decode_remediation_owner(content: bytes, path: Path) -> RemediationLockOwner:
    try:
        value = _decode_mapping(content, path)
        expected = {
            "token",
            "pid",
            "hostname",
            "command",
            "created_at",
            "idempotency_key",
        }
        if set(value) != expected:
            raise TypeError(f"lock metadata fields must be exactly {sorted(expected)}")
        return RemediationLockOwner(
            token=_text_field(value["token"], "token"),
            pid=_pid_field(value["pid"]),
            hostname=_text_field(value["hostname"], "hostname"),
            command=_text_field(value["command"], "command"),
            created_at=_text_field(value["created_at"], "created_at"),
            idempotency_key=_text_field(value["idempotency_key"], "idempotency_key"),
        )
    except TypeError as error:
        raise IntegrityError(f"Mutation lock metadata is invalid: {path}: {error}") from error


def _read(path: Path) -> LockOwner:
    return _decode_owner(_read_content(path), path)


def _read_remediation(path: Path) -> RemediationLockOwner:
    return _decode_remediation_owner(_read_content(path), path)


def observe_mutation_lock(layout: RepositoryLayout) -> LockObservation:
    """Read one bounded regular lock and retain its exact bytes."""
    return observe_lock_path(_path(layout))


def observe_lock_path(path: Path) -> LockObservation:
    """Read and validate exact bytes from a specified mutation-lock evidence path."""
    content = _read_content(path)
    owner = _decode_owner(content, path)
    return LockObservation(owner=owner, content=content)


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        return _windows_process_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _windows_process_alive(pid: int) -> bool:
    """Query process state without using Windows ``os.kill(pid, 0)``.

    CPython maps ordinary Windows ``os.kill`` signal values to ``TerminateProcess``;
    the POSIX liveness idiom is therefore unsafe on Windows.
    """
    import ctypes
    from collections.abc import Callable
    from ctypes import wintypes
    from typing import cast

    process_query_limited_information = 0x1000
    error_invalid_parameter = 87
    still_active = 259
    win_dll = cast(type[ctypes.CDLL], ctypes.__dict__["WinDLL"])
    get_last_error = cast(Callable[[], int], ctypes.__dict__["get_last_error"])
    kernel32 = win_dll("kernel32", use_last_error=True)
    open_process = kernel32.OpenProcess
    open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    open_process.restype = wintypes.HANDLE
    get_exit_code = kernel32.GetExitCodeProcess
    get_exit_code.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    get_exit_code.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL

    handle = open_process(process_query_limited_information, False, pid)
    if not handle:
        # Access denied is conservatively treated as live; only a definitively invalid
        # process identifier is stale.
        return get_last_error() != error_invalid_parameter
    exit_code = wintypes.DWORD()
    try:
        if not get_exit_code(handle, ctypes.byref(exit_code)):
            return True
        return exit_code.value == still_active
    finally:
        close_handle(handle)


def lock_owner_is_definitively_stale(owner: LockOwner) -> bool:
    """Return true only for a same-host owner whose PID is definitively not live."""
    return owner.hostname == socket.gethostname() and not _alive(owner.pid)


def lock_diagnostic(layout: RepositoryLayout) -> str | None:
    path = _path(layout)
    if not path.exists() and not path.is_symlink():
        return None
    owner = _read(path)
    status = "live" if owner.hostname == socket.gethostname() and _alive(owner.pid) else "stale"
    return (
        f"{status} mutation lock: pid={owner.pid} host={owner.hostname} "
        f"command={owner.command!r} created={owner.created_at}; never delete locks silently"
    )


def remediation_lock_diagnostic(layout: RepositoryLayout) -> str | None:
    path = _remediation_path(layout)
    if not path.exists() and not path.is_symlink():
        return None
    owner = _read_remediation(path)
    status = "live" if owner.hostname == socket.gethostname() and _alive(owner.pid) else "stale"
    return (
        f"{status} stale-lock remediation guard: pid={owner.pid} host={owner.hostname} "
        f"key={owner.idempotency_key!r} created={owner.created_at}"
    )


def _write_owner_exclusively(path: Path, owner: LockOwner | RemediationLockOwner) -> None:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(asdict(owner), stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        sync_directory(path.parent)
    except FileExistsError:
        raise
    except OSError as error:
        raise IntegrityError(f"Cannot create repository lock {path}: {error}") from error


def _release_owned(path: Path, token: str, *, label: str) -> None:
    current = _read_remediation(path) if label == "remediation" else _read(path)
    if current.token != token:
        raise IntegrityError(
            f"{label.capitalize()} lock ownership changed while command was running"
        )
    try:
        path.unlink()
        sync_directory(path.parent)
    except OSError as error:
        raise IntegrityError(f"Cannot release repository {label} lock: {error}") from error


@contextmanager
def stale_lock_remediation_guard(
    layout: RepositoryLayout, *, idempotency_key: str
) -> Generator[RemediationLockOwner]:
    """Exclude ordinary mutations while one explicit stale-lock operation runs."""
    path = _remediation_path(layout)
    owner = RemediationLockOwner(
        token=str(uuid4()),
        pid=os.getpid(),
        hostname=socket.gethostname(),
        command="remediate-lock",
        created_at=datetime.now(UTC).isoformat(),
        idempotency_key=idempotency_key,
    )
    try:
        _write_owner_exclusively(path, owner)
    except FileExistsError as error:
        current = _read_remediation(path)
        if (
            current.idempotency_key != idempotency_key
            or current.hostname != socket.gethostname()
            or _alive(current.pid)
        ):
            detail = remediation_lock_diagnostic(layout)
            raise ConflictError(f"Stale-lock remediation is already locked; {detail}") from error
        _release_owned(path, current.token, label="remediation")
        try:
            _write_owner_exclusively(path, owner)
        except FileExistsError as retry_error:
            detail = remediation_lock_diagnostic(layout)
            raise ConflictError(
                f"Stale-lock remediation is already locked; {detail}"
            ) from retry_error
    try:
        yield owner
    finally:
        _release_owned(path, owner.token, label="remediation")


@contextmanager
def repository_mutation_lock(layout: RepositoryLayout, *, command: str) -> Generator[LockOwner]:
    path = _path(layout)
    owner = LockOwner(
        token=str(uuid4()),
        pid=os.getpid(),
        hostname=socket.gethostname(),
        command=command,
        created_at=datetime.now(UTC).isoformat(),
    )
    remediation_detail = remediation_lock_diagnostic(layout)
    if remediation_detail is not None:
        raise ConflictError(f"Repository lock remediation is in progress; {remediation_detail}")
    try:
        _write_owner_exclusively(path, owner)
    except FileExistsError as error:
        detail = lock_diagnostic(layout)
        raise ConflictError(f"Repository mutation is locked; {detail}") from error
    remediation_detail = remediation_lock_diagnostic(layout)
    if remediation_detail is not None:
        _release_owned(path, owner.token, label="mutation")
        raise ConflictError(f"Repository lock remediation is in progress; {remediation_detail}")
    try:
        yield owner
    finally:
        _release_owned(path, owner.token, label="mutation")
