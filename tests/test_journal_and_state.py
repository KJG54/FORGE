from pathlib import Path
from uuid import UUID, uuid4

import pytest

from forge.contracts import (
    Actor,
    ActorType,
    AuditEvent,
    InitiativeLifecycleState,
    IntegrityState,
    MaterializedState,
    RepositoryState,
)
from forge.contracts.base import utc_now
from forge.errors import ConflictError, IntegrityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.canonical import canonical_json_bytes
from forge.storage.journal import append_event, read_journal, render_event
from forge.storage.snapshots import (
    append_event_and_update_snapshot,
    inspect_snapshot_integrity,
    load_snapshot,
    render_snapshot,
    replay_events,
    write_snapshot,
)


def _actor() -> Actor:
    return Actor(
        id=uuid4(),
        actor_type=ActorType.FORGE_CLI,
        display_label="FORGE CLI",
        tool_reference="forge 0.1.0a0",
    )


def _event(
    initiative_id: UUID,
    sequence: int,
    event_type: str,
    *,
    event_id: UUID | None = None,
    event_hash: str | None = None,
) -> AuditEvent:
    return AuditEvent(
        id=event_id or uuid4(),
        initiative_id=initiative_id,
        sequence=sequence,
        timestamp=utc_now(),
        event_type=event_type,
        actor=_actor(),
        authorization_basis="owner invoked supported CLI command",
        event_hash=event_hash,
    )


def _workflow_reducer(
    state: MaterializedState | None,
    event: AuditEvent,
) -> MaterializedState:
    if state is None:
        state = MaterializedState(
            repository_state=RepositoryState.INITIALIZED,
            initiative_id=event.initiative_id,
            lifecycle_state=InitiativeLifecycleState.ACTIVE,
        )
    if event.event_type == "initiative-paused":
        return state.model_copy(
            update={"lifecycle_state": InitiativeLifecycleState.PAUSED}
        )
    if event.event_type == "initiative-resumed":
        return state.model_copy(
            update={"lifecycle_state": InitiativeLifecycleState.ACTIVE}
        )
    return state


def test_atomic_write_validates_before_replace_and_cleans_temporary_files(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "state.json"
    destination.write_bytes(b"original\n")

    def reject(_: Path) -> None:
        raise IntegrityError("invalid temporary content")

    with pytest.raises(IntegrityError, match="invalid temporary content"):
        atomic_write_bytes(destination, b"replacement\n", validator=reject)

    assert destination.read_bytes() == b"original\n"
    assert list(tmp_path.glob(".state.json.*.tmp")) == []


def test_events_append_in_order_and_replay_to_an_atomic_snapshot(tmp_path: Path) -> None:
    journal = tmp_path / "events.jsonl"
    snapshot = tmp_path / "state.json"
    initiative_id = uuid4()

    first = append_event_and_update_snapshot(
        journal,
        snapshot,
        _event(initiative_id, 1, "initiative-created"),
        _workflow_reducer,
    )
    second = append_event_and_update_snapshot(
        journal,
        snapshot,
        _event(initiative_id, 2, "initiative-paused"),
        _workflow_reducer,
    )

    assert first.journal_head_sequence == 1
    assert second.journal_head_sequence == 2
    assert second.journal_head_hash is not None
    assert second.lifecycle_state is InitiativeLifecycleState.PAUSED
    assert read_journal(journal)[-1].sequence == 2
    assert load_snapshot(snapshot) == second
    assert snapshot.read_bytes() == render_snapshot(second)
    report = inspect_snapshot_integrity(journal, snapshot, _workflow_reducer)
    assert report.is_healthy
    assert report.diagnostics == ()


def test_journal_rejects_sequence_gaps_and_preserves_the_committed_prefix(
    tmp_path: Path,
) -> None:
    journal = tmp_path / "events.jsonl"
    initiative_id = uuid4()
    first = _event(initiative_id, 1, "initiative-created")
    sealed_first = append_event(journal, first)[-1]

    with pytest.raises(IntegrityError, match="expected 2, found 3"):
        append_event(journal, _event(initiative_id, 3, "initiative-paused"))

    assert read_journal(journal) == (sealed_first,)


def test_journal_rejects_mixed_initiatives_duplicate_ids_and_invalid_hashes(
    tmp_path: Path,
) -> None:
    initiative_id = uuid4()
    event_id = uuid4()
    first = _event(initiative_id, 1, "initiative-created", event_id=event_id)

    mixed = tmp_path / "mixed.jsonl"
    mixed.write_bytes(
        render_event(first) + render_event(_event(uuid4(), 2, "initiative-paused"))
    )
    with pytest.raises(IntegrityError, match="more than one initiative"):
        read_journal(mixed)

    duplicate = tmp_path / "duplicate.jsonl"
    duplicate.write_bytes(
        render_event(first)
        + render_event(_event(initiative_id, 2, "initiative-paused", event_id=event_id))
    )
    with pytest.raises(IntegrityError, match="duplicate event ID"):
        read_journal(duplicate)

    hash_claim = tmp_path / "hash-claim.jsonl"
    hash_claim.write_bytes(
        render_event(
            _event(
                initiative_id,
                1,
                "initiative-created",
                event_hash="sha256:" + "0" * 64,
            )
        )
    )
    with pytest.raises(IntegrityError, match="Event hash mismatch"):
        read_journal(hash_claim)


def test_canonical_json_is_stable_and_rejects_non_finite_numbers() -> None:
    assert canonical_json_bytes({"z": 1, "a": "é"}) == b'{"a":"\xc3\xa9","z":1}'
    with pytest.raises(IntegrityError, match="canonical JSON"):
        canonical_json_bytes({"invalid": float("nan")})


def test_hash_chain_detects_changed_removed_reordered_and_relinked_events(
    tmp_path: Path,
) -> None:
    journal = tmp_path / "events.jsonl"
    initiative_id = uuid4()
    for sequence, event_type in enumerate(
        ("initiative-created", "initiative-paused", "initiative-resumed"), start=1
    ):
        append_event(journal, _event(initiative_id, sequence, event_type))
    events = read_journal(journal)
    assert events[0].previous_event_hash is None
    assert events[1].previous_event_hash == events[0].event_hash
    assert events[2].previous_event_hash == events[1].event_hash

    changed = events[1].model_copy(update={"metadata": {"tampered": True}})
    journal.write_bytes(b"".join(render_event(item) for item in (events[0], changed, events[2])))
    with pytest.raises(IntegrityError, match="Event hash mismatch at sequence 2"):
        read_journal(journal)

    journal.write_bytes(render_event(events[0]) + render_event(events[2]))
    with pytest.raises(IntegrityError, match="expected 2, found 3"):
        read_journal(journal)

    journal.write_bytes(render_event(events[1]) + render_event(events[0]) + render_event(events[2]))
    with pytest.raises(IntegrityError, match="expected 1, found 2"):
        read_journal(journal)

    relinked = events[1].model_copy(update={"previous_event_hash": "sha256:" + "0" * 64})
    journal.write_bytes(
        render_event(events[0]) + render_event(relinked) + render_event(events[2])
    )
    with pytest.raises(IntegrityError, match="previous-hash mismatch at sequence 2"):
        read_journal(journal)


def test_legacy_m1_journal_is_readable_but_cannot_be_extended(tmp_path: Path) -> None:
    journal = tmp_path / "events.jsonl"
    initiative_id = uuid4()
    legacy = _event(initiative_id, 1, "initiative-created")
    journal.write_bytes(render_event(legacy))
    assert read_journal(journal) == (legacy,)
    with pytest.raises(ConflictError, match="Legacy M1 journal is read-only"):
        append_event(journal, _event(initiative_id, 2, "initiative-paused"))

    sealed = append_event(tmp_path / "hashed.jsonl", legacy)[-1]
    mixed = tmp_path / "mixed-chain.jsonl"
    second = _event(initiative_id, 2, "initiative-paused")
    mixed.write_bytes(render_event(sealed) + render_event(second))
    with pytest.raises(IntegrityError, match="mixes legacy unsealed"):
        read_journal(mixed)


def test_journal_rejects_truncated_or_blank_records(tmp_path: Path) -> None:
    journal = tmp_path / "events.jsonl"
    event = _event(uuid4(), 1, "initiative-created")
    journal.write_bytes(render_event(event).rstrip(b"\n"))
    with pytest.raises(IntegrityError, match="incomplete record"):
        read_journal(journal)

    journal.write_bytes(render_event(event) + b"\n")
    with pytest.raises(IntegrityError, match="blank record"):
        read_journal(journal)


def test_valid_but_stale_snapshot_reports_integrity_error_and_blocks_append(
    tmp_path: Path,
) -> None:
    journal = tmp_path / "events.jsonl"
    snapshot = tmp_path / "state.json"
    initiative_id = uuid4()
    state = append_event_and_update_snapshot(
        journal,
        snapshot,
        _event(initiative_id, 1, "initiative-created"),
        _workflow_reducer,
    )
    altered = state.model_copy(
        update={"lifecycle_state": InitiativeLifecycleState.PAUSED}
    )
    write_snapshot(snapshot, altered)

    report = inspect_snapshot_integrity(journal, snapshot, _workflow_reducer)
    assert report.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert report.reported_state is not None
    assert report.reported_state.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert report.diagnostics == (
        "state.json does not match deterministic journal replay",
    )

    with pytest.raises(IntegrityError, match="does not match"):
        append_event_and_update_snapshot(
            journal,
            snapshot,
            _event(initiative_id, 2, "initiative-paused"),
            _workflow_reducer,
        )
    assert len(read_journal(journal)) == 1


def test_invalid_snapshot_is_reported_as_integrity_error(tmp_path: Path) -> None:
    journal = tmp_path / "events.jsonl"
    snapshot = tmp_path / "state.json"
    event = _event(uuid4(), 1, "initiative-created")
    append_event(journal, event)
    snapshot.write_text("{not valid json}\n", encoding="utf-8")

    report = inspect_snapshot_integrity(journal, snapshot, _workflow_reducer)

    assert report.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert report.reported_state is not None
    assert report.reported_state.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert report.diagnostics[0].startswith("Invalid materialized snapshot")


def test_snapshot_failure_leaves_detectable_committed_journal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal = tmp_path / "events.jsonl"
    snapshot = tmp_path / "state.json"
    event = _event(uuid4(), 1, "initiative-created")

    def fail_snapshot(_: Path, __: MaterializedState) -> None:
        raise IntegrityError("simulated snapshot failure")

    monkeypatch.setattr("forge.storage.snapshots.write_snapshot", fail_snapshot)
    with pytest.raises(IntegrityError, match="simulated snapshot failure"):
        append_event_and_update_snapshot(journal, snapshot, event, _workflow_reducer)

    committed = read_journal(journal)
    assert len(committed) == 1
    assert committed[0].id == event.id
    assert committed[0].event_hash is not None
    report = inspect_snapshot_integrity(journal, snapshot, _workflow_reducer)
    assert report.integrity_state is IntegrityState.INTEGRITY_ERROR
    assert report.diagnostics == (
        "The event journal has committed records but state.json is missing",
    )


def test_replay_rejects_a_reducer_that_changes_initiative_identity() -> None:
    event = _event(uuid4(), 1, "initiative-created")

    def invalid_reducer(
        _: MaterializedState | None,
        __: AuditEvent,
    ) -> MaterializedState:
        return MaterializedState(
            repository_state=RepositoryState.INITIALIZED,
            initiative_id=uuid4(),
        )

    with pytest.raises(IntegrityError, match="Reducer produced initiative"):
        replay_events((event,), invalid_reducer)
