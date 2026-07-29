"""Rehearse M6 backup, migration, recovery, archival, abandonment, and succession."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import NoReturn

from forge import __version__
from forge.storage.journal import read_journal, render_event
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import load_snapshot, write_snapshot


class ProcedureRehearsalError(RuntimeError):
    """A release-procedure precondition or rehearsal failed."""


def _fail(message: str) -> NoReturn:
    raise ProcedureRehearsalError(message)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "NO_COLOR": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def _run(
    executable: Path,
    arguments: Sequence[str | Path],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    expected_output: str,
) -> str:
    command = [str(executable), *(str(item) for item in arguments)]
    result = subprocess.run(
        command,
        cwd=cwd,
        env=dict(environment),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        shell=False,
        timeout=30,
    )
    if result.returncode != 0:
        _fail(
            f"Command exited with {result.returncode}: "
            f"{subprocess.list2cmdline(command)}\n{result.stderr}"
        )
    if expected_output not in result.stdout:
        _fail(
            f"Command omitted {expected_output!r}: "
            f"{subprocess.list2cmdline(command)}"
        )
    return result.stdout


def _run_expected_failure(
    executable: Path,
    arguments: Sequence[str | Path],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    expected_output: str,
) -> None:
    command = [str(executable), *(str(item) for item in arguments)]
    result = subprocess.run(
        command,
        cwd=cwd,
        env=dict(environment),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        shell=False,
        timeout=30,
    )
    combined = result.stdout + result.stderr
    if result.returncode == 0:
        _fail(f"Command unexpectedly succeeded: {subprocess.list2cmdline(command)}")
    if expected_output not in combined:
        _fail(
            f"Failed command omitted {expected_output!r}: "
            f"{subprocess.list2cmdline(command)}"
        )


def _value(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            value = line.removeprefix(prefix).strip()
            if value:
                return value
    _fail(f"Command output omitted value prefix {prefix!r}")


def _initialize_active(
    executable: Path,
    repository: Path,
    *,
    environment: Mapping[str, str],
    objective: str,
) -> str:
    repository.mkdir()
    _run(
        executable,
        ("init", repository, "--owner-name", "Release Procedure Owner"),
        cwd=repository.parent,
        environment=environment,
        expected_output="Initialized FORGE repository",
    )
    created = _run(
        executable,
        (
            "create",
            objective,
            "--scope",
            "Synthetic release-procedure rehearsal only",
            "--pack",
            "software-basic",
            "--trust-pack-data",
            "-C",
            repository,
        ),
        cwd=repository.parent,
        environment=environment,
        expected_output="Created initiative ",
    )
    return _value(created, "Created initiative ")


def _make_legacy_journal(repository: Path) -> None:
    layout = RepositoryLayout.at(repository)
    events = read_journal(layout.event_journal_file)
    legacy = tuple(
        event.model_copy(
            update={
                "metadata": {
                    key: value
                    for key, value in event.metadata.items()
                    if key != "idempotency"
                },
                "previous_event_hash": None,
                "event_hash": None,
            }
        )
        for event in events
    )
    layout.event_journal_file.write_bytes(
        b"".join(render_event(event) for event in legacy)
    )
    snapshot = load_snapshot(layout.state_file).model_copy(
        update={"journal_head_hash": None}
    )
    write_snapshot(layout.state_file, snapshot)
    # The legacy format predates M2 command receipts. The CLI-created fixture has
    # receipts only because setup used today's supported command surface.
    for receipt in layout.idempotency_directory.glob("*.json"):
        receipt.unlink()


def _rehearse_backup_migration_recovery(
    executable: Path,
    root: Path,
    environment: Mapping[str, str],
) -> dict[str, str]:
    repository = root / "upgrade-recovery"
    _initialize_active(
        executable,
        repository,
        environment=environment,
        objective="Rehearse backup migration and recovery",
    )

    backup = root / "complete-backup"
    shutil.copytree(repository, backup)
    _run(
        executable,
        ("doctor", "-C", backup),
        cwd=root,
        environment=environment,
        expected_output="FORGE repository health: healthy",
    )

    _make_legacy_journal(repository)
    _run(
        executable,
        ("migrate", "-C", repository),
        cwd=root,
        environment=environment,
        expected_output="Migration required: yes",
    )
    _run(
        executable,
        (
            "migrate",
            "--apply",
            "--idempotency-key",
            "release-upgrade-rehearsal",
            "-C",
            repository,
        ),
        cwd=root,
        environment=environment,
        expected_output="Integrity: healthy",
    )

    layout = RepositoryLayout.at(repository)
    layout.state_file.unlink()
    _run_expected_failure(
        executable,
        ("doctor", "-C", repository),
        cwd=root,
        environment=environment,
        expected_output="state.json is missing",
    )
    _run(
        executable,
        (
            "recover",
            "--reason",
            "Rehearse recovery of a missing derived snapshot",
            "--idempotency-key",
            "release-snapshot-recovery",
            "-C",
            repository,
        ),
        cwd=root,
        environment=environment,
        expected_output="Completed recovery ",
    )
    _run(
        executable,
        ("doctor", "-C", repository),
        cwd=root,
        environment=environment,
        expected_output="FORGE repository health: healthy",
    )

    restored = root / "restored-backup"
    shutil.copytree(backup, restored)
    _run(
        executable,
        ("doctor", "-C", restored),
        cwd=root,
        environment=environment,
        expected_output="FORGE repository health: healthy",
    )
    return {
        "backup": "passed",
        "migration": "passed",
        "snapshot_recovery": "passed",
        "restore": "passed",
    }


def _rehearse_abandonment_successor(
    executable: Path,
    root: Path,
    environment: Mapping[str, str],
) -> dict[str, str]:
    repository = root / "abandonment-successor"
    predecessor_id = _initialize_active(
        executable,
        repository,
        environment=environment,
        objective="Rehearse abandonment and successor lineage",
    )
    _run(
        executable,
        (
            "abandon",
            "--reason",
            "Exercise explicit non-success terminal handling",
            "--unfinished-work",
            "All synthetic workflow outputs remain unfinished",
            "--risk",
            "No project outcome was accepted",
            "-C",
            repository,
        ),
        cwd=root,
        environment=environment,
        expected_output="Atomic M2 abandonment archive created",
    )
    _run(
        executable,
        ("status", "--archive", predecessor_id, "-C", repository),
        cwd=root,
        environment=environment,
        expected_output="Lifecycle: abandoned",
    )
    successor = _run(
        executable,
        (
            "create",
            "Rehearse a fresh successor",
            "--scope",
            "Synthetic successor lineage only",
            "--predecessor",
            predecessor_id,
            "--pack",
            "software-basic",
            "--trust-pack-data",
            "-C",
            repository,
        ),
        cwd=root,
        environment=environment,
        expected_output=f"Predecessor: {predecessor_id}",
    )
    successor_id = _value(successor, "Created initiative ")
    if successor_id == predecessor_id:
        _fail("Successor reused the predecessor initiative identity")
    _run(
        executable,
        ("doctor", "-C", repository),
        cwd=root,
        environment=environment,
        expected_output="FORGE repository health: healthy",
    )
    return {
        "abandonment": "passed",
        "archive_access": "passed",
        "successor": "passed",
    }


@contextmanager
def rehearsal_root(requested: Path | None) -> Generator[Path]:
    """Yield a new procedure root and preserve a caller-requested directory."""

    if requested is None:
        with tempfile.TemporaryDirectory(
            prefix="forge-release-procedures-"
        ) as temporary:
            yield Path(temporary)
        return
    resolved = requested.resolve()
    if resolved.exists():
        _fail(f"Refusing to use an existing procedure work directory: {resolved}")
    resolved.mkdir(parents=True)
    yield resolved


def run_rehearsal(
    *,
    forge_executable: Path,
    work_directory: Path | None = None,
) -> dict[str, object]:
    """Run the maintained non-destructive release-procedure scenarios."""

    executable = forge_executable.resolve(strict=True)
    if not executable.is_file():
        _fail(f"FORGE executable is not a regular file: {executable}")
    environment = _environment()
    _run(
        executable,
        ("--version",),
        cwd=Path.cwd(),
        environment=environment,
        expected_output=__version__,
    )
    with rehearsal_root(work_directory) as root:
        backup_recovery = _rehearse_backup_migration_recovery(
            executable,
            root,
            environment,
        )
        terminal_lineage = _rehearse_abandonment_successor(
            executable,
            root,
            environment,
        )
    return {
        "schema_version": 1,
        "status": "passed",
        "procedures": {
            **backup_recovery,
            **terminal_lineage,
        },
        "limitations": [
            "Fixtures are synthetic and temporary; no project outcome is accepted.",
            "Successful archive closure is exercised separately by both example workflows.",
            "Host filesystem behavior is evidence only for the exact observed environment.",
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rehearse maintained FORGE release recovery and lineage procedures."
    )
    parser.add_argument(
        "--forge",
        type=Path,
        default=Path(shutil.which("forge") or "forge"),
        help="Exact installed FORGE console executable to exercise.",
    )
    parser.add_argument(
        "--work-directory",
        type=Path,
        help="Fresh nonexistent directory to retain; defaults to temporary.",
    )
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        report = run_rehearsal(
            forge_executable=arguments.forge,
            work_directory=arguments.work_directory,
        )
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if arguments.output is None:
            sys.stdout.write(rendered)
        else:
            output = arguments.output.resolve()
            if output.exists():
                _fail(f"Refusing to overwrite procedure report: {output}")
            output.write_text(rendered, encoding="utf-8")
    except (OSError, ProcedureRehearsalError, subprocess.TimeoutExpired) as error:
        print(f"release procedure rehearsal failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
