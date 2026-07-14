"""Materialized-state replay, persistence, and integrity comparison."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from forge.contracts.events import AuditEvent
from forge.contracts.state import IntegrityState, MaterializedState
from forge.errors import IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.journal import append_event, read_journal, validate_event_sequence

MAX_SNAPSHOT_BYTES = 10_485_760
StateReducer = Callable[[MaterializedState | None, AuditEvent], MaterializedState]


def replay_events(
    events: Iterable[AuditEvent],
    reducer: StateReducer,
) -> MaterializedState | None:
    """Deterministically reduce a validated event sequence into current state.

    Increment 2 owns replay mechanics. Increment 3 supplies the domain-neutral workflow
    reducer so lifecycle semantics do not leak into persistence code.
    """
    ordered = tuple(events)
    validate_event_sequence(ordered)
    state: MaterializedState | None = None
    for event in ordered:
        state = reducer(state, event)
        if state.initiative_id != event.initiative_id:
            raise IntegrityError(
                f"Reducer produced initiative {state.initiative_id} for event "
                f"belonging to {event.initiative_id}"
            )
        state = state.model_copy(
            update={
                "integrity_state": IntegrityState.HEALTHY,
                "journal_head_sequence": event.sequence,
                "journal_head_hash": event.event_hash,
            }
        )
    return state


def render_snapshot(state: MaterializedState) -> bytes:
    """Render a deterministic, newline-terminated state snapshot."""
    payload = json.dumps(
        state.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return payload.encode("utf-8") + b"\n"


def load_snapshot(path: Path) -> MaterializedState:
    """Load one bounded and strictly validated materialized snapshot."""
    if path.is_symlink():
        raise SecurityError(f"Refusing to read a snapshot through a symbolic link: {path}")
    if not path.is_file():
        raise IntegrityError(f"Materialized snapshot is not a regular file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read materialized snapshot {path}: {error}") from error
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise IntegrityError(f"Materialized snapshot exceeds {MAX_SNAPSHOT_BYTES} bytes: {path}")
    try:
        return MaterializedState.model_validate_json(raw)
    except ValidationError as error:
        raise IntegrityError(f"Invalid materialized snapshot {path}: {error}") from error


def write_snapshot(path: Path, state: MaterializedState) -> None:
    """Atomically replace and verify a materialized snapshot."""
    rendered = render_snapshot(state)
    if len(rendered) > MAX_SNAPSHOT_BYTES:
        raise IntegrityError(f"Materialized snapshot exceeds {MAX_SNAPSHOT_BYTES} bytes")

    def validate_temporary(temporary: Path) -> None:
        if load_snapshot(temporary) != state:
            raise IntegrityError("Temporary snapshot did not reproduce the requested state")

    atomic_write_bytes(path, rendered, validator=validate_temporary)


@dataclass(frozen=True)
class SnapshotIntegrityReport:
    """Non-mutating comparison between authoritative history and derived state."""

    integrity_state: IntegrityState
    journal_event_count: int
    snapshot: MaterializedState | None
    replayed_state: MaterializedState | None
    diagnostics: tuple[str, ...] = ()

    @property
    def is_healthy(self) -> bool:
        return self.integrity_state is IntegrityState.HEALTHY

    @property
    def reported_state(self) -> MaterializedState | None:
        """Expose the observed state with an explicit integrity dimension."""
        base = self.snapshot if self.snapshot is not None else self.replayed_state
        if base is None:
            return None
        return base.model_copy(update={"integrity_state": self.integrity_state})


def inspect_snapshot_integrity(
    journal_path: Path,
    snapshot_path: Path,
    reducer: StateReducer,
) -> SnapshotIntegrityReport:
    """Compare ``state.json`` with deterministic replay without repairing either file."""
    events = read_journal(journal_path)
    replayed = replay_events(events, reducer)
    diagnostics: list[str] = []
    snapshot: MaterializedState | None = None
    snapshot_invalid = False
    if snapshot_path.exists():
        try:
            snapshot = load_snapshot(snapshot_path)
        except IntegrityError as error:
            snapshot_invalid = True
            diagnostics.append(str(error))

    if events and snapshot is None and not snapshot_invalid:
        diagnostics.append("The event journal has committed records but state.json is missing")
    elif not events and snapshot is not None and not snapshot_invalid:
        diagnostics.append("state.json exists without a committed event journal")
    elif not snapshot_invalid and snapshot != replayed:
        diagnostics.append("state.json does not match deterministic journal replay")

    integrity_state = (
        IntegrityState.INTEGRITY_ERROR if diagnostics else IntegrityState.HEALTHY
    )
    return SnapshotIntegrityReport(
        integrity_state=integrity_state,
        journal_event_count=len(events),
        snapshot=snapshot,
        replayed_state=replayed,
        diagnostics=tuple(diagnostics),
    )


def append_event_and_update_snapshot(
    journal_path: Path,
    snapshot_path: Path,
    event: AuditEvent,
    reducer: StateReducer,
) -> MaterializedState:
    """Commit an event, then atomically refresh its reconstructable state view.

    A pre-existing mismatch blocks the mutation. If snapshot writing fails after the
    append, the journal remains authoritative and the mismatch is detectable; Increment 2
    intentionally does not perform the explicit recovery assigned to M2.
    """
    before = inspect_snapshot_integrity(journal_path, snapshot_path, reducer)
    if not before.is_healthy:
        raise IntegrityError("; ".join(before.diagnostics))

    events = append_event(journal_path, event)
    state = replay_events(events, reducer)
    if state is None:
        raise IntegrityError("A committed event journal did not produce materialized state")
    write_snapshot(snapshot_path, state)

    after = inspect_snapshot_integrity(journal_path, snapshot_path, reducer)
    if not after.is_healthy:
        raise IntegrityError("; ".join(after.diagnostics))
    return state
