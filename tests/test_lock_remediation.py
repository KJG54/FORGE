from __future__ import annotations

import json
import os
import socket
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.locking import LockRemediationRecord
from forge.core.authorization import forge_cli_actor, owner_actor
from forge.core.lock_remediation import remediate_stale_lock
from forge.errors import AuthorizationError, ConflictError, IntegrityError, SecurityError
from forge.storage.locking import (
    LOCK_NAME,
    REMEDIATION_LOCK_NAME,
    LockOwner,
    RemediationLockOwner,
    repository_mutation_lock,
    stale_lock_remediation_guard,
)
from forge.storage.records import load_record
from forge.storage.repository import initialize_repository

runner = CliRunner()
DEAD_PID = 999_999_999


class InvocationResult(Protocol):
    exit_code: int
    stdout: str
    stderr: str
    output: str


def _write_lock(path: Path, owner: LockOwner, *, newline: bytes = b"\n") -> bytes:
    content = json.dumps(asdict(owner), ensure_ascii=False, sort_keys=True).encode() + newline
    path.write_bytes(content)
    return content


def _stale_owner(*, token: str = "stale-token", host: str | None = None) -> LockOwner:
    return LockOwner(
        token=token,
        pid=DEAD_PID,
        hostname=socket.gethostname() if host is None else host,
        command="interrupted-command",
        created_at="2026-07-17T12:00:00+00:00",
    )


def _invoke(path: Path, *, key: str = "remove-stale-lock") -> InvocationResult:
    return cast(
        InvocationResult,
        runner.invoke(
            app,
            [
                "remediate-lock",
                "--reason",
                "Confirmed the original process exited unexpectedly",
                "--idempotency-key",
                key,
                "-C",
                str(path),
            ],
        ),
    )


def test_cli_preserves_exact_stale_lock_and_replays_without_governed_mutation(
    tmp_path: Path,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    lock_path = initialized.layout.lock_directory / LOCK_NAME
    original = _write_lock(lock_path, _stale_owner(), newline=b"\r\n")

    result = _invoke(tmp_path)
    assert result.exit_code == 0, result.output
    assert "Completed stale-lock remediation" in result.stdout
    assert "Governed initiative state: unchanged" in result.stdout
    assert not lock_path.exists()
    operation = next(initialized.layout.lock_remediation_directory.iterdir())
    preserved = operation / LOCK_NAME
    record = load_record(operation / "record.json", LockRemediationRecord)
    assert preserved.read_bytes() == original
    assert record.source_owner_pid == DEAD_PID
    assert record.source_owner_hostname == socket.gethostname()
    assert record.preserved_lock_path == preserved.relative_to(tmp_path).as_posix()
    assert not (initialized.layout.active_directory / "events.jsonl").exists()

    replay = _invoke(tmp_path)
    assert replay.exit_code == 0, replay.output
    assert "Idempotent replay of stale-lock remediation" in replay.stdout
    assert preserved.read_bytes() == original

    created = runner.invoke(
        app,
        [
            "create",
            "Work after lock remediation",
            "--scope",
            "Lock test",
            "--trust-pack-data",
            "--idempotency-key",
            "post-remediation-create",
            "-C",
            str(tmp_path),
        ],
    )
    assert created.exit_code == 0, created.output
    doctor = runner.invoke(app, ["doctor", "-C", str(tmp_path)])
    assert doctor.exit_code == 0, doctor.output
    assert "local stale-lock remediations (1)" in doctor.stdout


@pytest.mark.parametrize(
    ("owner", "message"),
    [
        (
            LockOwner(
                token="live-token",
                pid=os.getpid(),
                hostname=socket.gethostname(),
                command="live-command",
                created_at=datetime.now(UTC).isoformat(),
            ),
            "still live",
        ),
        (_stale_owner(host="another-host"), "cannot be proven stale locally"),
    ],
)
def test_live_and_foreign_host_locks_are_never_removed(
    tmp_path: Path,
    owner: LockOwner,
    message: str,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    lock_path = initialized.layout.lock_directory / LOCK_NAME
    original = _write_lock(lock_path, owner)

    result = _invoke(tmp_path)
    assert result.exit_code == 31
    assert message in result.stderr
    assert lock_path.read_bytes() == original
    assert tuple(initialized.layout.lock_remediation_directory.iterdir()) == ()


def test_malformed_and_symbolic_locks_are_refused_without_removal(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    lock_path = initialized.layout.lock_directory / LOCK_NAME
    lock_path.write_text("{invalid", encoding="utf-8")
    malformed = _invoke(tmp_path, key="malformed-lock")
    assert malformed.exit_code == 30
    assert "metadata is invalid" in malformed.stderr
    assert lock_path.exists()

    lock_path.unlink()
    target = tmp_path / "outside-lock"
    target.write_text("not a lock", encoding="utf-8")
    try:
        lock_path.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")
    symbolic = _invoke(tmp_path, key="symbolic-lock")
    assert symbolic.exit_code == 40
    assert "symbolic" in symbolic.stderr
    assert lock_path.is_symlink()
    assert target.read_text(encoding="utf-8") == "not a lock"


def test_same_key_resumes_after_authorization_record_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    lock_path = initialized.layout.lock_directory / LOCK_NAME
    original = _write_lock(lock_path, _stale_owner())

    def fail_commit(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated interruption before atomic lock removal")

    with monkeypatch.context() as context:
        context.setattr("forge.core.lock_remediation._commit_removal", fail_commit)
        interrupted = _invoke(tmp_path, key="resume-lock-remediation")
    assert interrupted.exit_code == 30
    assert lock_path.read_bytes() == original
    operation = next(initialized.layout.lock_remediation_directory.iterdir())
    assert (operation / "record.json").is_file()
    assert not (operation / LOCK_NAME).exists()

    resumed = _invoke(tmp_path, key="resume-lock-remediation")
    assert resumed.exit_code == 0, resumed.output
    assert "Resumed stale-lock remediation" in resumed.stdout
    assert not lock_path.exists()
    assert (operation / LOCK_NAME).read_bytes() == original


def test_changed_lock_and_tampered_preserved_evidence_are_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    lock_path = initialized.layout.lock_directory / LOCK_NAME
    _write_lock(lock_path, _stale_owner())

    def fail_commit(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated interruption")

    with monkeypatch.context() as context:
        context.setattr("forge.core.lock_remediation._commit_removal", fail_commit)
        assert _invoke(tmp_path, key="changed-lock").exit_code == 30
    _write_lock(lock_path, _stale_owner(token="replacement-token"))
    changed = _invoke(tmp_path, key="changed-lock")
    assert changed.exit_code == 31
    assert "does not match" in changed.stderr
    assert lock_path.exists()

    lock_path.unlink()
    _write_lock(lock_path, _stale_owner(token="second-operation"))
    assert _invoke(tmp_path, key="tampered-evidence").exit_code == 0
    operations = tuple(initialized.layout.lock_remediation_directory.iterdir())
    completed = next(
        item
        for item in operations
        if load_record(item / "record.json", LockRemediationRecord).idempotency_key
        == "tampered-evidence"
    )
    (completed / LOCK_NAME).write_text("tampered", encoding="utf-8")
    tampered = _invoke(tmp_path, key="tampered-evidence")
    assert tampered.exit_code == 30
    assert "Preserved stale-lock evidence is invalid" in tampered.stderr
    doctor = runner.invoke(app, ["doctor", "-C", str(tmp_path)])
    assert doctor.exit_code == 30
    assert "Preserved stale-lock evidence is invalid" in doctor.stderr


def test_remediation_guard_blocks_mutations_and_same_key_takes_over_stale_guard(
    tmp_path: Path,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    layout = initialized.layout
    with (
        stale_lock_remediation_guard(layout, idempotency_key="guarded-operation"),
        pytest.raises(ConflictError, match="remediation is in progress"),
        repository_mutation_lock(layout, command="blocked-command"),
    ):
        pass

    stale_guard = RemediationLockOwner(
        token="stale-guard-token",
        pid=DEAD_PID,
        hostname=socket.gethostname(),
        command="remediate-lock",
        created_at="2026-07-17T12:00:00+00:00",
        idempotency_key="take-over-guard",
    )
    guard_path = layout.lock_directory / REMEDIATION_LOCK_NAME
    guard_path.write_text(json.dumps(asdict(stale_guard)), encoding="utf-8")
    _write_lock(layout.lock_directory / LOCK_NAME, _stale_owner())
    result = _invoke(tmp_path, key="take-over-guard")
    assert result.exit_code == 0, result.output
    assert not guard_path.exists()


def test_core_requires_configured_owner_authority_and_reason(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    layout = initialized.layout
    _write_lock(layout.lock_directory / LOCK_NAME, _stale_owner())
    configuration = initialized.configuration

    with pytest.raises(AuthorizationError, match="Only configured owner"):
        remediate_stale_lock(
            layout,
            project_id=configuration.project_id,
            owner_identity_id=configuration.owner.id,
            actor=forge_cli_actor(),
            reason="Unauthorized attempt",
            idempotency_key="unauthorized-remediation",
        )
    with pytest.raises(ConflictError, match="non-empty owner reason"):
        remediate_stale_lock(
            layout,
            project_id=configuration.project_id,
            owner_identity_id=configuration.owner.id,
            actor=owner_actor(configuration.owner),
            reason="  ",
            idempotency_key="missing-reason",
        )
    assert (layout.lock_directory / LOCK_NAME).exists()


def test_missing_lock_is_refused_without_creating_a_record(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    with pytest.raises(SecurityError, match="missing"):
        remediate_stale_lock(
            initialized.layout,
            project_id=initialized.configuration.project_id,
            owner_identity_id=initialized.configuration.owner.id,
            actor=owner_actor(initialized.configuration.owner),
            reason="No lock exists",
            idempotency_key="missing-lock",
        )
    assert tuple(initialized.layout.lock_remediation_directory.iterdir()) == ()
