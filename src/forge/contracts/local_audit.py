"""Structured local-only security and command-failure audit records."""

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from forge.contracts.base import (
    NonEmptyString,
    Sha256Digest,
    UtcDateTime,
    VersionedModel,
)


class LocalAuditCategory(StrEnum):
    CONFIGURATION = "configuration"
    AUTHORIZATION = "authorization"
    TRANSITION = "transition"
    INTEGRITY = "integrity"
    CONFLICT = "conflict"
    SECURITY = "security"
    EXTERNAL_TOOL = "external_tool"
    INTERNAL = "internal"


class LocalAuditSeverity(StrEnum):
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LocalAuditEvent(VersionedModel):
    """Non-authoritative local observation of one refused or failed CLI operation."""

    id: UUID
    project_id: UUID
    initiative_id: UUID | None = None
    configured_owner_id: UUID
    timestamp: UtcDateTime
    source: Literal["forge-cli"] = "forge-cli"
    operation: NonEmptyString
    category: LocalAuditCategory
    severity: LocalAuditSeverity
    outcome: Literal["refused"] = "refused"
    exit_code: Annotated[int, Field(ge=1, le=255)]
    error_type: NonEmptyString
    detail_digest: Sha256Digest
    tool_version: NonEmptyString
