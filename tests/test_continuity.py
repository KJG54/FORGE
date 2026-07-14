from __future__ import annotations

from pathlib import Path
from typing import Protocol, cast
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.state import InitiativeLifecycleState
from forge.core.continuity import pause_initiative
from forge.errors import AuthorizationError
from forge.storage.configuration import load_configuration
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import load_snapshot

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
            "Continuity objective",
            "--scope",
            "Pause and resume test scope",
            "--trust-pack-data",
            "--idempotency-key",
            "create-continuity-test",
            "-C",
            str(path),
        ],
    )
    assert created.exit_code == 0, created.output
    return RepositoryLayout.at(path)


def _pause(path: Path, *, key: str = "pause-once") -> InvocationResult:
    return cast(
        InvocationResult,
        runner.invoke(
            app,
            [
                "pause",
                "--reason",
                "Waiting for owner review",
                "--idempotency-key",
                key,
                "-C",
                str(path),
            ],
        ),
    )


def test_pause_and_resume_survive_restart_with_durable_summary(tmp_path: Path) -> None:
    layout = _repository(tmp_path)
    before = load_snapshot(layout.state_file)

    paused = _pause(tmp_path)

    assert paused.exit_code == 0, paused.output
    paused_state = load_snapshot(layout.state_file)
    assert paused_state.lifecycle_state is InitiativeLifecycleState.PAUSED
    assert paused_state.active_pause_event_id is not None
    assert paused_state.current_step_id == before.current_step_id
    assert paused_state.step_states == before.step_states
    assert paused_state.permitted_next_actions == ("resume",)
    status = runner.invoke(app, ["status", "-C", str(tmp_path)])
    assert status.exit_code == 0, status.output
    assert "Lifecycle: paused" in status.stdout
    assert "Next: resume" in status.stdout
    assert "Blocker: Initiative paused: Waiting for owner review" in status.stdout
    history = runner.invoke(app, ["history", "-C", str(tmp_path)])
    assert history.exit_code == 0, history.output
    assert "initiative-paused" in history.stdout

    resumed = runner.invoke(
        app,
        [
            "resume",
            "--idempotency-key",
            "resume-once",
            "-C",
            str(tmp_path),
        ],
    )

    assert resumed.exit_code == 0, resumed.output
    assert "Summary: Resuming objective: Continuity objective." in resumed.stdout
    assert "Pause reason: Waiting for owner review." in resumed.stdout
    resumed_state = load_snapshot(layout.state_file)
    assert resumed_state.lifecycle_state is InitiativeLifecycleState.ACTIVE
    assert resumed_state.active_pause_event_id is None
    assert resumed_state.current_step_id == before.current_step_id
    assert resumed_state.step_states == before.step_states
    assert resumed_state.permitted_next_actions == before.permitted_next_actions
    assert [event.event_type for event in read_journal(layout.event_journal_file)][-2:] == [
        "initiative-paused",
        "initiative-resumed",
    ]


def test_paused_initiative_rejects_normal_mutation_but_allows_idempotent_replay(
    tmp_path: Path,
) -> None:
    layout = _repository(tmp_path)
    paused = _pause(tmp_path)
    assert paused.exit_code == 0, paused.output
    journal = layout.event_journal_file.read_bytes()
    source = tmp_path / "objective.md"
    source.write_text("paused mutation", encoding="utf-8")

    blocked = runner.invoke(
        app,
        [
            "artifact",
            "add",
            source.name,
            "--role",
            "objective-and-constraints",
            "--title",
            "Blocked while paused",
            "--idempotency-key",
            "blocked-paused-add",
            "-C",
            str(tmp_path),
        ],
    )

    assert blocked.exit_code == 31
    assert "Initiative is paused" in blocked.stderr
    assert layout.event_journal_file.read_bytes() == journal
    replay = _pause(tmp_path)
    assert replay.exit_code == 0, replay.output
    assert "Idempotent replay" in replay.stdout
    assert layout.event_journal_file.read_bytes() == journal


def test_pause_refuses_active_governed_runs(tmp_path: Path) -> None:
    layout = _repository(tmp_path)
    for filename, role, key in (
        ("objective.md", "objective-and-constraints", "continuity-objective"),
        ("requirements.md", "requirements", "continuity-requirements"),
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
    begun = runner.invoke(
        app,
        [
            "begin",
            "discover",
            "--idempotency-key",
            "continuity-begin",
            "-C",
            str(tmp_path),
        ],
    )
    assert begun.exit_code == 0, begun.output
    original_journal = layout.event_journal_file.read_bytes()

    paused = _pause(tmp_path, key="unsafe-pause")

    assert paused.exit_code == 31
    assert "Pause requires no active governed runs" in paused.stderr
    assert layout.event_journal_file.read_bytes() == original_journal


def test_pause_requires_configured_owner(tmp_path: Path) -> None:
    layout = _repository(tmp_path)
    configuration = load_configuration(layout.configuration_file)
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )

    with pytest.raises(AuthorizationError, match="Only configured owner"):
        pause_initiative(layout, actor=outsider, reason="Unauthorized")

    assert len(read_journal(layout.event_journal_file)) == 1
    assert configuration.owner.id != outsider.id
