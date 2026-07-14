from __future__ import annotations

import json
import socket
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.errors import ConflictError, IntegrityError
from forge.storage.locking import (
    LOCK_NAME,
    LockOwner,
    lock_diagnostic,
    repository_mutation_lock,
)
from forge.storage.repository import initialize_repository

runner = CliRunner()


def test_lock_releases_after_success_and_failure(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    path = initialized.layout.lock_directory / LOCK_NAME
    with repository_mutation_lock(initialized.layout, command="test"):
        assert path.is_file()
        diagnostic = lock_diagnostic(initialized.layout)
        assert diagnostic is not None
        assert diagnostic.startswith("live mutation lock")
        with (
            pytest.raises(ConflictError, match="Repository mutation is locked"),
            repository_mutation_lock(initialized.layout, command="nested"),
        ):
            pass
    assert not path.exists()

    with (
        pytest.raises(RuntimeError, match="simulated"),
        repository_mutation_lock(initialized.layout, command="failure"),
    ):
        raise RuntimeError("simulated")
    assert not path.exists()


def test_cross_process_lock_blocks_cli_mutation_without_traceback(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    path = initialized.layout.lock_directory / LOCK_NAME
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert process.poll() is None
        owner = LockOwner(
            token="holder-token",
            pid=process.pid,
            hostname=socket.gethostname(),
            command="holder-process",
            created_at=datetime.now(UTC).isoformat(),
        )
        path.write_text(json.dumps(asdict(owner)), encoding="utf-8", newline="\n")
        blocked = runner.invoke(
            app,
            [
                "create",
                "Blocked objective",
                "--scope",
                "Lock test",
                "--trust-pack-data",
                "-C",
                str(tmp_path),
            ],
        )
        assert blocked.exit_code == 31
        assert "live mutation lock" in blocked.stderr
        assert "Traceback" not in blocked.stderr
    finally:
        path.unlink(missing_ok=True)
        process.terminate()
        process.wait(timeout=10)
    assert lock_diagnostic(initialized.layout) is None


def test_stale_and_invalid_locks_are_reported_but_never_removed(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")
    path = initialized.layout.lock_directory / LOCK_NAME
    stale = LockOwner(
        token="stale-token",
        pid=999_999_999,
        hostname="unreachable-host",
        command="interrupted-command",
        created_at="2026-07-14T00:00:00+00:00",
    )
    path.write_text(json.dumps(asdict(stale)), encoding="utf-8")
    diagnostic = lock_diagnostic(initialized.layout)
    assert diagnostic is not None
    assert diagnostic.startswith("stale mutation lock")
    doctor = runner.invoke(app, ["doctor", "-C", str(tmp_path)])
    assert doctor.exit_code == 0
    assert "Warning: stale mutation lock" in doctor.stdout
    assert path.exists()

    path.write_text("{invalid", encoding="utf-8")
    with pytest.raises(IntegrityError, match="metadata is invalid"):
        lock_diagnostic(initialized.layout)
    assert path.exists()
