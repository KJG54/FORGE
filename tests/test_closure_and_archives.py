from pathlib import Path
from uuid import UUID, uuid4

import pytest
from typer.testing import CliRunner

import forge.core.archival as archival
from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.state import InitiativeLifecycleState
from forge.contracts.verification import CheckOutcome
from forge.core.acceptance import record_acceptance
from forge.core.archival import close_initiative, list_archive_ids, load_archive
from forge.core.artifacts import add_artifact, current_revisions_for_roles
from forge.core.authorization import owner_actor
from forge.core.history import inspect_history
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.status import inspect_status
from forge.core.verification import (
    complete_step,
    record_check,
    record_evidence,
    verify_step,
)
from forge.errors import AuthorizationError, ConflictError, IntegrityError
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _new_initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Complete and preserve a governed initiative",
        declared_scope_summary="Exercise resumable atomic closure",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _completed_initiative(tmp_path: Path) -> tuple[InitializationResult, Actor, UUID]:
    initialized, actor = _new_initiative(tmp_path)
    active = None
    for step in load_active_initiative(initialized.layout).workflow.steps:
        begin_manual_run(initialized.layout, step_id=step.id, actor=actor)
        revision_ids: list[UUID] = []
        for role in step.required_outputs:
            path = f"outputs/{role}.md"
            target = tmp_path / path
            target.parent.mkdir(exist_ok=True)
            target.write_text(f"# {role}\nGoverned output for {step.id}.\n", encoding="utf-8")
            result = add_artifact(
                initialized.layout,
                path=path,
                role=role,
                title=f"{role} output",
                actor=actor,
                media_type="text/markdown",
            )
            revision_ids.append(result.revision.id)
        claim = complete_step(
            initialized.layout,
            step_id=step.id,
            assertion=f"Produced declared outputs for {step.id}",
            actor=actor,
        )
        check = record_check(
            initialized.layout,
            step_id=step.id,
            check_id=step.check_requirements[0],
            check_version="1",
            invocation_metadata={"invocation": "manual governed review"},
            outcome=CheckOutcome.PASSED,
            actor=actor,
            exit_status=0,
        )
        record_evidence(
            initialized.layout,
            step_id=step.id,
            purpose=f"Bind current outputs and check for {step.id}",
            actor=actor,
            artifact_revision_ids=tuple(revision_ids),
            check_result_ids=(check.check.id,),
            claim_ids=(claim.claim.id,),
        )
        verify_step(initialized.layout, step_id=step.id)
        record_acceptance(
            initialized.layout,
            step_id=step.id,
            accepted_scope=f"Current {step.id} outputs",
            actor=actor,
        )
        active = load_active_initiative(initialized.layout)
        assert {
            item.id for item in current_revisions_for_roles(active, step.required_outputs)
        } == set(revision_ids)
    assert active is not None
    return initialized, actor, active.initiative.id


def test_close_requires_owner_and_complete_workflow(tmp_path: Path) -> None:
    initialized, actor = _new_initiative(tmp_path)
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        close_initiative(
            initialized.layout,
            closing_summary="Not authorized",
            actor=outsider,
        )
    with pytest.raises(ConflictError, match="every workflow step"):
        close_initiative(
            initialized.layout,
            closing_summary="Incomplete",
            actor=actor,
        )
    assert not tuple(initialized.layout.archive_directory.iterdir())


def test_close_preserves_exact_bytes_and_supports_read_only_restart(
    tmp_path: Path,
) -> None:
    initialized, actor, initiative_id = _completed_initiative(tmp_path)
    before = {
        revision.id: (initialized.layout.root / revision.preserved_object_path).read_bytes()
        for step in load_active_initiative(initialized.layout).workflow.steps
        for revision in current_revisions_for_roles(
            load_active_initiative(initialized.layout),
            step.required_outputs,
        )
        if revision.preserved_object_path is not None
    }
    result = close_initiative(
        initialized.layout,
        closing_summary="All governed steps are accepted and ready for closure",
        actor=actor,
    )

    assert result.event.event_type == "initiative-closed"
    assert result.closure.terminal_state is InitiativeLifecycleState.CLOSED
    assert not result.archive.manifest.preliminary
    assert result.archive.manifest.limitations == ()
    assert result.archive.manifest.archive_digest.startswith("sha256:")
    assert set(list_archive_ids(initialized.layout)) == {initiative_id}
    assert not tuple(initialized.layout.active_directory.iterdir())
    restarted = load_archive(initialized.layout, initiative_id)
    assert restarted.active.state.lifecycle_state is InitiativeLifecycleState.CLOSED
    assert restarted.events[-1].id == result.event.id
    assert all(reference.accepted for reference in restarted.manifest.object_references)
    for reference in restarted.manifest.object_references:
        assert (
            initialized.layout.root / reference.preserved_object_path
        ).read_bytes() == before[reference.artifact_revision_id]

    (tmp_path / "outputs" / "project-artifacts.md").write_text(
        "Changed after closure", encoding="utf-8"
    )
    assert load_archive(initialized.layout, initiative_id).manifest == restarted.manifest
    default_status = inspect_status(initialized.layout)
    assert default_status.initiative is None
    assert default_status.archived_initiative_ids == (initiative_id,)
    assert default_status.next_actions == ("create-successor",)
    archived_status = inspect_status(initialized.layout, archive_id=initiative_id)
    assert archived_status.integrity_state.value == "healthy"
    assert archived_status.selected_archive_id == initiative_id
    history = inspect_history(initialized.layout, archive_id=initiative_id)
    assert history[-1].event_type == "initiative-closed"
    assert inspect_history(
        initialized.layout,
        archive_id=initiative_id,
        event_type="initiative-closed",
    ) == (history[-1],)
    successor = create_initiative(
        initialized.layout,
        objective="Continue from accepted archived work",
        declared_scope_summary="Fresh governed work with explicit predecessor provenance",
        actor=actor,
        trust_pack_data=True,
        predecessor_ids=(initiative_id,),
    )
    assert successor.active.initiative.id != initiative_id
    assert successor.active.initiative.predecessor_references[0].initiative_id == initiative_id


def test_close_rejects_changed_working_bytes(tmp_path: Path) -> None:
    initialized, actor, _ = _completed_initiative(tmp_path)
    (tmp_path / "outputs" / "lessons.md").write_text("Changed", encoding="utf-8")
    with pytest.raises(ConflictError, match="exact current working bytes"):
        close_initiative(
            initialized.layout,
            closing_summary="Must not close stale bytes",
            actor=actor,
        )


def test_archive_manifest_and_preserved_object_tampering_are_detected(
    tmp_path: Path,
) -> None:
    initialized, actor, initiative_id = _completed_initiative(tmp_path)
    closed = close_initiative(
        initialized.layout,
        closing_summary="Tamper detection fixture",
        actor=actor,
    )
    archive_file = closed.archive.layout.initiative_file
    original_archive = archive_file.read_bytes()
    archive_file.write_bytes(original_archive + b" ")
    with pytest.raises(IntegrityError, match="inventory"):
        load_archive(initialized.layout, initiative_id)
    archive_file.write_bytes(original_archive)

    reference = closed.archive.manifest.object_references[0]
    object_path = initialized.layout.root / reference.preserved_object_path
    original_object = object_path.read_bytes()
    object_path.write_bytes(b"tampered")
    with pytest.raises(IntegrityError, match="Preserved object"):
        load_archive(initialized.layout, initiative_id)
    object_path.write_bytes(original_object)
    assert load_archive(initialized.layout, initiative_id).manifest == closed.archive.manifest


def test_close_status_and_history_cli(tmp_path: Path) -> None:
    initialized, _, initiative_id = _completed_initiative(tmp_path)
    closed = runner.invoke(
        app,
        [
            "close",
            "--summary",
            "CLI owner closure",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert closed.exit_code == 0, closed.stdout
    assert "Atomic M2 archive created" in closed.stdout
    status = runner.invoke(
        app,
        ["status", "--archive", str(initiative_id), "-C", str(initialized.layout.root)],
    )
    assert status.exit_code == 0, status.stdout
    assert "Lifecycle: closed" in status.stdout
    assert "Archive guarantee: atomic M2" in status.stdout
    history = runner.invoke(
        app,
        [
            "history",
            "--archive",
            str(initiative_id),
            "--event-type",
            "initiative-closed",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert history.exit_code == 0, history.stdout
    assert "initiative-closed" in history.stdout


def test_interrupted_archive_promotion_is_detected_and_resumed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, actor, _ = _completed_initiative(tmp_path)

    def fail_copy(_source: object, _destination: object) -> None:
        raise OSError("simulated archive interruption")

    monkeypatch.setattr(archival, "_copy_active_tree", fail_copy)
    with pytest.raises(IntegrityError, match="Atomic archive promotion was interrupted"):
        close_initiative(
            initialized.layout,
            closing_summary="Interruption fixture",
            actor=actor,
        )
    report = inspect_status(initialized.layout)
    assert report.integrity_state.value == "integrity_error"
    assert any("retry 'forge close'" in blocker for blocker in report.blockers)
    with pytest.raises(IntegrityError, match="supported mutations are disabled"):
        begin_manual_run(initialized.layout, step_id="close", actor=actor)
    monkeypatch.undo()
    resumed = close_initiative(
        initialized.layout,
        closing_summary="Interruption fixture",
        actor=actor,
    )
    assert not resumed.archive.manifest.preliminary
    assert not tuple(initialized.layout.active_directory.iterdir())


def test_cli_close_retry_completes_interrupted_active_retirement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, _, initiative_id = _completed_initiative(tmp_path)
    original_rmtree = archival.shutil.rmtree
    failed = False

    def fail_retired_cleanup(path: Path) -> None:
        nonlocal failed
        if path.name == f"closed-active-{initiative_id}" and not failed:
            failed = True
            raise OSError("simulated retirement interruption")
        original_rmtree(path)

    monkeypatch.setattr(archival.shutil, "rmtree", fail_retired_cleanup)
    arguments = [
        "close",
        "--summary",
        "Retirement recovery fixture",
        "--idempotency-key",
        "close-retirement-retry",
        "-C",
        str(initialized.layout.root),
    ]
    interrupted = runner.invoke(app, arguments)
    assert interrupted.exit_code != 0
    assert "same idempotency key" in interrupted.stderr
    assert load_archive(initialized.layout, initiative_id).manifest.preliminary is False
    report = inspect_status(initialized.layout)
    assert report.integrity_state.value == "integrity_error"

    monkeypatch.undo()
    resumed = runner.invoke(app, arguments)
    assert resumed.exit_code == 0, resumed.stderr
    assert "Atomic M2 archive created" in resumed.stdout
    assert not tuple(initialized.layout.active_directory.iterdir())
    replay = runner.invoke(app, arguments)
    assert replay.exit_code == 0
    assert "Idempotent replay" in replay.stdout


def test_cli_close_retry_rebuilds_interrupted_archive_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, _, initiative_id = _completed_initiative(tmp_path)
    original_copy = archival._copy_active_tree  # pyright: ignore[reportPrivateUsage]

    def interrupt_after_copy(source: Path, destination: Path) -> None:
        original_copy(source, destination)
        raise OSError("simulated promotion interruption")

    monkeypatch.setattr(archival, "_copy_active_tree", interrupt_after_copy)
    arguments = [
        "close",
        "--summary",
        "Promotion recovery fixture",
        "--idempotency-key",
        "close-promotion-retry",
        "-C",
        str(initialized.layout.root),
    ]
    interrupted = runner.invoke(app, arguments)
    assert interrupted.exit_code != 0
    assert "same idempotency key" in interrupted.stderr
    staging = tuple(initialized.layout.archive_directory.glob(f".{initiative_id}.*.staging"))
    assert len(staging) == 1
    assert inspect_status(initialized.layout).integrity_state.value == "integrity_error"

    monkeypatch.undo()
    resumed = runner.invoke(app, arguments)
    assert resumed.exit_code == 0, resumed.stderr
    assert not tuple(initialized.layout.archive_directory.glob(f".{initiative_id}.*.staging"))
    assert load_archive(initialized.layout, initiative_id).manifest.preliminary is False
