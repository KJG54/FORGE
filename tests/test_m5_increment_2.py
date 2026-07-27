from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

import forge.packs.loader as pack_loader
from forge.cli.app import app
from forge.contracts.actors import Actor
from forge.core.archival import abandon_initiative, load_archive
from forge.core.authorization import owner_actor
from forge.core.lifecycle import (
    InitiativeCreationResult,
    create_initiative,
    load_active_initiative,
)
from forge.errors import ConfigurationError, IntegrityError
from forge.packs.loader import load_pack
from forge.packs.validation import (
    PackResourceKind,
    ValidatedPack,
    calculate_pack_digest,
    validate_pack,
)
from forge.storage.journal import read_journal
from forge.storage.repository import InitializationResult, initialize_repository

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_PACK_ROOT = (
    PROJECT_ROOT / "src" / "forge" / "packs" / "bundled" / "research-basic"
)
SOFTWARE_PACK_ROOT = (
    PROJECT_ROOT / "src" / "forge" / "packs" / "bundled" / "software-basic"
)
EVIDENCE_TEMPLATE = "templates/research-evidence-register.md"
CITATION_TEMPLATE = "templates/research-citation-record.md"
LEGACY_RESEARCH_DIGEST = (
    "sha256:e9d71cfd2bb304005b9b572df839de0860241c7f1cd843ba0f7e7a5056455a87"
)

runner = CliRunner()


def _research_initiative(
    tmp_path: Path,
) -> tuple[InitializationResult, Actor, InitiativeCreationResult]:
    initialized = initialize_repository(tmp_path, owner_display_name="Research Owner")
    actor = owner_actor(initialized.configuration.owner)
    created = create_initiative(
        initialized.layout,
        objective="Use exact governed research templates",
        declared_scope_summary="M5 Increment 2 template boundary only",
        actor=actor,
        trust_pack_data=True,
        pack_id="research-basic",
    )
    return initialized, actor, created


def test_research_templates_are_utf8_data_only_and_digest_bound(
    tmp_path: Path,
) -> None:
    pack = load_pack(RESEARCH_PACK_ROOT, bundled=True)

    assert pack.manifest.version == "0.3.0"
    templates = tuple(
        resource
        for resource in pack.resources
        if resource.kind is PackResourceKind.TEMPLATE
    )
    assert tuple(resource.path for resource in templates) == (
        EVIDENCE_TEMPLATE,
        CITATION_TEMPLATE,
    )
    assert all(resource.content_digest.startswith("sha256:") for resource in pack.resources)
    assert all(resource.content.decode("utf-8") for resource in pack.resources)
    assert b"does not establish" in templates[0].content
    assert b"does not prove" in templates[1].content
    assert pack.manifest.declared_capability_ids == ()

    copied = tmp_path / "changed-pack"
    shutil.copytree(RESEARCH_PACK_ROOT, copied)
    template = copied / EVIDENCE_TEMPLATE
    template.write_text(
        template.read_text(encoding="utf-8") + "\nChanged without a new digest.\n",
        encoding="utf-8",
    )
    with pytest.raises(IntegrityError, match="integrity digest mismatch"):
        load_pack(copied)


def test_pack_loader_refuses_binary_and_unsupported_resource_classes(
    tmp_path: Path,
) -> None:
    binary = tmp_path / "binary-pack"
    shutil.copytree(RESEARCH_PACK_ROOT, binary)
    (binary / CITATION_TEMPLATE).write_bytes(b"\xff\xfe\x00")
    with pytest.raises(ConfigurationError, match="UTF-8 text"):
        load_pack(binary)

    unsupported = tmp_path / "unsupported-pack"
    shutil.copytree(RESEARCH_PACK_ROOT, unsupported)
    manifest = unsupported / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "explanation_paths: []",
            f"explanation_paths: [{EVIDENCE_TEMPLATE}]",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="explanation resources remain unavailable"):
        load_pack(unsupported)


def test_empty_resource_pack_digests_and_pre_resource_locks_remain_compatible() -> None:
    software = load_pack(SOFTWARE_PACK_ROOT, bundled=True)
    assert software.resources == ()
    assert (
        calculate_pack_digest(software.manifest, software.workflows)
        == software.manifest.integrity_digest
    )

    research = load_pack(RESEARCH_PACK_ROOT, bundled=True)
    legacy_manifest = research.manifest.model_copy(
        update={
            "version": "0.1.0",
            "template_paths": (),
            "data_resource_paths": (),
            "integrity_digest": LEGACY_RESEARCH_DIGEST,
        }
    )
    legacy_steps = tuple(
        step.model_copy(
            update={
                "check_requirements": ("evidence-register-structure-reviewed",)
            }
        )
        if step.id == "collect"
        else step
        for step in research.workflow().steps
    )
    legacy_workflow = research.workflow().model_copy(
        update={"version": "0.1.0", "steps": legacy_steps}
    )
    legacy_pack = ValidatedPack(
        RESEARCH_PACK_ROOT,
        legacy_manifest,
        (legacy_workflow,),
    )
    assert (
        calculate_pack_digest(legacy_manifest, (legacy_workflow,))
        == LEGACY_RESEARCH_DIGEST
    )
    validate_pack(legacy_pack)


def test_creation_restart_tamper_detection_and_archive_preserve_exact_templates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized, actor, created = _research_initiative(tmp_path)
    resource_root = initialized.layout.pack_resource_directory

    assert created.active.pack_resources
    assert (resource_root / EVIDENCE_TEMPLATE).read_bytes() == (
        RESEARCH_PACK_ROOT / EVIDENCE_TEMPLATE
    ).read_bytes()
    restarted = load_active_initiative(initialized.layout)
    assert restarted.pack_resources == created.active.pack_resources

    extra = resource_root / "templates" / "unexpected.md"
    extra.write_text("unexpected", encoding="utf-8")
    with pytest.raises(IntegrityError, match="inventory"):
        load_active_initiative(initialized.layout)
    extra.unlink()

    evidence = resource_root / EVIDENCE_TEMPLATE
    original = evidence.read_bytes()
    evidence.write_bytes(original + b"tampered")
    with pytest.raises(IntegrityError, match="integrity digest mismatch"):
        load_active_initiative(initialized.layout)
    evidence.write_bytes(original)

    citation = resource_root / CITATION_TEMPLATE
    citation_original = citation.read_bytes()
    citation.unlink()
    with pytest.raises(IntegrityError, match="inventory"):
        load_active_initiative(initialized.layout)
    citation.write_bytes(citation_original)

    aggregate_size = sum(
        len(resource.content) for resource in created.active.pack_resources
    )
    with monkeypatch.context() as aggregate_limit:
        aggregate_limit.setattr(
            pack_loader,
            "MAX_PACK_TOTAL_BYTES",
            aggregate_size - 1,
        )
        with pytest.raises(IntegrityError, match="aggregate bytes"):
            load_active_initiative(initialized.layout)

    abandoned = abandon_initiative(
        initialized.layout,
        reason="Archive the Increment 2 resource fixture",
        unfinished_work_summary="Research workflow was not started",
        unresolved_risks=("The research objective remains unanswered",),
        actor=actor,
    )
    archive = load_archive(initialized.layout, abandoned.abandonment.initiative_id)
    assert archive.active.pack_resources == created.active.pack_resources
    archived_paths = {item.path for item in archive.manifest.files}
    assert f"pack-resources/{EVIDENCE_TEMPLATE}" in archived_paths
    assert f"pack-resources/{CITATION_TEMPLATE}" in archived_paths


def test_precommit_creation_failure_removes_new_locked_template_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Rollback Owner")

    def fail_record_write(*_args: object, **_kwargs: object) -> None:
        raise IntegrityError("simulated record write failure")

    monkeypatch.setattr("forge.core.lifecycle.write_record", fail_record_write)
    with pytest.raises(IntegrityError, match="simulated record write failure"):
        create_initiative(
            initialized.layout,
            objective="Fail before the creation event",
            declared_scope_summary="Prove template rollback",
            actor=owner_actor(initialized.configuration.owner),
            trust_pack_data=True,
            pack_id="research-basic",
        )

    assert not initialized.layout.pack_resource_directory.exists()
    assert not any(initialized.layout.active_directory.iterdir())


def test_template_cli_lists_and_shows_available_then_locked_bytes(
    tmp_path: Path,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="CLI Template Owner")
    available_list = runner.invoke(
        app,
        ["pack", "template", "list", "research-basic", "-C", str(tmp_path)],
    )
    assert available_list.exit_code == 0, available_list.stderr
    assert "Templates from available research-basic@0.3.0" in available_list.stdout
    assert EVIDENCE_TEMPLATE in available_list.stdout
    assert CITATION_TEMPLATE in available_list.stdout

    available_show = runner.invoke(
        app,
        [
            "pack",
            "template",
            "show",
            "research-basic",
            CITATION_TEMPLATE,
            "-C",
            str(tmp_path),
        ],
    )
    assert available_show.exit_code == 0, available_show.stderr
    assert available_show.stdout == (
        RESEARCH_PACK_ROOT / CITATION_TEMPLATE
    ).read_text(encoding="utf-8")

    create_initiative(
        initialized.layout,
        objective="Inspect locked templates",
        declared_scope_summary="Read-only CLI template inspection",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
        pack_id="research-basic",
    )
    event_count = len(read_journal(initialized.layout.event_journal_file))
    locked_list = runner.invoke(
        app,
        ["pack", "template", "list", "research-basic", "-C", str(tmp_path)],
    )
    assert locked_list.exit_code == 0, locked_list.stderr
    assert "Templates from locked research-basic@0.3.0" in locked_list.stdout
    assert len(read_journal(initialized.layout.event_journal_file)) == event_count

    unknown = runner.invoke(
        app,
        [
            "pack",
            "template",
            "show",
            "research-basic",
            "templates/unknown.md",
            "-C",
            str(tmp_path),
        ],
    )
    assert unknown.exit_code == 10
    assert "has no declared template" in unknown.stderr
    assert len(read_journal(initialized.layout.event_journal_file)) == event_count
