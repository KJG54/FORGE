"""Identity and supported-command authority contracts."""

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from forge.contracts.base import (
    NonEmptyString,
    SymbolicId,
    UtcDateTime,
    VersionedModel,
)


class ActorType(StrEnum):
    OWNER = "owner"
    HUMAN_CONTRIBUTOR = "human_contributor"
    FORGE_CLI = "forge_cli"
    AGENT_ADAPTER = "agent_adapter"
    EXTERNAL_TOOL = "external_tool"
    UNKNOWN_EXTERNAL_PROCESS = "unknown_external_process"
    MIGRATION = "migration"
    RECOVERY = "recovery"


class OwnerIdentity(VersionedModel):
    """Governance identity; this record does not provide authentication."""

    id: UUID
    display_name: NonEmptyString
    created_at: UtcDateTime
    local_metadata: dict[str, Any] = Field(default_factory=dict)


class Actor(VersionedModel):
    id: UUID
    actor_type: ActorType
    display_label: NonEmptyString
    tool_reference: NonEmptyString | None = None


class AuthorityGrant(VersionedModel):
    id: UUID
    actor_id: UUID
    allowed_action_class: SymbolicId
    scope: tuple[NonEmptyString, ...]
    granting_owner_decision_id: UUID
    valid_from: UtcDateTime
    valid_until: UtcDateTime | None = None
    version_scope: NonEmptyString | None = None
    revocation_id: UUID | None = None

    @model_validator(mode="after")
    def validate_time_window(self) -> "AuthorityGrant":
        if self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError("valid_until must not be earlier than valid_from")
        return self
