from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID

from typer.testing import CliRunner

from forge.cli.app import app
from forge.core.transaction_receipts import (
    build_refusal_receipt,
    render_transaction_receipt,
)
from forge.errors import ConfigurationError
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout

runner = CliRunner()


def _initialize(path: Path) -> RepositoryLayout:
    initialized = runner.invoke(app, ["init", str(path), "--owner-name", "Owner"])
    assert initialized.exit_code == 0, initialized.output
    return RepositoryLayout.at(path)


def _invoke(path: Path, *arguments: str):  # type: ignore[no-untyped-def]
    return runner.invoke(app, [*arguments, "-C", str(path)])


def _field(output: str, name: str) -> str:
    match = re.search(rf"(?:^|[;( ]){re.escape(name)}=([^;,)\] ]+)", output)
    assert match is not None, output
    return match.group(1)


def _assert_two_line_receipt(output: str) -> None:
    lines = output.strip().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("Recorded -> ")
    assert lines[1].startswith("Means    -> ")


def test_new_commit_and_replay_use_one_canonical_receipt(tmp_path: Path) -> None:
    layout = _initialize(tmp_path)
    created = _invoke(
        tmp_path,
        "create",
        "Objective",
        "--scope",
        "Bounded scope",
        "--trust-pack-data",
        "--idempotency-key",
        "create-l3",
    )

    assert created.exit_code == 0, created.output
    _assert_two_line_receipt(created.stdout)
    events = read_journal(layout.event_journal_file)
    assert len(events) == 1
    assert f"[sequence 1-1; events {events[0].id}]" in created.stdout
    assert "transaction=create:create-l3" in created.stdout
    assert "legal_actions=begin:discover" in created.stdout

    original_journal = layout.event_journal_file.read_bytes()
    replayed = _invoke(
        tmp_path,
        "create",
        "Objective",
        "--scope",
        "Bounded scope",
        "--trust-pack-data",
        "--idempotency-key",
        "create-l3",
    )

    assert replayed.exit_code == 0, replayed.output
    _assert_two_line_receipt(replayed.stdout)
    assert "Idempotent replay of create transaction create-l3" in replayed.stdout
    assert "zero new events" in replayed.stdout
    assert f"[sequence 1-1; events {events[0].id}]" in replayed.stdout
    assert layout.event_journal_file.read_bytes() == original_journal


def test_refusal_has_no_recorded_claim_and_proves_unchanged_only_when_safe(
    tmp_path: Path,
) -> None:
    layout = _initialize(tmp_path)
    refused = _invoke(
        tmp_path,
        "create",
        "Objective",
        "--scope",
        "Bounded scope",
        "--idempotency-key",
        "refused-l3",
    )

    assert refused.exit_code == 20
    assert "Recorded ->" not in refused.output
    assert refused.output.count("Means    ->") == 1
    assert "Refused create" in refused.output
    assert "validated no new governed events" in refused.output
    assert not layout.event_journal_file.exists()

    uncertain = build_refusal_receipt(
        layout,
        command="create",
        error=ConfigurationError("synthetic\nuncertainty"),
        position_before=None,
    )
    rendered = render_transaction_receipt(uncertain)
    assert rendered.startswith("Means    -> Refused create")
    assert len(rendered.splitlines()) == 1
    assert "synthetic uncertainty" in rendered
    assert "governed commit state is not asserted" in rendered
    assert "validated no new governed events" not in rendered


def test_multi_event_commit_reports_exact_range_and_resulting_state(
    tmp_path: Path,
) -> None:
    layout = _initialize(tmp_path)
    assert _invoke(
        tmp_path,
        "create",
        "Objective",
        "--scope",
        "Bounded scope",
        "--trust-pack-data",
        "--idempotency-key",
        "create-multi",
    ).exit_code == 0
    begun = _invoke(
        tmp_path,
        "begin",
        "discover",
        "--idempotency-key",
        "begin-multi",
    )
    assert begun.exit_code == 0, begun.output
    UUID(_field(begun.stdout, "run_id"))
    for filename, role in (
        ("objective.md", "objective-and-constraints"),
        ("requirements.md", "requirements"),
    ):
        (tmp_path / filename).write_text(role, encoding="utf-8")
        added = _invoke(
            tmp_path,
            "artifact",
            "add",
            filename,
            "--role",
            role,
            "--title",
            role,
        )
        assert added.exit_code == 0, added.output
        UUID(_field(added.stdout, "revision_id"))

    completed = _invoke(
        tmp_path,
        "complete",
        "discover",
        "--assertion",
        "Discovery outputs are ready",
        "--idempotency-key",
        "complete-multi",
    )

    assert completed.exit_code == 0, completed.output
    _assert_two_line_receipt(completed.stdout)
    matching = [
        event
        for event in read_journal(layout.event_journal_file)
        if event.metadata.get("idempotency", {}).get("key") == "complete-multi"
    ]
    assert len(matching) == 2
    assert f"sequence {matching[0].sequence}-{matching[1].sequence}" in completed.stdout
    assert f"events {matching[0].id},{matching[1].id}" in completed.stdout
    assert "claim-recorded" in completed.stdout
    assert "step-transitioned" in completed.stdout
    assert "step=discover:awaiting_verification" in completed.stdout
    assert "legal_actions=verify:discover" in completed.stdout


def test_failed_check_is_a_commit_and_detailed_inspection_remains_available(
    tmp_path: Path,
) -> None:
    layout = _initialize(tmp_path)
    assert _invoke(
        tmp_path,
        "create",
        "Objective",
        "--scope",
        "Bounded scope",
        "--trust-pack-data",
    ).exit_code == 0
    assert _invoke(tmp_path, "begin", "discover").exit_code == 0
    for filename, role in (
        ("objective.md", "objective-and-constraints"),
        ("requirements.md", "requirements"),
    ):
        (tmp_path / filename).write_text(role, encoding="utf-8")
        assert _invoke(
            tmp_path,
            "artifact",
            "add",
            filename,
            "--role",
            role,
            "--title",
            role,
        ).exit_code == 0
    assert _invoke(
        tmp_path,
        "complete",
        "discover",
        "--assertion",
        "Outputs produced",
    ).exit_code == 0

    checked = _invoke(
        tmp_path,
        "check",
        "record",
        "discover",
        "outputs-present",
        "--invocation",
        "manual review",
        "--outcome",
        "failed",
        "--exit-status",
        "1",
    )

    assert checked.exit_code == 0, checked.output
    _assert_two_line_receipt(checked.stdout)
    assert "check-recorded" in checked.stdout
    assert "outcome=failed" in checked.stdout
    check_result_id = UUID(_field(checked.stdout, "check_result_id"))

    history = _invoke(tmp_path, "history")
    assert history.exit_code == 0, history.output
    assert "check-recorded" in history.stdout
    shown = _invoke(tmp_path, "check", "show", str(check_result_id))
    assert shown.exit_code == 0, shown.output
    assert "Outcome: failed" in shown.stdout
    assert read_journal(layout.event_journal_file)[-1].id == UUID(
        re.search(r"events ([0-9a-f-]{36})\]", checked.stdout).group(1)  # type: ignore[union-attr]
    )
