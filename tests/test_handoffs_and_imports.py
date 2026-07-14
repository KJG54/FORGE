import json
import shutil
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import yaml
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor
from forge.contracts.agents import AgentResult, ReturnedFile
from forge.contracts.state import StepState
from forge.contracts.verification import CheckOutcome
from forge.core.acceptance import record_acceptance
from forge.core.artifacts import list_artifacts, show_artifact
from forge.core.authorization import owner_actor
from forge.core.handoffs import create_handoff
from forge.core.imports import apply_result_import, preview_result_import
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.verification import complete_step, record_check, record_evidence, verify_step
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.records import render_record
from forge.storage.repository import InitializationResult, initialize_repository


def _initiative(tmp_path: Path) -> tuple[InitializationResult, Actor]:
    repository = tmp_path / "repository"
    repository.mkdir()
    initialized = initialize_repository(repository, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Produce bounded discovery outputs",
        declared_scope_summary="Objective and requirements only",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized, actor


def _bundle(
    tmp_path: Path,
    source_id: UUID,
    files: tuple[tuple[str, str, bytes], ...],
    *,
    result_id: UUID | None = None,
    extra_file: tuple[str, bytes] | None = None,
) -> tuple[Path, AgentResult]:
    bundle = tmp_path / f"bundle-{uuid4()}"
    bundle.mkdir()
    returned: list[ReturnedFile] = []
    for source, target, content in files:
        path = bundle / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        returned.append(
            ReturnedFile(
                source_path=source,
                proposed_target_path=target,
                media_type="text/markdown",
            )
        )
    if extra_file is not None:
        path = bundle / extra_file[0]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(extra_file[1])
    result = AgentResult(
        id=result_id or uuid4(),
        source_run_or_handoff_id=source_id,
        worker_claims=("Returned requested files",),
        returned_files=tuple(returned),
        declared_limitations=("Worker output is untrusted",),
        tool_metadata={"worker": "manual-fixture"},
    )
    manifest = bundle / "result.json"
    manifest.write_bytes(render_record(result))
    return manifest, result


def test_handoff_is_portable_local_context_without_governance_mutation(
    tmp_path: Path,
) -> None:
    initialized, _ = _initiative(tmp_path)
    before = initialized.layout.event_journal_file.read_bytes()
    generated = create_handoff(
        initialized.layout,
        step_id="discover",
        constraints=("Do not modify unrelated files",),
    )

    assert generated.handoff.step_id == "discover"
    assert generated.handoff.required_outputs == (
        "objective-and-constraints",
        "requirements",
    )
    assert generated.json_path.is_file()
    assert generated.markdown_path.is_file()
    assert generated.result_schema_path.is_file()
    schema = json.loads(generated.result_schema_path.read_text(encoding="utf-8"))
    assert schema["title"] == "AgentResult"
    assert initialized.layout.event_journal_file.read_bytes() == before


def test_preview_is_non_mutating_and_apply_atomically_registers_new_artifacts(
    tmp_path: Path,
) -> None:
    initialized, actor = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    manifest, result = _bundle(
        tmp_path,
        handoff.handoff.id,
        (
            ("objective.md", "objective.md", b"# Objective\nBounded work.\n"),
            ("requirements.md", "requirements.md", b"# Requirements\n- Safe import.\n"),
        ),
    )
    roles = {
        "objective.md": "objective-and-constraints",
        "requirements.md": "requirements",
    }

    preview = preview_result_import(
        initialized.layout,
        manifest_path=manifest,
        role_assignments=roles,
    )
    assert not preview.blockers
    assert {item.action for item in preview.actions} == {"create-artifact"}
    assert not (initialized.layout.root / "objective.md").exists()
    assert preview.staged.directory.is_dir()
    assert load_active_initiative(initialized.layout).state.current_artifact_revisions == {}

    imported = apply_result_import(
        initialized.layout,
        manifest_path=manifest,
        actor=actor,
        role_assignments=roles,
    )
    assert imported.event.event_type == "result-imported"
    assert imported.preview.staged.result.id == result.id
    assert (initialized.layout.root / "objective.md").read_bytes().startswith(b"# Objective")
    views = list_artifacts(initialized.layout)
    assert {item.artifact.role for item in views} == {
        "objective-and-constraints",
        "requirements",
    }
    assert all(item.current_revision.provenance.metadata == {"untrusted": True} for item in views)
    shutil.rmtree(handoff.directory)
    shutil.rmtree(imported.preview.staged.directory)
    restarted = load_active_initiative(initialized.layout)
    assert len(restarted.state.current_artifact_revisions) == 2
    assert restarted.state.step_states["discover"] is StepState.READY
    with pytest.raises(ConflictError, match="already imported"):
        preview_result_import(
            initialized.layout,
            manifest_path=manifest,
            role_assignments=roles,
        )


def test_governed_collision_requires_and_creates_explicit_revision(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    first_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("objective.md", "objective.md", b"First objective"),),
    )
    apply_result_import(
        initialized.layout,
        manifest_path=first_manifest,
        actor=actor,
        role_assignments={"objective.md": "objective-and-constraints"},
    )
    first = list_artifacts(initialized.layout)[0]
    assert first.current_revision.preserved_object_path is not None
    first_object = initialized.layout.root / first.current_revision.preserved_object_path
    first_bytes = first_object.read_bytes()
    second_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("objective.md", "objective.md", b"Second objective"),),
    )

    blocked = preview_result_import(initialized.layout, manifest_path=second_manifest)
    assert "governed collision requires" in blocked.blockers[0]
    with pytest.raises(ConflictError, match="Import preview is blocked"):
        apply_result_import(
            initialized.layout,
            manifest_path=second_manifest,
            actor=actor,
        )
    imported = apply_result_import(
        initialized.layout,
        manifest_path=second_manifest,
        actor=actor,
        collision_actions={"objective.md": "revise"},
    )
    assert imported.revisions[0].revision_number == 2
    history = show_artifact(initialized.layout, first.artifact.id)
    assert [item.revision_number for item in history.revisions] == [1, 2]
    assert first_object.read_bytes() == first_bytes
    assert first.current_revision.id in imported.revisions[0].stale_dependency_effects


def test_ungoverned_collision_requires_replace_and_role(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    target = initialized.layout.root / "requirements.md"
    target.write_text("Local draft", encoding="utf-8")
    manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("requirements.md", "requirements.md", b"Imported requirements"),),
    )
    preview = preview_result_import(
        initialized.layout,
        manifest_path=manifest,
        role_assignments={"requirements.md": "requirements"},
    )
    assert any("ungoverned collision requires" in item for item in preview.blockers)
    apply_result_import(
        initialized.layout,
        manifest_path=manifest,
        actor=actor,
        role_assignments={"requirements.md": "requirements"},
        collision_actions={"requirements.md": "replace"},
    )
    assert target.read_bytes() == b"Imported requirements"


def test_governed_manual_run_can_be_the_result_source(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    run = begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    manifest, result = _bundle(
        tmp_path,
        run.run.id,
        (("objective.md", "objective.md", b"Run-produced objective"),),
    )
    imported = apply_result_import(
        initialized.layout,
        manifest_path=manifest,
        actor=actor,
        role_assignments={"objective.md": "objective-and-constraints"},
    )
    assert imported.event.run_id == run.run.id
    assert imported.preview.staged.result.id == result.id
    assert load_active_initiative(initialized.layout).state.step_states[
        "discover"
    ] is StepState.IN_PROGRESS


def test_late_imported_revision_invalidates_completed_acceptance(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (
            ("objective.md", "objective.md", b"Initial objective"),
            ("requirements.md", "requirements.md", b"Initial requirements"),
        ),
    )
    imported = apply_result_import(
        initialized.layout,
        manifest_path=manifest,
        actor=actor,
        role_assignments={
            "objective.md": "objective-and-constraints",
            "requirements.md": "requirements",
        },
    )
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    claim = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Imported outputs reviewed",
        actor=actor,
    )
    check = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"invocation": "manual review"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
        exit_status=0,
    )
    evidence = record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Bind imported outputs",
        actor=actor,
        artifact_revision_ids=tuple(item.id for item in imported.revisions),
        check_result_ids=(check.check.id,),
        claim_ids=(claim.claim.id,),
    )
    verify_step(initialized.layout, step_id="discover")
    acceptance = record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Imported discovery outputs",
        actor=actor,
    )
    late_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("objective.md", "objective.md", b"Late revised objective"),),
    )
    late = apply_result_import(
        initialized.layout,
        manifest_path=late_manifest,
        actor=actor,
        collision_actions={"objective.md": "revise"},
    )
    active = load_active_initiative(initialized.layout)
    assert late.revisions[0].revision_number == 2
    assert active.state.step_states["discover"] is StepState.INVALIDATED
    assert active.state.step_states["plan"] is StepState.PENDING
    assert acceptance.acceptance.id in active.state.stale_record_ids
    assert evidence.evidence.id in active.state.stale_record_ids


@pytest.mark.parametrize(
    "source,target",
    [
        ("../escape.md", "objective.md"),
        ("objective.md", "../escape.md"),
        ("objective.md", "C:/absolute.md"),
        ("objective.md", ".forge/active/owned.md"),
    ],
)
def test_unsafe_paths_are_rejected(
    tmp_path: Path,
    source: str,
    target: str,
) -> None:
    initialized, _ = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    bundle = tmp_path / "unsafe-bundle"
    bundle.mkdir()
    if source == "objective.md":
        (bundle / source).write_text("content", encoding="utf-8")
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "id": str(uuid4()),
        "source_run_or_handoff_id": str(handoff.handoff.id),
        "worker_claims": ["claim"],
        "returned_files": [
            {
                "schema_version": "1.0",
                "source_path": source,
                "proposed_target_path": target,
            }
        ],
        "declared_limitations": [],
        "tool_metadata": {},
    }
    manifest = bundle / "result.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises((ConfigurationError, SecurityError)):
        preview_result_import(initialized.layout, manifest_path=manifest)


def test_undeclared_files_duplicate_targets_secrets_and_limits_are_rejected(
    tmp_path: Path,
) -> None:
    initialized, _ = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    undeclared_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("objective.md", "objective.md", b"Objective"),),
        extra_file=("undeclared.txt", b"not declared"),
    )
    with pytest.raises(SecurityError, match="inventory"):
        preview_result_import(initialized.layout, manifest_path=undeclared_manifest)

    duplicate_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (
            ("one.md", "objective.md", b"one"),
            ("two.md", "objective.md", b"two"),
        ),
    )
    with pytest.raises(SecurityError, match="duplicate target"):
        preview_result_import(initialized.layout, manifest_path=duplicate_manifest)

    secret_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("secret.txt", "objective.md", b"api_key=abcdefghijklmnopqrstuvwxyz123456"),),
    )
    with pytest.raises(SecurityError, match="credential"):
        preview_result_import(initialized.layout, manifest_path=secret_manifest)

    configuration = yaml.safe_load(
        initialized.layout.configuration_file.read_text(encoding="utf-8")
    )
    configuration["imports"]["max_files"] = 1
    initialized.layout.configuration_file.write_text(
        yaml.safe_dump(configuration, sort_keys=False), encoding="utf-8"
    )
    excessive_count_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (
            ("one.md", "objective.md", b"one"),
            ("two.md", "requirements.md", b"two"),
        ),
    )
    with pytest.raises(SecurityError, match="files, exceeding"):
        preview_result_import(initialized.layout, manifest_path=excessive_count_manifest)

    configuration["imports"]["max_files"] = 2
    configuration["imports"]["max_file_bytes"] = 4
    configuration["imports"]["max_total_bytes"] = 5
    initialized.layout.configuration_file.write_text(
        yaml.safe_dump(configuration, sort_keys=False), encoding="utf-8"
    )
    excessive_total_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (
            ("one.md", "objective.md", b"123"),
            ("two.md", "requirements.md", b"456"),
        ),
    )
    with pytest.raises(SecurityError, match="total limit"):
        preview_result_import(initialized.layout, manifest_path=excessive_total_manifest)

    configuration["imports"]["max_total_bytes"] = 4
    initialized.layout.configuration_file.write_text(
        yaml.safe_dump(configuration, sort_keys=False), encoding="utf-8"
    )
    oversized_manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("large.md", "objective.md", b"12345"),),
    )
    with pytest.raises(SecurityError, match="per-file"):
        preview_result_import(initialized.layout, manifest_path=oversized_manifest)


def test_declared_digest_mismatch_is_rejected_and_preserved(tmp_path: Path) -> None:
    initialized, _ = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    manifest, result = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("objective.md", "objective.md", b"Objective"),),
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["returned_files"][0]["declared_digest"] = f"sha256:{'0' * 64}"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SecurityError, match="declared digest"):
        preview_result_import(initialized.layout, manifest_path=manifest)
    assert (
        initialized.layout.import_staging_directory / str(result.id) / "manifest.json"
    ).is_file()


def test_tampered_import_record_fails_restart_integrity(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    manifest, result = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("objective.md", "objective.md", b"Objective"),),
    )
    apply_result_import(
        initialized.layout,
        manifest_path=manifest,
        actor=actor,
        role_assignments={"objective.md": "objective-and-constraints"},
    )
    record = initialized.layout.imported_result_directory / f"{result.id}.json"
    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["worker_claims"] = ["tampered claim"]
    record.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IntegrityError, match="Imported result"):
        load_active_initiative(initialized.layout)


def test_failed_apply_rolls_back_targets_records_and_new_objects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, actor = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("objective.md", "objective.md", b"Rollback objective"),),
    )

    def fail_commit(*_args: object, **_kwargs: object) -> object:
        raise IntegrityError("simulated event failure")

    monkeypatch.setattr("forge.core.imports.append_event_and_update_snapshot", fail_commit)
    with pytest.raises(IntegrityError, match="simulated event failure"):
        apply_result_import(
            initialized.layout,
            manifest_path=manifest,
            actor=actor,
            role_assignments={"objective.md": "objective-and-constraints"},
        )
    assert not (initialized.layout.root / "objective.md").exists()
    assert not initialized.layout.imported_result_directory.exists()
    assert not initialized.layout.artifact_directory.exists()
    assert not any(path.is_file() for path in initialized.layout.object_directory.rglob("*"))
    assert load_active_initiative(initialized.layout).state.current_artifact_revisions == {}


def test_staged_bytes_cannot_change_between_preview_and_apply(tmp_path: Path) -> None:
    initialized, actor = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    manifest, _ = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("objective.md", "objective.md", b"Previewed objective"),),
    )
    preview = preview_result_import(
        initialized.layout,
        manifest_path=manifest,
        role_assignments={"objective.md": "objective-and-constraints"},
    )
    (preview.staged.directory / "files" / "objective.md").write_bytes(b"changed later")
    with pytest.raises(IntegrityError, match="inventory no longer matches"):
        apply_result_import(
            initialized.layout,
            manifest_path=manifest,
            actor=actor,
            role_assignments={"objective.md": "objective-and-constraints"},
        )
    assert not (initialized.layout.root / "objective.md").exists()


def test_failed_secret_staging_is_preserved_and_never_reaches_project(tmp_path: Path) -> None:
    initialized, _ = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    manifest, result = _bundle(
        tmp_path,
        handoff.handoff.id,
        (("secret.txt", "objective.md", b"password=abcdefghijklmnopqrstuvwxyz123456"),),
    )
    with pytest.raises(SecurityError, match="credential"):
        preview_result_import(initialized.layout, manifest_path=manifest)
    failed = initialized.layout.import_staging_directory / str(result.id)
    assert (failed / "manifest.json").is_file()
    assert not (initialized.layout.root / "objective.md").exists()


def test_source_symlink_escape_is_rejected_when_supported(tmp_path: Path) -> None:
    initialized, _ = _initiative(tmp_path)
    handoff = create_handoff(initialized.layout, step_id="discover")
    bundle = tmp_path / "symlink-bundle"
    bundle.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    linked = bundle / "objective.md"
    try:
        linked.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")
    result = AgentResult(
        id=uuid4(),
        source_run_or_handoff_id=handoff.handoff.id,
        worker_claims=("claim",),
        returned_files=(
            ReturnedFile(
                source_path="objective.md",
                proposed_target_path="objective.md",
            ),
        ),
    )
    manifest = bundle / "result.json"
    manifest.write_bytes(render_record(result))
    with pytest.raises(SecurityError, match="symbolic link"):
        preview_result_import(initialized.layout, manifest_path=manifest)


def test_handoff_and_import_result_cli_preview_and_apply(tmp_path: Path) -> None:
    initialized, _ = _initiative(tmp_path)
    runner = CliRunner()
    generated = runner.invoke(
        app,
        ["handoff", "discover", "-C", str(initialized.layout.root)],
    )
    assert generated.exit_code == 0, generated.stdout
    handoff_id = UUID(
        next(
            line.removeprefix("Created handoff ")
            for line in generated.stdout.splitlines()
            if line.startswith("Created handoff ")
        )
    )
    manifest, _ = _bundle(
        tmp_path,
        handoff_id,
        (("objective.md", "objective.md", b"CLI objective"),),
    )
    preview = runner.invoke(
        app,
        [
            "import-result",
            str(manifest),
            "--role",
            "objective.md=objective-and-constraints",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert preview.exit_code == 0, preview.stdout
    assert "Preview only" in preview.stdout
    assert not (initialized.layout.root / "objective.md").exists()
    applied = runner.invoke(
        app,
        [
            "import-result",
            str(manifest),
            "--role",
            "objective.md=objective-and-constraints",
            "--apply",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert applied.exit_code == 0, applied.stdout
    assert "Imported event:" in applied.stdout
    assert "remains subject to claims" in applied.stdout
