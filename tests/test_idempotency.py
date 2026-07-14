from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, cast

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.errors import IntegrityError
from forge.storage.idempotency import validate_idempotency_store
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout

runner = CliRunner()


class InvocationResult(Protocol):
    exit_code: int
    stdout: str
    stderr: str
    output: str


def _initialize(path: Path) -> RepositoryLayout:
    result = runner.invoke(app, ["init", str(path), "--owner-name", "Owner"])
    assert result.exit_code == 0, result.output
    return RepositoryLayout.at(path)


def _create(path: Path, *, key: str, objective: str = "Objective") -> InvocationResult:
    return cast(
        InvocationResult,
        runner.invoke(
            app,
            [
                "create",
                objective,
                "--scope",
                "Bounded scope",
                "--trust-pack-data",
                "--idempotency-key",
                key,
                "-C",
                str(path),
            ],
        ),
    )


def test_repeated_command_replays_without_duplicate_events(tmp_path: Path) -> None:
    layout = _initialize(tmp_path)
    first = _create(tmp_path, key="create-once")
    assert first.exit_code == 0, first.output
    assert "Idempotency key: create-once" in first.stdout
    original_journal = layout.event_journal_file.read_bytes()
    events = read_journal(layout.event_journal_file)
    assert len(events) == 1
    assert events[0].metadata["idempotency"]["key"] == "create-once"
    assert validate_idempotency_store(layout) == 1

    replay = _create(tmp_path, key="create-once")
    assert replay.exit_code == 0, replay.output
    assert "Idempotent replay; committed event(s):" in replay.stdout
    assert layout.event_journal_file.read_bytes() == original_journal

    conflict = _create(tmp_path, key="create-once", objective="Different objective")
    assert conflict.exit_code == 31
    assert "already used for a different command request" in conflict.stderr
    assert layout.event_journal_file.read_bytes() == original_journal


def test_multi_event_command_receipt_binds_every_event(tmp_path: Path) -> None:
    layout = _initialize(tmp_path)
    assert _create(tmp_path, key="create-for-begin").exit_code == 0
    for filename, role, key in (
        ("objective.md", "objective-and-constraints", "add-objective"),
        ("requirements.md", "requirements", "add-requirements"),
    ):
        (tmp_path / filename).write_text(role, encoding="utf-8")
        added = runner.invoke(
            app,
            [
                "artifact",
                "add",
                filename,
                "--role",
                role,
                "--title",
                role,
                "--idempotency-key",
                key,
                "-C",
                str(tmp_path),
            ],
        )
        assert added.exit_code == 0, added.output
    assert runner.invoke(
        app,
        [
            "begin",
            "discover",
            "--idempotency-key",
            "begin-once",
            "-C",
            str(tmp_path),
        ],
    ).exit_code == 0
    completed = runner.invoke(
        app,
        [
            "complete",
            "discover",
            "--assertion",
            "Discovery outputs are ready",
            "--idempotency-key",
            "complete-once",
            "-C",
            str(tmp_path),
        ],
    )
    assert completed.exit_code == 0, completed.output
    events = read_journal(layout.event_journal_file)
    matching = [
        event
        for event in events
        if event.metadata.get("idempotency", {}).get("key") == "complete-once"
    ]
    assert len(matching) == 2
    original_journal = layout.event_journal_file.read_bytes()
    assert validate_idempotency_store(layout) == 5

    replay = runner.invoke(
        app,
        [
            "complete",
            "discover",
            "--assertion",
            "Discovery outputs are ready",
            "--idempotency-key",
            "complete-once",
            "-C",
            str(tmp_path),
        ],
    )
    assert replay.exit_code == 0, replay.output
    assert "Idempotent replay" in replay.stdout
    assert layout.event_journal_file.read_bytes() == original_journal


def test_interrupted_receipt_write_blocks_retry_without_duplication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = _initialize(tmp_path)

    def fail_receipt(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated receipt failure")

    with monkeypatch.context() as context:
        context.setattr("forge.storage.idempotency.write_record", fail_receipt)
        interrupted = _create(tmp_path, key="interrupted-create")
    assert interrupted.exit_code == 30
    assert "simulated receipt failure" in interrupted.stderr
    committed = layout.event_journal_file.read_bytes()
    assert len(read_journal(layout.event_journal_file)) == 1

    retry = _create(tmp_path, key="interrupted-create")
    assert retry.exit_code == 30
    assert "committed events without a completion receipt" in retry.stderr
    assert "explicit recovery is required" in retry.stderr
    assert layout.event_journal_file.read_bytes() == committed


def test_tampered_receipt_is_detected(tmp_path: Path) -> None:
    layout = _initialize(tmp_path)
    assert _create(tmp_path, key="tamper-receipt").exit_code == 0
    receipt_path = next(layout.idempotency_directory.glob("*.json"))
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["request_digest"] = "sha256:" + "0" * 64
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(IntegrityError, match="metadata disagrees"):
        validate_idempotency_store(layout)
