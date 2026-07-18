"""Journal-bound mutation idempotency and completion receipts."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Collection, Generator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError

from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.idempotency import (
    IdempotencyEventMetadata,
    IdempotencyEventReference,
    IdempotencyReceipt,
)
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.canonical import canonical_json_digest
from forge.storage.journal import inspect_journal_recovery_candidate, read_journal
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout

IDEMPOTENCY_METADATA_KEY = "idempotency"
_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_COMMAND_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$")
_REQUEST_CONTEXT: ContextVar[IdempotencyEventMetadata | None] = ContextVar(
    "forge_idempotency_request", default=None
)
type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]


@dataclass(frozen=True)
class IdempotencyInvocation:
    key: str
    command: str
    request_digest: str
    receipt: IdempotencyReceipt | None = None

    @property
    def is_replay(self) -> bool:
        return self.receipt is not None


@dataclass(frozen=True)
class IncompleteIdempotencyCommand:
    key: str
    command: str
    request_digest: str
    events: tuple[IdempotencyEventReference, ...]


@dataclass(frozen=True)
class _RawRegistry:
    receipts: dict[str, IdempotencyReceipt]
    event_groups: dict[str, tuple[tuple[IdempotencyEventMetadata, AuditEvent], ...]]


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return _json_value(value.value)
    if isinstance(value, BaseModel):
        return _json_value(cast(object, value.model_dump(mode="json")))
    if isinstance(value, Mapping):
        normalized: dict[str, JsonValue] = {}
        for key, item in cast(Mapping[object, object], value).items():
            if not isinstance(key, str):
                raise ConfigurationError("Idempotency request mappings require string keys")
            normalized[key] = _json_value(item)
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [_json_value(item) for item in cast(Sequence[object], value)]
    raise ConfigurationError(
        f"Cannot bind idempotency to unsupported request value {type(value).__name__}"
    )


def request_digest(command: str, parameters: Mapping[str, object]) -> str:
    """Bind a stable command identity to its normalized explicit parameters."""
    normalized_command = _validate_command(command)
    return canonical_json_digest(
        {
            "command": normalized_command,
            "parameters": _json_value(parameters),
        }
    )


def _validate_key(value: str | None) -> str:
    candidate = (str(uuid4()) if value is None else value).strip()
    if not _KEY_PATTERN.fullmatch(candidate):
        raise ConfigurationError(
            "Idempotency key must be 1-128 ASCII letters, digits, '.', '_', ':', or '-'"
        )
    return candidate


def normalize_idempotency_key(value: str | None) -> str:
    """Return one generated or strictly validated public idempotency key."""
    return _validate_key(value)


def _validate_command(value: str) -> str:
    candidate = value.strip()
    if len(candidate) > 128 or not _COMMAND_PATTERN.fullmatch(candidate):
        raise ConfigurationError(f"Invalid idempotency command identity {value!r}")
    return candidate


def _metadata(event: AuditEvent) -> IdempotencyEventMetadata | None:
    raw = event.metadata.get(IDEMPOTENCY_METADATA_KEY)
    if raw is None:
        return None
    try:
        return IdempotencyEventMetadata.model_validate(raw)
    except ValidationError as error:
        raise IntegrityError(
            f"Event {event.id} has invalid idempotency metadata: {error}"
        ) from error


def stamp_event_for_current_mutation(event: AuditEvent) -> AuditEvent:
    """Attach the active command identity before the event is hash sealed."""
    if IDEMPOTENCY_METADATA_KEY in event.metadata:
        raise ConflictError("Event metadata key 'idempotency' is reserved by FORGE")
    request = _REQUEST_CONTEXT.get()
    if request is None:
        return event
    metadata = dict(event.metadata)
    metadata[IDEMPOTENCY_METADATA_KEY] = request.model_dump(mode="json")
    return event.model_copy(update={"metadata": metadata})


def current_idempotency_request() -> IdempotencyEventMetadata:
    """Return the command identity bound to the active mutation context."""
    request = _REQUEST_CONTEXT.get()
    if request is None:
        raise IntegrityError("Recovery requires an active idempotent mutation context")
    return request


def active_idempotency_request() -> IdempotencyEventMetadata | None:
    """Return the active command identity when called inside a mutation context."""
    return _REQUEST_CONTEXT.get()


def _receipt_path(layout: RepositoryLayout, key: str) -> Path:
    filename = hashlib.sha256(key.encode("utf-8")).hexdigest() + ".json"
    return layout.idempotency_directory / filename


def _ensure_receipt_directory(layout: RepositoryLayout) -> None:
    path = layout.idempotency_directory
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise SecurityError(f"Idempotency receipt directory is unsafe: {path}")
        return
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create idempotency receipt directory: {error}") from error


def _read_receipts(layout: RepositoryLayout) -> dict[str, IdempotencyReceipt]:
    directory = layout.idempotency_directory
    if not directory.exists():
        return {}
    if directory.is_symlink() or not directory.is_dir():
        raise SecurityError(f"Idempotency receipt directory is unsafe: {directory}")
    receipts: dict[str, IdempotencyReceipt] = {}
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file() or path.suffix != ".json":
            raise IntegrityError(f"Unexpected idempotency receipt entry: {path}")
        receipt = load_record(path, IdempotencyReceipt)
        if path != _receipt_path(layout, receipt.key):
            raise IntegrityError(f"Idempotency receipt path does not match its key: {path}")
        if receipt.key in receipts:
            raise IntegrityError(f"Duplicate idempotency receipt key: {receipt.key}")
        receipts[receipt.key] = receipt
    return receipts


def _journal_events(
    layout: RepositoryLayout,
    *,
    allow_recoverable_active_journal: bool = False,
) -> tuple[AuditEvent, ...]:
    events: list[AuditEvent] = []
    if layout.event_journal_file.exists():
        if allow_recoverable_active_journal:
            candidate = inspect_journal_recovery_candidate(layout.event_journal_file)
            events.extend(
                candidate.events
                if candidate is not None
                else read_journal(layout.event_journal_file)
            )
        else:
            events.extend(read_journal(layout.event_journal_file))
    archive = layout.archive_directory
    if archive.is_symlink() or not archive.is_dir():
        raise SecurityError(f"Archive directory is missing or unsafe: {archive}")
    for candidate in sorted(archive.iterdir(), key=lambda item: item.name):
        if candidate.name.startswith("."):
            continue
        if candidate.is_symlink() or not candidate.is_dir():
            raise IntegrityError(f"Unexpected archive entry: {candidate}")
        try:
            UUID(candidate.name)
        except ValueError as error:
            raise IntegrityError(
                f"Archive directory name is not an initiative UUID: {candidate}"
            ) from error
        journal = candidate / "events.jsonl"
        if journal.exists():
            events.extend(read_journal(journal))
    event_ids = tuple(event.id for event in events)
    if len(set(event_ids)) != len(event_ids):
        raise IntegrityError("Repository history contains duplicate event IDs across initiatives")
    return tuple(events)


def _read_raw_registry(
    layout: RepositoryLayout,
    *,
    allow_recoverable_active_journal: bool = False,
) -> _RawRegistry:
    groups: dict[str, list[tuple[IdempotencyEventMetadata, AuditEvent]]] = {}
    for event in _journal_events(
        layout,
        allow_recoverable_active_journal=allow_recoverable_active_journal,
    ):
        metadata = _metadata(event)
        if metadata is not None:
            groups.setdefault(metadata.key, []).append((metadata, event))
    return _RawRegistry(
        receipts=_read_receipts(layout),
        event_groups={key: tuple(value) for key, value in groups.items()},
    )


def _validate_registry(
    raw: _RawRegistry,
    *,
    allowed_incomplete_keys: Collection[str] = (),
) -> None:
    allowed = set(allowed_incomplete_keys)
    all_keys = set(raw.receipts) | set(raw.event_groups)
    for key in all_keys:
        receipt = raw.receipts.get(key)
        group = raw.event_groups.get(key, ())
        if receipt is None:
            if key in allowed and group:
                identities = {
                    (metadata.command, metadata.request_digest)
                    for metadata, _event in group
                }
                if len(identities) != 1:
                    raise IntegrityError(f"Idempotency metadata disagrees for key {key!r}")
                continue
            raise IntegrityError(
                f"Idempotency key {key!r} has committed events without a completion receipt; "
                "explicit recovery is required. Inspect history, then use the command's "
                "specialized same-key retry or 'forge recover-command' with a distinct key"
            )
        if not group:
            raise IntegrityError(
                f"Idempotency receipt {key!r} does not reference committed journal events"
            )
        expected_identity = (receipt.command, receipt.request_digest)
        if any(
            (metadata.command, metadata.request_digest) != expected_identity
            for metadata, _event in group
        ):
            raise IntegrityError(f"Idempotency metadata disagrees for key {key!r}")
        referenced = {item.event_id: item for item in receipt.events}
        if len(referenced) != len(group):
            raise IntegrityError(f"Idempotency receipt event count disagrees for key {key!r}")
        for _metadata_value, event in group:
            reference = referenced.get(event.id)
            if (
                reference is None
                or event.event_hash is None
                or reference.initiative_id != event.initiative_id
                or reference.sequence != event.sequence
                or reference.event_hash != event.event_hash
            ):
                raise IntegrityError(
                    f"Idempotency receipt {key!r} is not bound to exact journal events"
                )


def validate_idempotency_store(layout: RepositoryLayout) -> int:
    """Validate all receipts against active and archived hash-chained events."""
    raw = _read_raw_registry(layout)
    _validate_registry(raw)
    return len(raw.receipts)


def inspect_incomplete_command(
    layout: RepositoryLayout,
    *,
    target_key: str,
    recovery_key: str,
    allow_completed_target: bool = False,
) -> IncompleteIdempotencyCommand:
    """Return one exact incomplete event group while refusing all other registry damage."""
    target_key = _validate_key(target_key)
    recovery_key = _validate_key(recovery_key)
    if target_key == recovery_key:
        raise ConflictError("The interrupted key and recovery command key must be different")
    raw = _read_raw_registry(layout)
    _validate_registry(
        raw,
        allowed_incomplete_keys=(target_key, recovery_key),
    )
    if target_key in raw.receipts and not allow_completed_target:
        raise ConflictError(f"Idempotency key {target_key!r} already has a completion receipt")
    group = raw.event_groups.get(target_key, ())
    if not group:
        raise ConflictError(
            f"Idempotency key {target_key!r} has no committed events to recover"
        )
    identities = {(metadata.command, metadata.request_digest) for metadata, _event in group}
    if len(identities) != 1:
        raise IntegrityError(f"Idempotency metadata disagrees for key {target_key!r}")
    command, digest = identities.pop()
    return IncompleteIdempotencyCommand(
        key=target_key,
        command=command,
        request_digest=digest,
        events=_event_references(group),
    )


def write_recovered_receipt(
    layout: RepositoryLayout,
    receipt: IdempotencyReceipt,
    *,
    recovery_key: str,
) -> None:
    """Atomically install an explicitly reconstructed receipt and validate exact history."""
    recovery_key = _validate_key(recovery_key)
    raw = _read_raw_registry(layout)
    _validate_registry(
        raw,
        allowed_incomplete_keys=(receipt.key, recovery_key),
    )
    if receipt.key in raw.receipts:
        if raw.receipts[receipt.key] != receipt:
            raise IntegrityError(
                f"Recovered receipt for key {receipt.key!r} changed after recovery commitment"
            )
        return
    group = raw.event_groups.get(receipt.key, ())
    if not group or _event_references(group) != receipt.events:
        raise IntegrityError(
            f"Committed events changed for recovered idempotency key {receipt.key!r}"
        )
    identity = {(metadata.command, metadata.request_digest) for metadata, _event in group}
    if identity != {(receipt.command, receipt.request_digest)}:
        raise IntegrityError(f"Recovered receipt identity disagrees for key {receipt.key!r}")
    _ensure_receipt_directory(layout)
    write_record(_receipt_path(layout, receipt.key), receipt)
    completed = _read_raw_registry(layout)
    _validate_registry(completed, allowed_incomplete_keys=(recovery_key,))


def _event_references(
    group: tuple[tuple[IdempotencyEventMetadata, AuditEvent], ...],
) -> tuple[IdempotencyEventReference, ...]:
    references: list[IdempotencyEventReference] = []
    for _metadata_value, event in group:
        if event.event_hash is None:
            raise IntegrityError("Idempotent mutations require hash-chained journal events")
        references.append(
            IdempotencyEventReference(
                event_id=event.id,
                initiative_id=event.initiative_id,
                sequence=event.sequence,
                event_hash=event.event_hash,
            )
        )
    return tuple(references)


@contextmanager
def idempotent_mutation(
    layout: RepositoryLayout,
    *,
    command: str,
    provided_key: str | None,
    parameters: Mapping[str, object],
    resume_incomplete: bool = False,
    allow_recoverable_active_journal: bool = False,
    additional_allowed_incomplete_keys: Collection[str] = (),
) -> Generator[IdempotencyInvocation]:
    """Replay a completed command or bind newly committed events to one receipt."""
    key = _validate_key(provided_key)
    command = _validate_command(command)
    digest = request_digest(command, parameters)
    raw = _read_raw_registry(
        layout,
        allow_recoverable_active_journal=allow_recoverable_active_journal,
    )
    additional = tuple(_validate_key(item) for item in additional_allowed_incomplete_keys)
    allowed = (*additional, *((key,) if resume_incomplete else ()))
    _validate_registry(raw, allowed_incomplete_keys=allowed)
    existing = raw.receipts.get(key)
    if existing is not None:
        if (existing.command, existing.request_digest) != (command, digest):
            raise ConflictError(
                f"Idempotency key {key!r} was already used for a different command request"
            )
        yield IdempotencyInvocation(key, command, digest, existing)
        return

    incomplete = raw.event_groups.get(key, ())
    if incomplete:
        if not resume_incomplete:
            raise IntegrityError(
                f"Idempotency key {key!r} has committed events without a completion receipt; "
                "explicit recovery is required. Inspect history, then use the command's "
                "specialized same-key retry or 'forge recover-command' with a distinct key"
            )
        if any(
            (metadata.command, metadata.request_digest) != (command, digest)
            for metadata, _event in incomplete
        ):
            raise ConflictError(
                f"Idempotency key {key!r} was already used for a different command request"
            )

    request = IdempotencyEventMetadata(
        key=key,
        command=command,
        request_digest=digest,
    )
    if _REQUEST_CONTEXT.get() is not None:
        raise IntegrityError("Nested idempotent mutation contexts are not supported")
    token = _REQUEST_CONTEXT.set(request)
    try:
        yield IdempotencyInvocation(key, command, digest)
    except BaseException:
        raise
    else:
        completed = _read_raw_registry(layout)
        group = completed.event_groups.get(key, ())
        if not group:
            raise IntegrityError(
                f"Mutation command {command!r} completed without a journal-bound event"
            )
        if any(metadata != request for metadata, _event in group):
            raise IntegrityError(f"Committed events disagree for idempotency key {key!r}")
        receipt = IdempotencyReceipt(
            key=key,
            command=command,
            request_digest=digest,
            completed_at=utc_now(),
            events=_event_references(group),
        )
        _ensure_receipt_directory(layout)
        write_record(_receipt_path(layout, key), receipt)
        validate_idempotency_store(layout)
    finally:
        _REQUEST_CONTEXT.reset(token)
