"""Ordered JSON Lines persistence for M1 governance events."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from forge.contracts.events import AuditEvent
from forge.errors import ConflictError, IntegrityError, SecurityError

MAX_EVENT_BYTES = 1_048_576


def render_event(event: AuditEvent) -> bytes:
    """Render one event deterministically as a newline-terminated JSON record."""
    payload = json.dumps(
        event.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return payload.encode("utf-8") + b"\n"


def validate_event_sequence(events: tuple[AuditEvent, ...]) -> None:
    """Validate M1 ordering and single-initiative journal invariants."""
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
        if event.previous_event_hash is not None or event.event_hash is not None:
            raise IntegrityError(
                "M1 journals must not claim hash chaining; canonical event hashes begin in M2"
            )


def read_journal(path: Path) -> tuple[AuditEvent, ...]:
    """Read and strictly validate an entire M1 event journal."""
    if not path.exists():
        return ()
    if path.is_symlink():
        raise SecurityError(f"Refusing to read an event journal through a symbolic link: {path}")
    if not path.is_file():
        raise IntegrityError(f"Event journal is not a regular file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read event journal {path}: {error}") from error
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


def append_event(path: Path, event: AuditEvent) -> tuple[AuditEvent, ...]:
    """Append one validated event and synchronize it as the M1 commit point."""
    if not path.parent.is_dir():
        raise ConflictError(f"Event journal parent directory does not exist: {path.parent}")
    if path.parent.is_symlink() or path.is_symlink():
        raise SecurityError(f"Refusing to append through a symbolic link: {path}")
    existing = read_journal(path)
    candidate = (*existing, event)
    validate_event_sequence(candidate)
    rendered = render_event(event)
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
