"""Bounded reading for mutable, ungoverned conversational notes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from forge.errors import ConflictError, SecurityError
from forge.storage.repository import RepositoryLayout

MAX_SCRATCHPAD_BYTES = 65_536
SCRATCHPAD_HEADER = "<!-- FORGE SCRATCHPAD v1"
SCRATCHPAD_HEADER_END = "-->"


@dataclass(frozen=True)
class ScratchpadDocument:
    """One safely read local scratchpad; its content is never authoritative."""

    path: Path
    exists: bool
    byte_size: int
    modified_at: datetime | None
    initiative_id: UUID | None
    journal_sequence: int | None
    notes: str

    @property
    def empty(self) -> bool:
        return not self.notes


def _metadata_value(line: str, key: str) -> str:
    actual_key, separator, value = line.partition(":")
    if not separator or actual_key != key or not value.strip():
        raise ConflictError(
            f"Malformed local scratchpad metadata; expected '{key}: <value>'"
        )
    return value.strip()


def _has_unsafe_control_characters(text: str) -> bool:
    return any(
        (ord(character) < 32 and character not in "\t\n\r") or ord(character) == 127
        for character in text
    )


def _parse_scratchpad(text: str) -> tuple[UUID, int, str]:
    lines = text.splitlines()
    if len(lines) < 4 or lines[0] != SCRATCHPAD_HEADER or lines[3] != SCRATCHPAD_HEADER_END:
        raise ConflictError(
            "Malformed local scratchpad header; use the documented FORGE SCRATCHPAD v1 format"
        )
    try:
        initiative_id = UUID(_metadata_value(lines[1], "initiative_id"))
    except ValueError as error:
        raise ConflictError("Malformed local scratchpad initiative_id; expected a UUID") from error
    sequence_text = _metadata_value(lines[2], "journal_sequence")
    try:
        journal_sequence = int(sequence_text)
    except ValueError as error:
        raise ConflictError(
            "Malformed local scratchpad journal_sequence; expected a non-negative integer"
        ) from error
    if journal_sequence < 0 or str(journal_sequence) != sequence_text:
        raise ConflictError(
            "Malformed local scratchpad journal_sequence; expected a canonical non-negative integer"
        )
    notes = "\n".join(lines[4:]).strip()
    return initiative_id, journal_sequence, notes


def _missing(path: Path) -> ScratchpadDocument:
    return ScratchpadDocument(
        path=path,
        exists=False,
        byte_size=0,
        modified_at=None,
        initiative_id=None,
        journal_sequence=None,
        notes="",
    )


def read_scratchpad(layout: RepositoryLayout) -> ScratchpadDocument:
    """Read the advisory scratchpad without following links or accepting irregular files."""
    directory = layout.conversation_directory
    path = layout.scratchpad_file
    if directory.is_symlink():
        raise SecurityError(f"Refusing to read a symbolic local conversation path: {directory}")
    if not directory.exists():
        return _missing(path)
    if not directory.is_dir():
        raise ConflictError(f"Local conversation path is not a regular directory: {directory}")
    if path.is_symlink():
        raise SecurityError(f"Refusing to read a symbolic local scratchpad: {path}")
    if not path.exists():
        return _missing(path)
    if not path.is_file():
        raise ConflictError(f"Local scratchpad is not a regular file: {path}")
    try:
        before = path.stat()
        if before.st_size > MAX_SCRATCHPAD_BYTES:
            raise ConflictError(
                f"Local scratchpad exceeds the {MAX_SCRATCHPAD_BYTES}-byte limit: {path}"
            )
        raw = path.read_bytes()
        after = path.stat()
    except ConflictError:
        raise
    except OSError as error:
        raise ConflictError(f"Cannot safely read local scratchpad {path}: {error}") from error
    if path.is_symlink() or not path.is_file():
        raise ConflictError(f"Local scratchpad changed type while it was being read: {path}")
    if (
        len(raw) != before.st_size
        or len(raw) > MAX_SCRATCHPAD_BYTES
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise ConflictError(f"Local scratchpad changed while it was being read: {path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ConflictError(f"Local scratchpad must be valid UTF-8 Markdown: {path}") from error
    if _has_unsafe_control_characters(text):
        raise ConflictError("Malformed local scratchpad contains unsafe control characters")
    try:
        modified_at = datetime.fromtimestamp(after.st_mtime, tz=UTC)
    except (OSError, OverflowError, ValueError) as error:
        raise ConflictError(f"Local scratchpad has an invalid update time: {path}") from error
    if not text.strip():
        return ScratchpadDocument(
            path=path,
            exists=True,
            byte_size=len(raw),
            modified_at=modified_at,
            initiative_id=None,
            journal_sequence=None,
            notes="",
        )
    initiative_id, journal_sequence, notes = _parse_scratchpad(text)
    return ScratchpadDocument(
        path=path,
        exists=True,
        byte_size=len(raw),
        modified_at=modified_at,
        initiative_id=initiative_id,
        journal_sequence=journal_sequence,
        notes=notes,
    )
