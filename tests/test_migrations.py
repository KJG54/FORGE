from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

import forge.core.migrations as migrations
from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.migrations import MigrationRecord
from forge.core.archival import abandon_initiative, load_archive
from forge.core.authorization import owner_actor
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.migrations import inspect_active_migration, migrate_active_repository
from forge.core.status import inspect_status
from forge.errors import AuthorizationError, IntegrityError
from forge.storage.journal import read_journal, render_event
from forge.storage.migrations import (
    HASH_CHAIN_JOURNAL_FORMAT,
    LEGACY_JOURNAL_FORMAT,
    LEGACY_JOURNAL_MIGRATION_ID,
    registered_migrations,
)
from forge.storage.records import load_record
from forge.storage.repository import InitializationResult, initialize_repository
from forge.storage.snapshots import load_snapshot, write_snapshot

runner = CliRunner()


def _initialized(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Migrate a legacy governed initiative",
        declared_scope_summary="Exercise explicit schema migration",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _make_legacy(initialized: InitializationResult) -> bytes:
    layout = initialized.layout
    events = read_journal(layout.event_journal_file)
    legacy = tuple(
        event.model_copy(update={"previous_event_hash": None, "event_hash": None})
        for event in events
    )
    source = b"".join(render_event(event) for event in legacy)
    layout.event_journal_file.write_bytes(source)
    snapshot = load_snapshot(layout.state_file).model_copy(
        update={"journal_head_hash": None}
    )
    write_snapshot(layout.state_file, snapshot)
    assert load_active_initiative(layout).state.journal_head_hash is None
    return source


def _forge_bytes(initialized: InitializationResult) -> dict[Path, bytes]:
    return {
        path.relative_to(initialized.layout.root): path.read_bytes()
        for path in initialized.layout.forge_directory.rglob("*")
        if path.is_file()
    }


def test_registry_and_preview_are_deterministic_and_read_only(tmp_path: Path) -> None:
    initialized, _ = _initialized(tmp_path)
    _make_legacy(initialized)
    before = _forge_bytes(initialized)

    registry = registered_migrations()
    assert tuple(item.id for item in registry) == (LEGACY_JOURNAL_MIGRATION_ID,)
    inspection = inspect_active_migration(initialized.layout)
    assert inspection.plan.required
    assert inspection.plan.current_format == LEGACY_JOURNAL_FORMAT
    assert inspection.plan.target_format == HASH_CHAIN_JOURNAL_FORMAT
    assert inspect_status(initialized.layout).next_actions == ("migrate",)

    preview = runner.invoke(app, ["migrate", "-C", str(initialized.layout.root)])
    assert preview.exit_code == 0, preview.stderr
    assert "Migration required: yes" in preview.stdout
    assert LEGACY_JOURNAL_MIGRATION_ID in preview.stdout
    assert _forge_bytes(initialized) == before


def test_apply_preserves_exact_source_and_unlocks_hash_chained_work(
    tmp_path: Path,
) -> None:
    initialized, actor = _initialized(tmp_path)
    original = _make_legacy(initialized)
    result = runner.invoke(
        app,
        [
            "migrate",
            "--apply",
            "--idempotency-key",
            "migrate-legacy-journal",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert f"Completed migration {LEGACY_JOURNAL_MIGRATION_ID}" in result.stdout
    assert "Integrity: healthy" in result.stdout

    events = read_journal(initialized.layout.event_journal_file)
    assert len(events) == 2
    assert all(event.event_hash is not None for event in events)
    assert events[-1].event_type == "schema-migrated"
    record_id = events[-1].affected_record_ids[0]
    record = load_record(
        initialized.layout.migration_record_directory / f"{record_id}.json",
        MigrationRecord,
    )
    assert (initialized.layout.root / record.preserved_source_path).read_bytes() == original
    assert record.owner_actor.id == initialized.configuration.owner.id
    assert record.migration_actor.actor_type is ActorType.MIGRATION
    active = load_active_initiative(initialized.layout)
    assert active.state.journal_head_hash == events[-1].event_hash
    assert not inspect_active_migration(initialized.layout).plan.required

    replay = runner.invoke(
        app,
        [
            "migrate",
            "--apply",
            "--idempotency-key",
            "migrate-legacy-journal",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert replay.exit_code == 0, replay.stderr
    assert "Idempotent replay" in replay.stdout
    assert len(read_journal(initialized.layout.event_journal_file)) == 2
    active = load_active_initiative(initialized.layout)
    begin_manual_run(
        initialized.layout,
        step_id=active.workflow.steps[0].id,
        actor=actor,
    )
    assert len(read_journal(initialized.layout.event_journal_file)) == 3


def test_migration_requires_owner_and_rejects_corrupt_legacy_source(tmp_path: Path) -> None:
    initialized, _ = _initialized(tmp_path)
    _make_legacy(initialized)
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        migrate_active_repository(initialized.layout, actor=outsider)

    initialized.layout.event_journal_file.write_bytes(
        initialized.layout.event_journal_file.read_bytes().rstrip(b"\n")
    )
    before = _forge_bytes(initialized)
    result = runner.invoke(
        app,
        ["migrate", "--apply", "-C", str(initialized.layout.root)],
    )
    assert result.exit_code != 0
    assert "incomplete record" in result.stderr
    assert _forge_bytes(initialized) == before


def test_migration_resumes_after_journal_commit_without_duplicate_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, _ = _initialized(tmp_path)
    _make_legacy(initialized)
    original_write = migrations.write_snapshot
    failed = False

    def interrupt_once(path: Path, state: object) -> None:
        nonlocal failed
        if not failed:
            failed = True
            raise IntegrityError("simulated post-commit migration interruption")
        original_write(path, state)  # type: ignore[arg-type]

    monkeypatch.setattr(migrations, "write_snapshot", interrupt_once)
    arguments = [
        "migrate",
        "--apply",
        "--idempotency-key",
        "resume-schema-migration",
        "-C",
        str(initialized.layout.root),
    ]
    interrupted = runner.invoke(app, arguments)
    assert interrupted.exit_code != 0
    assert "post-commit migration interruption" in interrupted.stderr
    assert read_journal(initialized.layout.event_journal_file)[-1].event_type == "schema-migrated"

    monkeypatch.undo()
    resumed = runner.invoke(app, arguments)
    assert resumed.exit_code == 0, resumed.stderr
    assert "Resumed migration" in resumed.stdout
    assert len(
        [
            event
            for event in read_journal(initialized.layout.event_journal_file)
            if event.event_type == "schema-migrated"
        ]
    ) == 1
    assert load_active_initiative(initialized.layout).state.journal_head_hash is not None
    replay = runner.invoke(app, arguments)
    assert "Idempotent replay" in replay.stdout


def test_active_migration_does_not_modify_predecessor_archive(tmp_path: Path) -> None:
    initialized, actor = _initialized(tmp_path)
    predecessor_id = load_active_initiative(initialized.layout).initiative.id
    abandon_initiative(
        initialized.layout,
        reason="Create immutable predecessor fixture",
        unfinished_work_summary="The migration fixture remains unfinished",
        unresolved_risks=("No accepted outcome exists",),
        actor=actor,
    )
    create_initiative(
        initialized.layout,
        objective="Legacy successor requiring migration",
        declared_scope_summary="Migrate active state without touching its predecessor",
        actor=actor,
        trust_pack_data=True,
        predecessor_ids=(predecessor_id,),
    )
    _make_legacy(initialized)
    successor_id = load_active_initiative(initialized.layout).initiative.id
    archive_path = initialized.layout.archive_directory / str(predecessor_id)
    before = {
        path.relative_to(archive_path): path.read_bytes()
        for path in archive_path.rglob("*")
        if path.is_file()
    }

    result = runner.invoke(
        app,
        ["migrate", "--apply", "-C", str(initialized.layout.root)],
    )
    assert result.exit_code == 0, result.stderr
    after = {
        path.relative_to(archive_path): path.read_bytes()
        for path in archive_path.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert load_archive(initialized.layout, predecessor_id).manifest.initiative_id == predecessor_id
    abandon_initiative(
        initialized.layout,
        reason="Archive the successfully migrated successor fixture",
        unfinished_work_summary="The workflow remains intentionally unfinished",
        unresolved_risks=("No accepted outcome exists",),
        actor=actor,
    )
    migrated_archive = load_archive(initialized.layout, successor_id)
    assert migrated_archive.layout.migration_record_directory.is_dir()
    assert migrated_archive.layout.migration_source_directory.is_dir()


def test_preserved_migration_source_tampering_is_detected(tmp_path: Path) -> None:
    initialized, _ = _initialized(tmp_path)
    _make_legacy(initialized)
    applied = runner.invoke(
        app,
        ["migrate", "--apply", "-C", str(initialized.layout.root)],
    )
    assert applied.exit_code == 0, applied.stderr
    event = read_journal(initialized.layout.event_journal_file)[-1]
    record_id = event.affected_record_ids[0]
    source = initialized.layout.migration_source_directory / f"{record_id}.events.jsonl"
    source.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(IntegrityError, match="Preserved migration source is invalid"):
        load_active_initiative(initialized.layout)
