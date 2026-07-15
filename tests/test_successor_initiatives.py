from pathlib import Path
from uuid import UUID, uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor, ActorType
from forge.contracts.initiatives import Initiative, InitiativeReference
from forge.contracts.state import StepState
from forge.core.acceptance import list_acceptances
from forge.core.archival import abandon_initiative, load_archive
from forge.core.artifacts import add_artifact
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative, load_active_initiative
from forge.core.status import inspect_status
from forge.errors import AuthorizationError, ConfigurationError, ConflictError, IntegrityError
from forge.storage.records import load_record, write_record
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initialized(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    return initialized, owner_actor(initialized.configuration.owner)


def _create(
    initialized: InitializationResult,
    actor: Actor,
    *,
    objective: str,
    predecessor_ids: tuple[UUID, ...] = (),
) -> UUID:
    result = create_initiative(
        initialized.layout,
        objective=objective,
        declared_scope_summary=f"Governed scope for {objective}",
        actor=actor,
        trust_pack_data=True,
        predecessor_ids=predecessor_ids,
    )
    return result.active.initiative.id


def _abandon(initialized: InitializationResult, actor: Actor) -> UUID:
    result = abandon_initiative(
        initialized.layout,
        reason="Stop this attempt before successful closure",
        unfinished_work_summary="All workflow steps remain unfinished",
        unresolved_risks=("The intended outcome was not accepted",),
        actor=actor,
    )
    return result.abandonment.initiative_id


def test_successor_requires_owner_and_valid_unique_archived_predecessor(
    tmp_path: Path,
) -> None:
    initialized, actor = _initialized(tmp_path)
    predecessor_id = _create(initialized, actor, objective="First attempt")
    _abandon(initialized, actor)
    outsider = Actor(
        id=uuid4(),
        actor_type=ActorType.HUMAN_CONTRIBUTOR,
        display_label="Contributor",
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        create_initiative(
            initialized.layout,
            objective="Unauthorized successor",
            declared_scope_summary="Must remain owner-authorized",
            actor=outsider,
            trust_pack_data=True,
            predecessor_ids=(predecessor_id,),
        )
    with pytest.raises(ConflictError, match="Successor-initiative"):
        _create(initialized, actor, objective="Missing predecessor")
    with pytest.raises(ConfigurationError, match="must not contain duplicates"):
        _create(
            initialized,
            actor,
            objective="Duplicate predecessor",
            predecessor_ids=(predecessor_id, predecessor_id),
        )
    with pytest.raises(ConflictError, match="not archived initiatives"):
        _create(
            initialized,
            actor,
            objective="Unknown predecessor",
            predecessor_ids=(uuid4(),),
        )


def test_successor_has_fresh_governance_and_preserves_predecessor_archive(
    tmp_path: Path,
) -> None:
    initialized, actor = _initialized(tmp_path)
    predecessor_id = _create(initialized, actor, objective="Archived attempt")
    _abandon(initialized, actor)
    before = load_archive(initialized.layout, predecessor_id)

    successor_id = _create(
        initialized,
        actor,
        objective="Fresh successor attempt",
        predecessor_ids=(predecessor_id,),
    )
    active = load_active_initiative(initialized.layout)
    reference = active.initiative.predecessor_references[0]
    assert successor_id != predecessor_id
    assert reference == InitiativeReference(
        initiative_id=predecessor_id,
        relationship="successor-of",
        archive_reference=f".forge/archive/{predecessor_id}",
    )
    assert active.state.journal_head_sequence == 1
    assert active.state.current_artifact_revisions == {}
    assert active.state.stale_record_ids == ()
    assert not list_acceptances(initialized.layout)
    assert next(iter(active.state.step_states.values())) is StepState.READY
    assert load_archive(initialized.layout, predecessor_id).manifest == before.manifest


def test_successor_supports_multiple_predecessors_and_validates_persisted_links(
    tmp_path: Path,
) -> None:
    initialized, actor = _initialized(tmp_path)
    first_id = _create(initialized, actor, objective="First archived attempt")
    _abandon(initialized, actor)
    second_id = _create(
        initialized,
        actor,
        objective="Second archived attempt",
        predecessor_ids=(first_id,),
    )
    _abandon(initialized, actor)

    _create(
        initialized,
        actor,
        objective="Combined successor",
        predecessor_ids=(second_id, first_id),
    )
    active = load_active_initiative(initialized.layout)
    assert tuple(
        item.initiative_id for item in active.initiative.predecessor_references
    ) == tuple(sorted((first_id, second_id), key=str))

    initiative = load_record(initialized.layout.initiative_file, Initiative)
    tampered = initiative.model_copy(
        update={
            "predecessor_references": (
                initiative.predecessor_references[0].model_copy(
                    update={"relationship": "unverified-lineage"}
                ),
                *initiative.predecessor_references[1:],
            )
        }
    )
    write_record(initialized.layout.initiative_file, tampered, overwrite=True)
    with pytest.raises(IntegrityError, match="predecessor reference"):
        load_active_initiative(initialized.layout)


def test_archive_views_summarize_multiple_archives_and_are_read_only(tmp_path: Path) -> None:
    initialized, actor = _initialized(tmp_path)
    first_id = _create(initialized, actor, objective="First archived attempt")
    _abandon(initialized, actor)
    second_id = _create(
        initialized,
        actor,
        objective="Second archived attempt",
        predecessor_ids=(first_id,),
    )
    _abandon(initialized, actor)
    _create(
        initialized,
        actor,
        objective="Current combined successor",
        predecessor_ids=(first_id, second_id),
    )
    before = {
        path.relative_to(initialized.layout.root): path.read_bytes()
        for path in initialized.layout.local_directory.rglob("*")
        if path.is_file()
    }

    report = inspect_status(initialized.layout)
    assert tuple(item.initiative_id for item in report.archive_summaries) == tuple(
        sorted((first_id, second_id), key=str)
    )
    summaries = {item.initiative_id: item for item in report.archive_summaries}
    assert summaries[first_id].objective == "First archived attempt"
    assert summaries[second_id].predecessor_ids == (first_id,)
    assert all(item.event_count == item.journal_head_sequence for item in report.archive_summaries)
    assert all(item.journal_head_hash is not None for item in report.archive_summaries)

    status = runner.invoke(
        app,
        ["status", "--archive", str(second_id), "-C", str(initialized.layout.root)],
    )
    assert status.exit_code == 0, status.stderr
    assert f"Archived initiative: {first_id} - abandoned" in status.stdout
    assert f"Predecessor: {first_id}" in status.stdout
    assert "Archive files:" in status.stdout
    assert "Journal head hash: sha256:" in status.stdout
    history = runner.invoke(
        app,
        ["history", "--archive", str(second_id), "-C", str(initialized.layout.root)],
    )
    assert history.exit_code == 0, history.stderr
    assert f"History source: archive {second_id}" in history.stdout
    assert "Events: 2 of 2" in history.stdout
    assert "hash=sha256:" in history.stdout
    assert "previous=chain-root" in history.stdout

    after = {
        path.relative_to(initialized.layout.root): path.read_bytes()
        for path in initialized.layout.local_directory.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_create_successor_cli_reports_lineage(tmp_path: Path) -> None:
    initialized, actor = _initialized(tmp_path)
    predecessor_id = _create(initialized, actor, objective="CLI predecessor")
    _abandon(initialized, actor)
    result = runner.invoke(
        app,
        [
            "create",
            "CLI successor",
            "--scope",
            "Fresh CLI-governed successor scope",
            "--predecessor",
            str(predecessor_id),
            "--trust-pack-data",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert f"Predecessor: {predecessor_id}" in result.stdout
    assert str(load_active_initiative(initialized.layout).initiative.id) in result.stdout


def test_successor_reuses_only_exact_terminal_predecessor_bytes(tmp_path: Path) -> None:
    initialized, actor = _initialized(tmp_path)
    predecessor_id = _create(initialized, actor, objective="Artifact predecessor")
    target = tmp_path / "outputs" / "project-artifacts.md"
    target.parent.mkdir()
    target.write_bytes(b"exact predecessor bytes\n")
    predecessor_artifact = add_artifact(
        initialized.layout,
        path="outputs/project-artifacts.md",
        role="project-artifacts",
        title="Predecessor deliverable",
        actor=actor,
        media_type="text/markdown",
    )
    _abandon(initialized, actor)
    _create(
        initialized,
        actor,
        objective="Artifact-reusing successor",
        predecessor_ids=(predecessor_id,),
    )

    reused = add_artifact(
        initialized.layout,
        path="outputs/project-artifacts.md",
        role="project-artifacts",
        title="Explicitly reused predecessor deliverable",
        actor=actor,
        media_type="text/markdown",
        predecessor_revision_id=predecessor_artifact.revision.id,
    )
    assert reused.revision.id != predecessor_artifact.revision.id
    assert reused.revision.content_digest == predecessor_artifact.revision.content_digest
    assert reused.revision.provenance.source_type == "predecessor-artifact"
    assert reused.revision.provenance.metadata["predecessor_initiative_id"] == str(
        predecessor_id
    )
    assert load_active_initiative(initialized.layout).state.journal_head_sequence == 2

    other = tmp_path / "outputs" / "lessons.md"
    other.write_bytes(b"different bytes\n")
    with pytest.raises(ConflictError, match="do not match"):
        add_artifact(
            initialized.layout,
            path="outputs/lessons.md",
            role="lessons",
            title="Invalid predecessor reuse",
            actor=actor,
            media_type="text/markdown",
            predecessor_revision_id=predecessor_artifact.revision.id,
        )
