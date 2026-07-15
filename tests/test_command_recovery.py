from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, cast

import pytest
from pydantic import BaseModel
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.idempotency import CommandRecoveryRecord, IdempotencyReceipt
from forge.errors import IntegrityError
from forge.storage.idempotency import validate_idempotency_store
from forge.storage.journal import read_journal
from forge.storage.records import load_record, write_record
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


def _create(path: Path, key: str = "interrupted-create") -> InvocationResult:
    return cast(
        InvocationResult,
        runner.invoke(
            app,
            [
                "create",
                "Objective",
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


def _recover(
    path: Path,
    *,
    key: str = "receipt-recovery",
    interrupted_key: str = "interrupted-create",
) -> InvocationResult:
    return cast(
        InvocationResult,
        runner.invoke(
            app,
            [
                "recover-command",
                interrupted_key,
                "--reason",
                "Receipt write was interrupted after the event commit",
                "--idempotency-key",
                key,
                "-C",
                str(path),
            ],
        ),
    )


def _interrupt_receipt(
    path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> RepositoryLayout:
    layout = _initialize(path)

    def fail_receipt(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated receipt failure")

    with monkeypatch.context() as context:
        context.setattr("forge.storage.idempotency.write_record", fail_receipt)
        result = _create(path)
    assert result.exit_code == 30, result.output
    return layout


def _prepare_discover_step(path: Path) -> RepositoryLayout:
    layout = _initialize(path)
    assert _create(path, key="create-for-discover").exit_code == 0
    for filename, role, key in (
        ("objective.md", "objective-and-constraints", "add-objective"),
        ("requirements.md", "requirements", "add-requirements"),
    ):
        (path / filename).write_text(role, encoding="utf-8")
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
                str(path),
            ],
        )
        assert added.exit_code == 0, added.output
    begun = runner.invoke(
        app,
        [
            "begin",
            "discover",
            "--idempotency-key",
            "begin-discover",
            "-C",
            str(path),
        ],
    )
    assert begun.exit_code == 0, begun.output
    return layout


def _complete_discover(path: Path, key: str) -> InvocationResult:
    return cast(
        InvocationResult,
        runner.invoke(
            app,
            [
                "complete",
                "discover",
                "--assertion",
                "Discovery outputs are ready",
                "--idempotency-key",
                key,
                "-C",
                str(path),
            ],
        ),
    )


def test_recovers_exact_missing_receipt_with_owner_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _interrupt_receipt(tmp_path, monkeypatch)

    result = _recover(tmp_path)
    assert result.exit_code == 0, result.output
    assert "Completed command receipt recovery" in result.stdout
    events = read_journal(layout.event_journal_file)
    assert [event.event_type for event in events] == [
        "initiative-created",
        "command-recovered",
    ]
    assert events[-1].metadata["interrupted_key"] == "interrupted-create"
    assert validate_idempotency_store(layout) == 2
    record_path = next(layout.command_recovery_record_directory.glob("*.json"))
    record = load_record(record_path, CommandRecoveryRecord)
    assert record.recovered_events[0].event_id == events[0].id
    assert record.recovered_receipt_digest in events[-1].affected_digests

    journal = layout.event_journal_file.read_bytes()
    replay = _create(tmp_path)
    assert replay.exit_code == 0
    assert "Idempotent replay" in replay.stdout
    assert layout.event_journal_file.read_bytes() == journal
    doctor = runner.invoke(app, ["doctor", "-C", str(tmp_path)])
    assert doctor.exit_code == 0, doctor.output


def test_recovery_resumes_after_event_commit_without_duplication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _interrupt_receipt(tmp_path, monkeypatch)

    def fail_recovered_receipt(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated recovered receipt failure")

    with monkeypatch.context() as context:
        context.setattr(
            "forge.core.command_recovery.write_recovered_receipt",
            fail_recovered_receipt,
        )
        interrupted = _recover(tmp_path, key="resume-receipt-recovery")
    assert interrupted.exit_code == 30
    assert len(read_journal(layout.event_journal_file)) == 2

    resumed = _recover(tmp_path, key="resume-receipt-recovery")
    assert resumed.exit_code == 0, resumed.output
    assert "Resumed command receipt recovery" in resumed.stdout
    assert len(read_journal(layout.event_journal_file)) == 2
    assert validate_idempotency_store(layout) == 2


def test_recovery_resumes_after_target_receipt_before_recovery_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _interrupt_receipt(tmp_path, monkeypatch)

    def fail_recovery_receipt(
        path: Path,
        record: BaseModel,
        *,
        overwrite: bool = False,
    ) -> None:
        if isinstance(record, IdempotencyReceipt) and record.key == "finish-recovery-receipt":
            raise IntegrityError("simulated recovery-operation receipt failure")
        write_record(path, record, overwrite=overwrite)

    with monkeypatch.context() as context:
        context.setattr("forge.storage.idempotency.write_record", fail_recovery_receipt)
        interrupted = _recover(tmp_path, key="finish-recovery-receipt")
    assert interrupted.exit_code == 30
    assert len(read_journal(layout.event_journal_file)) == 2
    receipts = tuple(layout.idempotency_directory.glob("*.json"))
    assert len(receipts) == 1
    assert load_record(receipts[0], IdempotencyReceipt).key == "interrupted-create"

    resumed = _recover(tmp_path, key="finish-recovery-receipt")
    assert resumed.exit_code == 0, resumed.output
    assert "Resumed command receipt recovery" in resumed.stdout
    assert len(read_journal(layout.event_journal_file)) == 2
    assert validate_idempotency_store(layout) == 2


def test_recovers_only_complete_multi_event_command_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _prepare_discover_step(tmp_path)

    def fail_receipt(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated multi-event receipt failure")

    with monkeypatch.context() as context:
        context.setattr("forge.storage.idempotency.write_record", fail_receipt)
        interrupted = _complete_discover(tmp_path, "interrupted-complete")
    assert interrupted.exit_code == 30
    matching = [
        event
        for event in read_journal(layout.event_journal_file)
        if event.metadata.get("idempotency", {}).get("key") == "interrupted-complete"
    ]
    assert [event.event_type for event in matching] == [
        "claim-recorded",
        "step-transitioned",
    ]

    recovered = _recover(
        tmp_path,
        key="recover-complete",
        interrupted_key="interrupted-complete",
    )
    assert recovered.exit_code == 0, recovered.output
    assert "Recovered event(s): 2" in recovered.stdout


def test_refuses_partial_multi_event_command_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _prepare_discover_step(tmp_path)

    def fail_transition(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated transition interruption")

    with monkeypatch.context() as context:
        context.setattr(
            "forge.core.verification.apply_record_backed_transition",
            fail_transition,
        )
        interrupted = _complete_discover(tmp_path, "partial-complete")
    assert interrupted.exit_code == 30
    matching = [
        event
        for event in read_journal(layout.event_journal_file)
        if event.metadata.get("idempotency", {}).get("key") == "partial-complete"
    ]
    assert [event.event_type for event in matching] == ["claim-recorded"]

    refused = _recover(
        tmp_path,
        key="refuse-partial-complete",
        interrupted_key="partial-complete",
    )
    assert refused.exit_code == 30
    assert "event group is partial or ambiguous" in refused.stderr
    assert len(read_journal(layout.event_journal_file)) == 5


def test_refuses_changed_receipt_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _interrupt_receipt(tmp_path, monkeypatch)
    receipt_directory = layout.idempotency_directory
    receipt_directory.mkdir(exist_ok=True)
    extra: dict[str, object] = {
        "schema_version": "1.0.0",
        "key": "unrelated",
        "command": "pause",
        "request_digest": "sha256:" + "0" * 64,
        "completed_at": "2026-07-15T00:00:00Z",
        "events": [],
    }
    (receipt_directory / ("0" * 64 + ".json")).write_text(json.dumps(extra), encoding="utf-8")

    result = _recover(tmp_path)
    assert result.exit_code == 30
    assert "Invalid governed record" in result.stderr
    assert len(read_journal(layout.event_journal_file)) == 1


def test_refuses_non_atomic_snapshot_condition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _interrupt_receipt(tmp_path, monkeypatch)
    layout.state_file.write_text("{}", encoding="utf-8")

    result = _recover(tmp_path)
    assert result.exit_code == 30
    assert "not an atomic interruption boundary" in result.stderr
    assert len(read_journal(layout.event_journal_file)) == 1


def test_refuses_recovery_when_receipt_already_exists(tmp_path: Path) -> None:
    _initialize(tmp_path)
    created = _create(tmp_path)
    assert created.exit_code == 0

    result = _recover(tmp_path)
    assert result.exit_code == 31
    assert "already has a completion receipt" in result.stderr


def test_recovers_exact_pre_command_snapshot_for_interrupted_pause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _initialize(tmp_path)
    assert _create(tmp_path, key="create-complete").exit_code == 0
    previous_snapshot = layout.state_file.read_bytes()

    def fail_receipt(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated pause receipt failure")

    with monkeypatch.context() as context:
        context.setattr("forge.storage.idempotency.write_record", fail_receipt)
        paused = runner.invoke(
            app,
            [
                "pause",
                "--reason",
                "Wait",
                "--idempotency-key",
                "interrupted-pause",
                "-C",
                str(tmp_path),
            ],
        )
    assert paused.exit_code == 30
    layout.state_file.write_bytes(previous_snapshot)

    recovered = _recover(
        tmp_path,
        key="recover-pause",
        interrupted_key="interrupted-pause",
    )
    assert recovered.exit_code == 0, recovered.output
    assert validate_idempotency_store(layout) == 3
    assert read_journal(layout.event_journal_file)[-1].event_type == "command-recovered"


def test_refuses_when_more_than_one_command_is_incomplete(tmp_path: Path) -> None:
    layout = _initialize(tmp_path)
    assert _create(tmp_path).exit_code == 0
    paused = runner.invoke(
        app,
        [
            "pause",
            "--reason",
            "Wait",
            "--idempotency-key",
            "pause-complete",
            "-C",
            str(tmp_path),
        ],
    )
    assert paused.exit_code == 0, paused.output
    for path in layout.idempotency_directory.glob("*.json"):
        path.unlink()

    result = _recover(tmp_path)
    assert result.exit_code == 30
    assert "committed events without a completion receipt" in result.stderr
    assert len(read_journal(layout.event_journal_file)) == 2


def test_tampered_recovery_provenance_is_detected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _interrupt_receipt(tmp_path, monkeypatch)
    assert _recover(tmp_path).exit_code == 0
    record_path = next(layout.command_recovery_record_directory.glob("*.json"))
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    payload["reason"] = "changed"
    record_path.write_text(json.dumps(payload), encoding="utf-8")

    doctor = runner.invoke(app, ["doctor", "-C", str(tmp_path)])
    assert doctor.exit_code == 30
    assert "Command recovery record does not match" in doctor.stderr


def test_recovery_provenance_survives_terminal_archival(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _interrupt_receipt(tmp_path, monkeypatch)
    assert _recover(tmp_path).exit_code == 0
    initiative_id = read_journal(layout.event_journal_file)[0].initiative_id

    abandoned = runner.invoke(
        app,
        [
            "abandon",
            "--reason",
            "Stop after recovery validation",
            "--unfinished-work",
            "Workflow was not started",
            "--risk",
            "Objective remains unfinished",
            "--idempotency-key",
            "archive-recovered-command",
            "-C",
            str(tmp_path),
        ],
    )
    assert abandoned.exit_code == 0, abandoned.output
    archived_record_directory = (
        layout.archive_directory / str(initiative_id) / "command-recovery-records"
    )
    assert len(tuple(archived_record_directory.glob("*.json"))) == 1
    doctor = runner.invoke(app, ["doctor", "-C", str(tmp_path)])
    assert doctor.exit_code == 0, doctor.output
