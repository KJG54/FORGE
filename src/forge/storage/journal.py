"""Ordered JSON Lines persistence for M1 governance events."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from forge.contracts.events import AuditEvent
from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.canonical import canonical_json_bytes, canonical_json_digest

MAX_EVENT_BYTES = 1_048_576
MAX_JOURNAL_RECOVERY_BYTES = 104_857_600


@dataclass(frozen=True)
class JournalRecoveryCandidate:
    """Exact damaged bytes and the unambiguous complete event prefix they contain."""

    source_bytes: bytes
    valid_prefix_bytes: bytes
    events: tuple[AuditEvent, ...]
    truncated_tail: bytes


def _read_journal_bytes(path: Path) -> bytes:
    if not path.exists():
        return b""
    if path.is_symlink():
        raise SecurityError(f"Refusing to read an event journal through a symbolic link: {path}")
    if not path.is_file():
        raise IntegrityError(f"Event journal is not a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read event journal {path}: {error}") from error


def _parse_complete_journal(raw: bytes) -> tuple[AuditEvent, ...]:
    if not raw:
        return ()
    if not raw.endswith(b"\n"):
        raise IntegrityError("Event journal ends with an incomplete record")

    events: list[AuditEvent] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line:
            raise IntegrityError(f"Event journal contains a blank record at line {line_number}")
        if len(line) > MAX_EVENT_BYTES:
            raise IntegrityError(
                f"Event journal record {line_number} exceeds {MAX_EVENT_BYTES} bytes"
            )
        try:
            decoded = json.loads(line)
            event = AuditEvent.model_validate(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise IntegrityError(
                f"Invalid event journal record at line {line_number}: {error}"
            ) from error
        events.append(event)

    validated = tuple(events)
    validate_event_sequence(validated)
    return validated


def _is_eof_json_truncation(error: json.JSONDecodeError, tail: bytes) -> bool:
    if error.msg.startswith("Unterminated string"):
        return True
    return error.pos >= len(tail) - 1 and error.msg in {
        "Expecting ',' delimiter",
        "Expecting ':' delimiter",
        "Expecting property name enclosed in double quotes",
        "Expecting value",
    }


def inspect_journal_recovery_candidate(path: Path) -> JournalRecoveryCandidate | None:
    """Return only an unambiguous EOF-truncated final record; reject all other damage."""
    raw = _read_journal_bytes(path)
    if not raw or raw.endswith(b"\n"):
        _parse_complete_journal(raw)
        return None
    if len(raw) > MAX_JOURNAL_RECOVERY_BYTES:
        raise IntegrityError(
            "Damaged event journal exceeds the explicit recovery preservation limit of "
            f"{MAX_JOURNAL_RECOVERY_BYTES} bytes"
        )
    delimiter = raw.rfind(b"\n")
    if delimiter < 0:
        raise IntegrityError(
            "Damaged event journal has no complete event prefix; recovery is ambiguous"
        )
    prefix = raw[: delimiter + 1]
    tail = raw[delimiter + 1 :]
    if len(tail) > MAX_EVENT_BYTES:
        raise IntegrityError(
            f"Truncated final record exceeds the {MAX_EVENT_BYTES}-byte event limit"
        )
    events = _parse_complete_journal(prefix)
    if not events:
        raise IntegrityError(
            "Damaged event journal has no complete event prefix; recovery is ambiguous"
        )
    try:
        decoded = json.loads(tail)
    except UnicodeDecodeError as error:
        if error.end != len(tail) or "unexpected end" not in error.reason:
            raise IntegrityError(
                "Final event journal record is malformed rather than unambiguously truncated"
            ) from error
    except json.JSONDecodeError as error:
        if not _is_eof_json_truncation(error, tail):
            raise IntegrityError(
                "Final event journal record is malformed rather than unambiguously truncated"
            ) from error
    else:
        try:
            AuditEvent.model_validate(decoded)
        except ValidationError as error:
            raise IntegrityError(
                "Final event journal record is complete but invalid; recovery is ambiguous"
            ) from error
        raise IntegrityError(
            "Final event journal record is complete but lacks its newline delimiter; "
            "recovery is ambiguous"
        )
    return JournalRecoveryCandidate(raw, prefix, events, tail)


def render_event(event: AuditEvent) -> bytes:
    """Render one event deterministically as a newline-terminated JSON record."""
    return canonical_json_bytes(event.model_dump(mode="json")) + b"\n"


def calculate_event_hash(event: AuditEvent) -> str:
    """Hash every canonical event field except the self-referential event hash."""
    payload = event.model_dump(mode="json", exclude={"event_hash"})
    return canonical_json_digest(payload)


def seal_event(event: AuditEvent, previous_hash: str | None) -> AuditEvent:
    """Return an immutable event bound to the preceding validated journal head."""
    if event.previous_event_hash is not None or event.event_hash is not None:
        raise ConflictError("New journal events must be unsealed; FORGE assigns chain hashes")
    linked = event.model_copy(update={"previous_event_hash": previous_hash})
    return linked.model_copy(update={"event_hash": calculate_event_hash(linked)})


def validate_event_sequence(events: tuple[AuditEvent, ...]) -> None:
    """Validate ordering, identity, and either a complete M2 chain or legacy M1 form."""
    initiative_id: UUID | None = None
    event_ids: set[UUID] = set()
    for expected_sequence, event in enumerate(events, start=1):
        if event.sequence != expected_sequence:
            raise IntegrityError(
                "Event journal sequence mismatch: "
                f"expected {expected_sequence}, found {event.sequence}"
            )
        if initiative_id is None:
            initiative_id = event.initiative_id
        elif event.initiative_id != initiative_id:
            raise IntegrityError("Event journal contains more than one initiative ID")
        if event.id in event_ids:
            raise IntegrityError(f"Event journal contains duplicate event ID: {event.id}")
        event_ids.add(event.id)
    if not events:
        return
    legacy = all(
        event.previous_event_hash is None and event.event_hash is None for event in events
    )
    hashed = all(event.event_hash is not None for event in events)
    if legacy:
        return
    if not hashed:
        raise IntegrityError("Event journal mixes legacy unsealed and M2 hash-chained records")
    previous_hash: str | None = None
    for event in events:
        if event.previous_event_hash != previous_hash:
            raise IntegrityError(
                f"Event journal previous-hash mismatch at sequence {event.sequence}"
            )
        expected_hash = calculate_event_hash(event)
        if event.event_hash != expected_hash:
            raise IntegrityError(f"Event hash mismatch at sequence {event.sequence}")
        previous_hash = event.event_hash


def read_journal(path: Path) -> tuple[AuditEvent, ...]:
    """Read and strictly validate an entire event journal without repairing it."""
    return _parse_complete_journal(_read_journal_bytes(path))


def append_event(path: Path, event: AuditEvent) -> tuple[AuditEvent, ...]:
    """Seal, append, synchronize, and verify one event as the commit point."""
    from forge.storage.idempotency import stamp_event_for_current_mutation

    if not path.parent.is_dir():
        raise ConflictError(f"Event journal parent directory does not exist: {path.parent}")
    if path.parent.is_symlink() or path.is_symlink():
        raise SecurityError(f"Refusing to append through a symbolic link: {path}")
    event = stamp_event_for_current_mutation(event)
    existing = read_journal(path)
    if existing and existing[-1].event_hash is None:
        raise ConflictError(
            "Legacy M1 journal is read-only until the authorized M2 migration increment"
        )
    sealed = seal_event(event, existing[-1].event_hash if existing else None)
    candidate = (*existing, sealed)
    validate_event_sequence(candidate)
    rendered = render_event(sealed)
    if len(rendered) - 1 > MAX_EVENT_BYTES:
        raise IntegrityError(f"Event exceeds the {MAX_EVENT_BYTES}-byte journal record limit")

    mode = "ab" if path.exists() else "xb"
    try:
        with path.open(mode) as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as error:
        raise ConflictError(
            "Event journal appeared concurrently; M1 does not support concurrent writers"
        ) from error
    except OSError as error:
        raise IntegrityError(f"Cannot append event journal {path}: {error}") from error

    verified = read_journal(path)
    if verified != candidate:
        raise IntegrityError("Event journal verification did not reproduce the appended event")
    return verified
