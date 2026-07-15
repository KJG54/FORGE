"""Registered, deterministic persisted-state migration primitives."""

from dataclasses import dataclass

from forge.contracts.base import SCHEMA_VERSION
from forge.contracts.events import AuditEvent
from forge.errors import IntegrityError
from forge.storage.journal import render_event, seal_event, validate_event_sequence

LEGACY_JOURNAL_FORMAT = "m1-unhashed-event-journal"
HASH_CHAIN_JOURNAL_FORMAT = "m2-sha256-event-chain"
LEGACY_JOURNAL_MIGRATION_ID = "legacy-m1-journal-to-m2-hash-chain-v1"
MAX_MIGRATION_SOURCE_BYTES = 104_857_600


@dataclass(frozen=True)
class MigrationDefinition:
    """One explicit directed migration edge in the supported registry."""

    id: str
    source_schema_version: str
    target_schema_version: str
    source_format: str
    target_format: str


@dataclass(frozen=True)
class MigrationPlan:
    """Read-only plan for the currently selected active initiative."""

    current_format: str
    target_format: str
    event_count: int
    definition: MigrationDefinition | None

    @property
    def required(self) -> bool:
        return self.definition is not None


LEGACY_JOURNAL_MIGRATION = MigrationDefinition(
    id=LEGACY_JOURNAL_MIGRATION_ID,
    source_schema_version=SCHEMA_VERSION,
    target_schema_version=SCHEMA_VERSION,
    source_format=LEGACY_JOURNAL_FORMAT,
    target_format=HASH_CHAIN_JOURNAL_FORMAT,
)
MIGRATION_REGISTRY = (LEGACY_JOURNAL_MIGRATION,)


def registered_migrations() -> tuple[MigrationDefinition, ...]:
    """Return the immutable migration registry in deterministic order."""
    return MIGRATION_REGISTRY


def plan_event_journal_migration(events: tuple[AuditEvent, ...]) -> MigrationPlan:
    """Select exactly one supported next edge for a validated journal."""
    if not events:
        raise IntegrityError("Active initiative journal is empty; migration is unsafe")
    legacy = all(
        event.previous_event_hash is None and event.event_hash is None for event in events
    )
    if legacy:
        return MigrationPlan(
            current_format=LEGACY_JOURNAL_FORMAT,
            target_format=HASH_CHAIN_JOURNAL_FORMAT,
            event_count=len(events),
            definition=LEGACY_JOURNAL_MIGRATION,
        )
    if all(event.event_hash is not None for event in events):
        return MigrationPlan(
            current_format=HASH_CHAIN_JOURNAL_FORMAT,
            target_format=HASH_CHAIN_JOURNAL_FORMAT,
            event_count=len(events),
            definition=None,
        )
    raise IntegrityError("Validated journal has no registered migration path")


def render_migrated_journal(
    legacy_events: tuple[AuditEvent, ...],
    migration_event: AuditEvent,
) -> tuple[bytes, tuple[AuditEvent, ...]]:
    """Seal legacy events and append one already-attributed migration event."""
    if not plan_event_journal_migration(legacy_events).required:
        raise IntegrityError("Journal is not a supported legacy migration source")
    sealed: list[AuditEvent] = []
    previous_hash: str | None = None
    for event in legacy_events:
        item = seal_event(event, previous_hash)
        sealed.append(item)
        previous_hash = item.event_hash
    sealed_migration = seal_event(migration_event, previous_hash)
    migrated = (*sealed, sealed_migration)
    validate_event_sequence(migrated)
    return b"".join(render_event(event) for event in migrated), migrated
