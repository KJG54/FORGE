"""Best-effort, local-only structured CLI failure auditing."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from pydantic import ValidationError

from forge import __version__
from forge.contracts.base import utc_now
from forge.contracts.initiatives import Initiative
from forge.contracts.local_audit import (
    LocalAuditCategory,
    LocalAuditEvent,
    LocalAuditSeverity,
)
from forge.errors import ConflictError, ExitCode, ForgeError, IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.canonical import sha256_digest
from forge.storage.configuration import load_configuration
from forge.storage.records import MAX_RECORD_BYTES, load_record, render_record
from forge.storage.repository import RepositoryLayout

_CATEGORY_BY_EXIT_CODE = {
    ExitCode.CONFIGURATION: LocalAuditCategory.CONFIGURATION,
    ExitCode.AUTHORIZATION: LocalAuditCategory.AUTHORIZATION,
    ExitCode.TRANSITION: LocalAuditCategory.TRANSITION,
    ExitCode.INTEGRITY: LocalAuditCategory.INTEGRITY,
    ExitCode.CONFLICT: LocalAuditCategory.CONFLICT,
    ExitCode.SECURITY: LocalAuditCategory.SECURITY,
    ExitCode.EXTERNAL_TOOL: LocalAuditCategory.EXTERNAL_TOOL,
    ExitCode.INTERNAL: LocalAuditCategory.INTERNAL,
}

_SEVERITY_BY_CATEGORY = {
    LocalAuditCategory.CONFIGURATION: LocalAuditSeverity.WARNING,
    LocalAuditCategory.AUTHORIZATION: LocalAuditSeverity.WARNING,
    LocalAuditCategory.TRANSITION: LocalAuditSeverity.NOTICE,
    LocalAuditCategory.INTEGRITY: LocalAuditSeverity.ERROR,
    LocalAuditCategory.CONFLICT: LocalAuditSeverity.NOTICE,
    LocalAuditCategory.SECURITY: LocalAuditSeverity.ERROR,
    LocalAuditCategory.EXTERNAL_TOOL: LocalAuditSeverity.WARNING,
    LocalAuditCategory.INTERNAL: LocalAuditSeverity.CRITICAL,
}


def _initiative_id(layout: RepositoryLayout) -> UUID | None:
    if not layout.initiative_file.is_file() or layout.initiative_file.is_symlink():
        return None
    try:
        return load_record(layout.initiative_file, Initiative).id
    except ForgeError:
        return None


def _ensure_audit_directory(layout: RepositoryLayout) -> Path:
    directory = layout.local_audit_event_directory
    if layout.local_directory.is_symlink() or directory.is_symlink():
        raise SecurityError(
            f"Refusing a local audit directory through a symbolic link: {directory}"
        )
    if not layout.local_directory.is_dir():
        raise IntegrityError(f"FORGE local directory is missing: {layout.local_directory}")
    try:
        directory.mkdir(exist_ok=True)
    except OSError as error:
        raise IntegrityError(f"Cannot create local audit directory {directory}: {error}") from error
    if directory.is_symlink():
        raise SecurityError(f"Local audit event directory is unsafe: {directory}")
    if not directory.is_dir():
        raise IntegrityError(f"Local audit path is not a directory: {directory}")
    return directory


def record_local_audit_event(
    layout: RepositoryLayout,
    *,
    operation: str,
    error: ForgeError,
) -> LocalAuditEvent:
    """Persist one sanitized local event without granting it governance authority."""
    configuration = load_configuration(layout.configuration_file)
    category = _CATEGORY_BY_EXIT_CODE.get(
        error.exit_code,
        LocalAuditCategory.INTERNAL,
    )
    event = LocalAuditEvent(
        id=uuid4(),
        project_id=configuration.project_id,
        initiative_id=_initiative_id(layout),
        configured_owner_id=configuration.owner.id,
        timestamp=utc_now(),
        operation=operation,
        category=category,
        severity=_SEVERITY_BY_CATEGORY[category],
        exit_code=int(error.exit_code),
        error_type=type(error).__name__,
        detail_digest=sha256_digest(str(error).encode("utf-8")),
        tool_version=__version__,
    )
    directory = _ensure_audit_directory(layout)
    destination = directory / f"{event.id}.json"
    if destination.exists() or destination.is_symlink():
        raise ConflictError(f"Refusing to overwrite local audit event: {destination}")
    atomic_write_bytes(destination, render_record(event))
    return event


def _load_local_audit_event(path: Path) -> LocalAuditEvent:
    if path.is_symlink():
        raise SecurityError(f"Refusing to read a local audit event through a symbolic link: {path}")
    if not path.is_file():
        raise IntegrityError(f"Local audit event is not a regular file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read local audit event {path}: {error}") from error
    if len(raw) > MAX_RECORD_BYTES:
        raise IntegrityError(f"Local audit event exceeds {MAX_RECORD_BYTES} bytes: {path}")
    try:
        return LocalAuditEvent.model_validate_json(raw)
    except ValidationError as error:
        raise IntegrityError(f"Invalid local audit event {path}: {error}") from error


def list_local_audit_events(
    layout: RepositoryLayout,
    *,
    category: LocalAuditCategory | None = None,
) -> tuple[LocalAuditEvent, ...]:
    """Validate and list local observations in deterministic timestamp order."""
    directory = layout.local_audit_event_directory
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise SecurityError(f"Local audit event directory is unsafe: {directory}")
    try:
        paths = tuple(directory.iterdir())
    except OSError as error:
        raise IntegrityError(f"Cannot inspect local audit event directory: {error}") from error
    if any(path.suffix != ".json" for path in paths):
        raise IntegrityError(
            f"Local audit event directory contains an unexpected entry: {directory}"
        )
    events = tuple(_load_local_audit_event(path) for path in paths)
    selected = (
        events
        if category is None
        else tuple(event for event in events if event.category is category)
    )
    return tuple(sorted(selected, key=lambda event: (event.timestamp, str(event.id))))


def show_local_audit_event(
    layout: RepositoryLayout,
    event_id: UUID,
) -> LocalAuditEvent:
    path = layout.local_audit_event_directory / f"{event_id}.json"
    if path.is_symlink():
        raise SecurityError(f"Local audit event path is unsafe: {path}")
    if not path.exists():
        raise ConflictError(f"Unknown local audit event {event_id}")
    return _load_local_audit_event(path)
