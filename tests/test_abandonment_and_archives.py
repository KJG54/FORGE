from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

import forge.core.archival as archival
from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.state import InitiativeLifecycleState
from forge.core.archival import abandon_initiative, load_archive
from forge.core.artifacts import add_artifact
from forge.core.authorization import owner_actor
from forge.core.continuity import pause_initiative
from forge.core.history import inspect_history
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.runs import cancel_run
from forge.core.status import inspect_status
from forge.errors import AuthorizationError, ConfigurationError, ConflictError, IntegrityError
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _new_initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Explore a governed initiative that may remain unfinished",
        declared_scope_summary="Exercise atomic abandonment",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _abandon(
    initialized: InitializationResult,
    actor: Actor,
) -> archival.AbandonmentResult:
    return abandon_initiative(
        initialized.layout,
        reason="Owner determined the initiative should stop",
        unfinished_work_summary="The remaining workflow steps were not completed",
        unresolved_risks=("The intended outcome was not delivered",),
        actor=actor,
    )


def test_abandon_requires_owner_and_explicit_decision_fields(tmp_path: Path) -> None:
    initialized, actor = _new_initiative(tmp_path)
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        _abandon(initialized, outsider)
    with pytest.raises(ConfigurationError, match="At least one unresolved risk"):
        abandon_initiative(
            initialized.layout,
            reason="Owner decision",
            unfinished_work_summary="Unfinished work",
            unresolved_risks=(),
            actor=actor,
        )


def test_abandon_preserves_registered_bytes_without_claiming_acceptance(
    tmp_path: Path,
) -> None:
    initialized, actor = _new_initiative(tmp_path)
    artifact_path = tmp_path / "outputs" / "partial.md"
    artifact_path.parent.mkdir()
    artifact_path.write_bytes(b"registered partial bytes\n")
    added = add_artifact(
        initialized.layout,
        path="outputs/partial.md",
        role="project-artifacts",
        title="Partial governed output",
        actor=actor,
        media_type="text/markdown",
    )
    artifact_path.write_bytes(b"later unregistered working bytes\n")

    result = _abandon(initialized, actor)
    initiative_id = result.abandonment.initiative_id
    assert result.event.event_type == "initiative-abandoned"
    assert result.abandonment.terminal_state is InitiativeLifecycleState.ABANDONED
    assert result.archive.closure is None
    assert result.archive.abandonment == result.abandonment
    assert result.archive.manifest.closure_record_id is None
    assert result.archive.manifest.abandonment_record_id == result.abandonment.id
    assert not result.archive.manifest.preliminary
    assert all(not reference.accepted for reference in result.archive.manifest.object_references)
    reference = result.archive.manifest.object_references[0]
    assert reference.artifact_revision_id == added.revision.id
    assert (initialized.layout.root / reference.preserved_object_path).read_bytes() == (
        b"registered partial bytes\n"
    )
    restarted = load_archive(initialized.layout, initiative_id)
    assert restarted.active.state.lifecycle_state is InitiativeLifecycleState.ABANDONED
    assert restarted.events[-1].id == result.event.id
    assert not tuple(initialized.layout.active_directory.iterdir())


def test_abandon_blocks_active_runs_then_allows_cancelled_and_paused_work(
    tmp_path: Path,
) -> None:
    initialized, actor = _new_initiative(tmp_path)
    step_id = load_active_initiative(initialized.layout).workflow.steps[0].id
    run = begin_manual_run(initialized.layout, step_id=step_id, actor=actor)
    with pytest.raises(ConflictError, match="cancel active runs first"):
        _abandon(initialized, actor)
    cancel_run(
        initialized.layout,
        run_id=run.run.id,
        reason="Prepare explicit owner abandonment",
        actor=actor,
    )
    pause_initiative(
        initialized.layout,
        actor=actor,
        reason="Pause before making the terminal owner decision",
    )
    result = _abandon(initialized, actor)
    assert result.archive.active.state.lifecycle_state is InitiativeLifecycleState.ABANDONED


def test_abandon_status_history_cli_and_terminal_immutability(tmp_path: Path) -> None:
    initialized, actor = _new_initiative(tmp_path)
    initiative_id = load_active_initiative(initialized.layout).initiative.id
    arguments = [
        "abandon",
        "--reason",
        "CLI owner stop decision",
        "--unfinished-work",
        "Implementation and review remain unfinished",
        "--risk",
        "No usable deliverable was accepted",
        "-C",
        str(initialized.layout.root),
    ]
    abandoned = runner.invoke(app, arguments)
    assert abandoned.exit_code == 0, abandoned.stderr
    assert "Atomic M2 abandonment archive created" in abandoned.stdout
    status = runner.invoke(
        app,
        ["status", "--archive", str(initiative_id), "-C", str(initialized.layout.root)],
    )
    assert status.exit_code == 0, status.stderr
    assert "Lifecycle: abandoned" in status.stdout
    assert "Abandonment reason: CLI owner stop decision" in status.stdout
    assert "Archive guarantee: atomic M2 abandoned" in status.stdout
    history = inspect_history(initialized.layout, archive_id=initiative_id)
    assert history[-1].event_type == "initiative-abandoned"
    assert inspect_status(initialized.layout).next_actions == ("create-successor",)
    successor = create_initiative(
        initialized.layout,
        objective="Continue after an abandoned attempt",
        declared_scope_summary="Fresh work linked to the abandoned predecessor",
        actor=actor,
        trust_pack_data=True,
        predecessor_ids=(initiative_id,),
    )
    assert successor.active.initiative.id != initiative_id


def test_abandoned_archive_tampering_is_detected(tmp_path: Path) -> None:
    initialized, actor = _new_initiative(tmp_path)
    result = _abandon(initialized, actor)
    record_path = result.archive.layout.abandonment_directory / (
        f"{result.abandonment.id}.json"
    )
    record_path.write_bytes(record_path.read_bytes() + b" ")
    with pytest.raises(IntegrityError, match="inventory"):
        load_archive(initialized.layout, result.abandonment.initiative_id)


def test_cli_abandon_retry_rebuilds_staging_and_finishes_retirement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, _ = _new_initiative(tmp_path)
    initiative_id = load_active_initiative(initialized.layout).initiative.id
    original_copy = archival._copy_active_tree  # pyright: ignore[reportPrivateUsage]

    def interrupt_after_copy(source: Path, destination: Path) -> None:
        original_copy(source, destination)
        raise OSError("simulated abandonment promotion interruption")

    monkeypatch.setattr(archival, "_copy_active_tree", interrupt_after_copy)
    arguments = [
        "abandon",
        "--reason",
        "Interruption fixture",
        "--unfinished-work",
        "All planned work remains unfinished",
        "--risk",
        "No final outcome exists",
        "--idempotency-key",
        "abandon-promotion-retry",
        "-C",
        str(initialized.layout.root),
    ]
    interrupted = runner.invoke(app, arguments)
    assert interrupted.exit_code != 0
    assert "same idempotency key" in interrupted.stderr
    assert len(tuple(initialized.layout.archive_directory.glob(".*.staging"))) == 1

    monkeypatch.undo()
    original_rmtree = archival.shutil.rmtree
    failed = False

    def interrupt_retirement(path: Path) -> None:
        nonlocal failed
        if path.name == f"abandoned-active-{initiative_id}" and not failed:
            failed = True
            raise OSError("simulated abandonment retirement interruption")
        original_rmtree(path)

    monkeypatch.setattr(archival.shutil, "rmtree", interrupt_retirement)
    retired_interruption = runner.invoke(app, arguments)
    assert retired_interruption.exit_code != 0
    assert "same idempotency key" in retired_interruption.stderr
    assert load_archive(initialized.layout, initiative_id).abandonment is not None

    monkeypatch.undo()
    resumed = runner.invoke(app, arguments)
    assert resumed.exit_code == 0, resumed.stderr
    replay = runner.invoke(app, arguments)
    assert replay.exit_code == 0
    assert "Idempotent replay" in replay.stdout
