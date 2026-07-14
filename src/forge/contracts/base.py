"""Shared validation primitives for persisted FORGE contracts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)

SCHEMA_VERSION = "1.0"
SchemaVersion = Literal["1.0"]

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SymbolicId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$",
    ),
]
SemanticVersion = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=(
            r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
            r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
            r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
        ),
    ),
]
Sha256Digest = Annotated[
    str,
    StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$"),
]
IdempotencyKey = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    ),
]


def normalize_utc_datetime(value: datetime) -> datetime:
    """Normalize every persisted aware timestamp to canonical UTC."""
    return value.astimezone(UTC)


UtcDateTime = Annotated[datetime, AwareDatetime, AfterValidator(normalize_utc_datetime)]
RecordSequence = Annotated[int, Field(ge=1)]

_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def utc_now() -> datetime:
    """Return an aware UTC timestamp for newly created records."""
    return datetime.now(UTC)


def validate_repository_relative_path(value: str) -> str:
    """Validate and normalize the lexical form of a governed repository path.

    Filesystem and symlink-boundary validation is performed by the security layer.
    This validator makes persisted paths portable and rejects absolute or traversing
    representations on every supported operating system.
    """
    if "\x00" in value:
        raise ValueError("repository path must not contain a NUL byte")

    candidate = value.strip().replace("\\", "/")
    windows_path = PureWindowsPath(value)
    if (
        not candidate
        or candidate.startswith("/")
        or candidate.startswith("//")
        or _WINDOWS_DRIVE.match(candidate)
        or windows_path.is_absolute()
        or windows_path.drive
    ):
        raise ValueError("repository path must be relative")

    segments = candidate.split("/")
    if any(part in {"", ".", ".."} for part in segments):
        raise ValueError("repository path must be normalized and must not traverse")
    path = PurePosixPath(candidate)
    return path.as_posix()


RepositoryRelativePath = Annotated[str, AfterValidator(validate_repository_relative_path)]


class ForgeModel(BaseModel):
    """Strict immutable base for public FORGE data contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class VersionedModel(ForgeModel):
    """Base for independently persisted schema-versioned records."""

    schema_version: SchemaVersion = SCHEMA_VERSION


class GovernanceRecord(VersionedModel):
    """Audit metadata shared by initiative-scoped governance facts."""

    initiative_id: UUID
    actor_id: UUID
    recorded_at: UtcDateTime
    event_sequence: RecordSequence
    correlation_id: UUID | None = None
    run_id: UUID | None = None
    authorization_basis: NonEmptyString
    tool_version: NonEmptyString | None = None
    affected_record_ids: tuple[UUID, ...] = ()
    affected_digests: tuple[Sha256Digest, ...] = ()
