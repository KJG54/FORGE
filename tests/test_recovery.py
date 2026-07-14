from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, cast

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.recovery import RecoveryRecord, SnapshotCondition
from forge.errors import IntegrityError
from forge.storage.canonical import sha256_digest
from forge.storage.journal import read_journal
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout

runner = CliRunner()


class InvocationResult(Protocol):
    exit_code: int
    stdout: str
    stderr: str
    output: str


def _repository(path: Path) -> RepositoryLayout:
    initialized = runner.invoke(app, ["init", str(path), "--owner-name", "Owner"])
    assert initialized.exit_code == 0, initialized.output
    created = runner.invoke(
        app,
        [
            "create",
            "Recovery objective",
            "--scope",
            "Recovery test scope",
            "--trust-pack-data",
            "--idempotency-key",
            "create-recovery-test",
            "-C",
            str(path),
        ],
    )
    assert created.exit_code == 0, created.output
    return RepositoryLayout.at(path)


def _recover(path: Path, key: str = "recover-once") -> InvocationResult:
    return cast(
        InvocationResult,
        runner.invoke(
            app,
            [
                "recover",
                "--reason",
                "Owner authorized reconstruction",
                "--idempotency-key",
                key,
                "-C",
                str(path),
            ],
        ),
    )


def _recovery_records(layout: RepositoryLayout) -> list[RecoveryRecord]:
    return [
        load_record(path, RecoveryRecord)
        for path in sorted(layout.recovery_record_directory.glob("*.json"))
    ]


def test_missing_snapshot_is_reconstructed_with_governed_provenance(
    tmp_path: Path,
) -> None:
    layout = _repository(tmp_path)
    layout.state_file.unlink()

    recovered = _recover(tmp_path)

    assert recovered.exit_code == 0, recovered.output
    assert "Integrity: healthy" in recovered.stdout
    records = _recovery_records(layout)
    assert len(records) == 1
    assert records[0].snapshot_condition is SnapshotCondition.MISSING
    assert records[0].preserved_snapshot_path is None
    events = read_journal(layout.event_journal_file)
    assert events[-1].event_type == "integrity-recovered"
    assert events[-1].affected_record_ids == (records[0].id,)
    doctor = runner.invoke(app, ["doctor", "-C", str(tmp_path)])
    assert doctor.exit_code == 0, doctor.output


@pytest.mark.parametrize("valid_json", [False, True])
def test_observed_snapshot_is_preserved_exactly(
    tmp_path: Path,
    valid_json: bool,
) -> None:
    layout = _repository(tmp_path)
    if valid_json:
        payload = json.loads(layout.state_file.read_text(encoding="utf-8"))
        payload["current_step_id"] = None
        original = json.dumps(payload).encode("utf-8")
    else:
        original = b"not valid state json\r\n"
    layout.state_file.write_bytes(original)

    recovered = _recover(tmp_path)

    assert recovered.exit_code == 0, recovered.output
    record = _recovery_records(layout)[0]
    expected_condition = (
        SnapshotCondition.MISMATCHED if valid_json else SnapshotCondition.INVALID
    )
    assert record.snapshot_condition is expected_condition
    assert record.preserved_snapshot_digest == sha256_digest(original)
    assert record.preserved_snapshot_size == len(original)
    assert record.preserved_snapshot_path is not None
    assert (layout.root / record.preserved_snapshot_path).read_bytes() == original


def test_damaged_journal_is_rejected_without_mutation(tmp_path: Path) -> None:
    layout = _repository(tmp_path)
    layout.state_file.write_bytes(b"bad snapshot")
    journal = layout.event_journal_file.read_bytes()
    layout.event_journal_file.write_bytes(journal[:-1])
    observed_journal = layout.event_journal_file.read_bytes()
    observed_snapshot = layout.state_file.read_bytes()

    recovered = _recover(tmp_path)

    assert recovered.exit_code == 30
    assert "incomplete record" in recovered.stderr
    assert layout.event_journal_file.read_bytes() == observed_journal
    assert layout.state_file.read_bytes() == observed_snapshot
    assert not layout.recovery_record_directory.exists()


def test_healthy_snapshot_recovery_is_rejected(tmp_path: Path) -> None:
    layout = _repository(tmp_path)
    original_journal = layout.event_journal_file.read_bytes()

    recovered = _recover(tmp_path)

    assert recovered.exit_code == 31
    assert "already healthy" in recovered.stderr
    assert layout.event_journal_file.read_bytes() == original_journal
    assert not layout.recovery_record_directory.exists()


def test_missing_preserved_object_is_rejected_before_recovery_commit(
    tmp_path: Path,
) -> None:
    layout = _repository(tmp_path)
    source = tmp_path / "objective.md"
    source.write_text("governed objective", encoding="utf-8")
    added = runner.invoke(
        app,
        [
            "artifact",
            "add",
            source.name,
            "--role",
            "objective-and-constraints",
            "--title",
            "Objective",
            "--idempotency-key",
            "add-recovery-object",
            "-C",
            str(tmp_path),
        ],
    )
    assert added.exit_code == 0, added.output
    preserved_object = next(layout.object_directory.rglob("*"))
    if preserved_object.is_dir():
        preserved_object = next(path for path in preserved_object.rglob("*") if path.is_file())
    preserved_object.unlink()
    layout.state_file.write_bytes(b"bad snapshot")
    original_journal = layout.event_journal_file.read_bytes()

    recovered = _recover(tmp_path, key="missing-object-recovery")

    assert recovered.exit_code == 30
    assert "Preserved object" in recovered.stderr
    assert layout.event_journal_file.read_bytes() == original_journal
    assert layout.state_file.read_bytes() == b"bad snapshot"
    assert not layout.recovery_record_directory.exists()


def test_interrupted_snapshot_write_resumes_without_duplicate_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _repository(tmp_path)
    original_snapshot = b"bad snapshot"
    layout.state_file.write_bytes(original_snapshot)

    def fail_snapshot(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated recovery snapshot failure")

    with monkeypatch.context() as context:
        context.setattr("forge.core.recovery.write_snapshot", fail_snapshot)
        interrupted = _recover(tmp_path, key="resume-recovery")
    assert interrupted.exit_code == 30
    assert "simulated recovery snapshot failure" in interrupted.stderr
    committed = read_journal(layout.event_journal_file)
    assert sum(event.event_type == "integrity-recovered" for event in committed) == 1

    layout.state_file.write_bytes(b"different post-commit damage")
    unsafe_retry = _recover(tmp_path, key="resume-recovery")
    assert unsafe_retry.exit_code == 30
    assert "automatic resume is unsafe" in unsafe_retry.stderr
    assert sum(
        event.event_type == "integrity-recovered"
        for event in read_journal(layout.event_journal_file)
    ) == 1
    layout.state_file.write_bytes(original_snapshot)

    resumed = _recover(tmp_path, key="resume-recovery")

    assert resumed.exit_code == 0, resumed.output
    assert "Resumed recovery" in resumed.stdout
    events = read_journal(layout.event_journal_file)
    assert sum(event.event_type == "integrity-recovered" for event in events) == 1
    assert runner.invoke(app, ["doctor", "-C", str(tmp_path)]).exit_code == 0
