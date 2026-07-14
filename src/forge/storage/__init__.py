"""Filesystem persistence services implemented through M1 Increment 2."""

from forge.storage.atomic import atomic_write_bytes
from forge.storage.journal import append_event, read_journal, render_event, validate_event_sequence
from forge.storage.repository import (
    InitializationResult,
    RepositoryLayout,
    discover_repository,
    initialize_repository,
)
from forge.storage.snapshots import (
    SnapshotIntegrityReport,
    StateReducer,
    append_event_and_update_snapshot,
    inspect_snapshot_integrity,
    load_snapshot,
    render_snapshot,
    replay_events,
    write_snapshot,
)

__all__ = [
    "InitializationResult",
    "RepositoryLayout",
    "SnapshotIntegrityReport",
    "StateReducer",
    "append_event",
    "append_event_and_update_snapshot",
    "atomic_write_bytes",
    "discover_repository",
    "initialize_repository",
    "inspect_snapshot_integrity",
    "load_snapshot",
    "read_journal",
    "render_event",
    "render_snapshot",
    "replay_events",
    "validate_event_sequence",
    "write_snapshot",
]
