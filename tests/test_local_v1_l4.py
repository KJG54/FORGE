from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout

runner = CliRunner()


def _active_repository(path: Path) -> RepositoryLayout:
    initialized = runner.invoke(app, ["init", str(path), "--owner-name", "Owner"])
    assert initialized.exit_code == 0, initialized.output
    created = runner.invoke(
        app,
        [
            "create",
            "L4 recap objective",
            "--scope",
            "Bounded scratchpad and recap scope",
            "--trust-pack-data",
            "--idempotency-key",
            "create-l4",
            "-C",
            str(path),
        ],
    )
    assert created.exit_code == 0, created.output
    return RepositoryLayout.at(path)


def _scratchpad(initiative_id: UUID, sequence: int, notes: str) -> str:
    return (
        "<!-- FORGE SCRATCHPAD v1\n"
        f"initiative_id: {initiative_id}\n"
        f"journal_sequence: {sequence}\n"
        "-->\n"
        f"{notes}\n"
    )


def _recap(path: Path):  # type: ignore[no-untyped-def]
    return runner.invoke(app, ["recap", "-C", str(path)])


def test_recap_separates_validated_position_from_missing_and_empty_notes(
    tmp_path: Path,
) -> None:
    layout = _active_repository(tmp_path)
    journal_before = layout.event_journal_file.read_bytes()
    state_before = layout.state_file.read_bytes()

    missing = _recap(tmp_path)

    assert missing.exit_code == 0, missing.output
    assert "Authoritative governed position (validated)" in missing.stdout
    assert f"Project label: {tmp_path.name}" in missing.stdout
    assert "source: repository directory; friendly and non-canonical" in missing.stdout
    assert "Last governed event time:" in missing.stdout
    assert "Journal head sequence: 1" in missing.stdout
    assert "Legal next actions:" in missing.stdout
    assert "Local scratchpad (mutable, ungoverned, advisory" in missing.stdout
    assert "Scratchpad update time: none" in missing.stdout
    assert "Reconciliation: missing" in missing.stdout

    layout.conversation_directory.mkdir()
    layout.scratchpad_file.write_bytes(b"")
    empty = _recap(tmp_path)

    assert empty.exit_code == 0, empty.output
    assert "Scratchpad update time: none" not in empty.stdout
    assert "Reconciliation: empty" in empty.stdout
    assert "Local notes: none" in empty.stdout
    assert layout.event_journal_file.read_bytes() == journal_before
    assert layout.state_file.read_bytes() == state_before


def test_recap_reconciles_current_stale_ahead_and_cross_initiative_notes(
    tmp_path: Path,
) -> None:
    layout = _active_repository(tmp_path)
    event = read_journal(layout.event_journal_file)[-1]
    layout.conversation_directory.mkdir()

    layout.scratchpad_file.write_text(
        _scratchpad(event.initiative_id, event.sequence, "Current hypothesis: use one reader."),
        encoding="utf-8",
    )
    current = _recap(tmp_path)
    assert current.exit_code == 0, current.output
    assert "Reconciliation: current" in current.stdout
    assert "Local notes (mutable and ungoverned" in current.stdout
    assert "Current hypothesis: use one reader." in current.stdout

    layout.scratchpad_file.write_text(
        _scratchpad(event.initiative_id, event.sequence - 1, "Question: is this still open?"),
        encoding="utf-8",
    )
    stale = _recap(tmp_path)
    assert stale.exit_code == 0, stale.output
    assert "Reconciliation: stale" in stale.stdout
    assert f"validated head is {event.sequence}" in stale.stdout

    layout.scratchpad_file.write_text(
        _scratchpad(event.initiative_id, event.sequence + 1, "Unconfirmed future note."),
        encoding="utf-8",
    )
    ahead = _recap(tmp_path)
    assert ahead.exit_code == 0, ahead.output
    assert "Reconciliation: ahead-of-journal" in ahead.stdout

    other_id = uuid4()
    layout.scratchpad_file.write_text(
        _scratchpad(other_id, event.sequence, "Old initiative question."),
        encoding="utf-8",
    )
    crossed = _recap(tmp_path)
    assert crossed.exit_code == 0, crossed.output
    assert "Reconciliation: initiative-mismatch" in crossed.stdout
    assert f"local notes name initiative {other_id}" in crossed.stdout
    assert "Old initiative question." in crossed.stdout


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"plain notes without metadata\n", "Malformed local scratchpad header"),
        (b"\xff\xfe", "must be valid UTF-8 Markdown"),
        (
            b"<!-- FORGE SCRATCHPAD v1\ninitiative_id: no\njournal_sequence: 1\n-->\n",
            "expected a UUID",
        ),
        (
            b"<!-- FORGE SCRATCHPAD v1\n"
            b"initiative_id: 00000000-0000-0000-0000-000000000000\n"
            b"journal_sequence: 01\n-->\nnotes\n",
            "canonical non-negative integer",
        ),
        (
            b"<!-- FORGE SCRATCHPAD v1\n"
            b"initiative_id: 00000000-0000-0000-0000-000000000000\n"
            b"journal_sequence: 1\n-->\nunsafe\x1b[31m\n",
            "unsafe control characters",
        ),
        (b"\x0b", "unsafe control characters"),
    ],
)
def test_recap_refuses_malformed_scratchpads(
    tmp_path: Path,
    content: bytes,
    message: str,
) -> None:
    layout = _active_repository(tmp_path)
    layout.conversation_directory.mkdir()
    layout.scratchpad_file.write_bytes(content)

    result = _recap(tmp_path)

    assert result.exit_code == 31
    assert message in result.stderr


def test_recap_refuses_oversized_symbolic_and_irregular_scratchpads(
    tmp_path: Path,
) -> None:
    oversized_root = tmp_path / "oversized"
    oversized_root.mkdir()
    oversized = _active_repository(oversized_root)
    oversized.conversation_directory.mkdir()
    oversized.scratchpad_file.write_bytes(b"x" * 65_537)
    too_large = _recap(oversized_root)
    assert too_large.exit_code == 31
    assert "exceeds the 65536-byte limit" in too_large.stderr

    irregular_root = tmp_path / "irregular"
    irregular_root.mkdir()
    irregular = _active_repository(irregular_root)
    irregular.conversation_directory.mkdir()
    irregular.scratchpad_file.mkdir()
    irregular_result = _recap(irregular_root)
    assert irregular_result.exit_code == 31
    assert "not a regular file" in irregular_result.stderr

    symbolic_root = tmp_path / "symbolic"
    symbolic_root.mkdir()
    symbolic = _active_repository(symbolic_root)
    symbolic.conversation_directory.mkdir()
    target = tmp_path / "outside-scratchpad.md"
    target.write_text("outside notes\n", encoding="utf-8")
    try:
        symbolic.scratchpad_file.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")
    symbolic_result = _recap(symbolic_root)
    assert symbolic_result.exit_code == 40
    assert "Refusing to read a symbolic local scratchpad" in symbolic_result.stderr


def test_recap_preserves_formal_pause_and_resume_behavior(tmp_path: Path) -> None:
    layout = _active_repository(tmp_path)
    paused = runner.invoke(
        app,
        [
            "pause",
            "--reason",
            "Owner requested a governed long-gap boundary",
            "--idempotency-key",
            "pause-l4",
            "-C",
            str(tmp_path),
        ],
    )
    assert paused.exit_code == 0, paused.output
    journal_before = layout.event_journal_file.read_bytes()

    recap = _recap(tmp_path)

    assert recap.exit_code == 0, recap.output
    assert "Lifecycle: paused" in recap.stdout
    assert "- resume" in recap.stdout
    assert "forge pause/resume remains the owner-authorized" in recap.stdout
    assert layout.event_journal_file.read_bytes() == journal_before

    resumed = runner.invoke(
        app,
        [
            "resume",
            "--idempotency-key",
            "resume-l4",
            "-C",
            str(tmp_path),
        ],
    )
    assert resumed.exit_code == 0, resumed.output
