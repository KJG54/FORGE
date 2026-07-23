from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.capabilities import (
    CapabilityTrustState,
    LocalValidatorDefinition,
    SideEffectClass,
)
from forge.contracts.configuration import CapabilityConfiguration
from forge.core.authorization import owner_actor
from forge.core.capabilities import (
    approve_capability,
    inspect_capability,
    list_capabilities,
    list_capability_approvals,
)
from forge.core.lifecycle import create_initiative
from forge.core.verification import list_checks
from forge.errors import ConflictError
from forge.packs.loader import available_packs, load_pack
from forge.packs.validation import calculate_pack_digest
from forge.storage.configuration import load_configuration, render_configuration
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _validator(
    *,
    executable: str = sys.executable,
    arguments: tuple[str, ...] = ("-m", "pytest", "-q"),
    environment_access: tuple[str, ...] = ("PATH",),
    working_directory: str | None = None,
) -> LocalValidatorDefinition:
    return LocalValidatorDefinition(
        id="validator.project.tests",
        version="1.0.0",
        provider="Project test runner",
        provider_version="declared-1",
        purpose="Run the project test suite against current artifact revisions",
        executable=executable,
        arguments=arguments,
        working_directory=working_directory,
        timeout_seconds=300,
        expected_outputs=("exit-status", "stdout", "stderr"),
        environment_access=environment_access,
        side_effect_class=SideEffectClass.READ_ONLY,
    )


def _initiative_with_validator(
    tmp_path: Path,
    validator: LocalValidatorDefinition | None = None,
) -> InitializationResult:
    tmp_path.mkdir(parents=True, exist_ok=True)
    initialized = initialize_repository(tmp_path, owner_display_name="Validator Owner")
    configured = initialized.configuration.model_copy(
        update={
            "capabilities": initialized.configuration.capabilities.model_copy(
                update={"local_validators": (validator or _validator(),)}
            )
        }
    )
    initialized.layout.configuration_file.write_bytes(render_configuration(configured))
    create_initiative(
        initialized.layout,
        objective="Prove the trusted local validator boundary",
        declared_scope_summary="Validator declaration and authorization only",
        actor=owner_actor(configured.owner),
        trust_pack_data=True,
    )
    return initialized


def test_validator_declaration_requires_vector_and_bounded_permissions() -> None:
    values = _validator().model_dump(mode="json")
    values["command"] = "python -m pytest -q"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LocalValidatorDefinition.model_validate(values)

    with pytest.raises(ValidationError, match="variable names only"):
        _validator(environment_access=("PATH=C:\\secret",))
    with pytest.raises(ValidationError, match="single-line"):
        _validator(arguments=("-m", "pytest\nwhoami"))
    with pytest.raises(ValidationError, match=r"must start with 'validator\.'"):
        LocalValidatorDefinition.model_validate(
            {**_validator().model_dump(mode="json"), "id": "agent.not-a-validator"}
        )
    with pytest.raises(ValidationError, match="at least one expected output"):
        LocalValidatorDefinition.model_validate(
            {**_validator().model_dump(mode="json"), "expected_outputs": []}
        )
    with pytest.raises(ValidationError, match="less than or equal to 3600"):
        LocalValidatorDefinition.model_validate(
            {**_validator().model_dump(mode="json"), "timeout_seconds": 3601}
        )
    with pytest.raises(ValidationError, match="IDs must be unique"):
        CapabilityConfiguration(local_validators=(_validator(), _validator()))


def test_validator_inspection_and_approval_bind_the_exact_disabled_profile(
    tmp_path: Path,
) -> None:
    initialized = _initiative_with_validator(tmp_path)

    inspection = inspect_capability(initialized.layout, "validator.project.tests")

    assert inspection.capability_type == "validator"
    assert inspection.compatible
    assert inspection.definition.executable == str(Path(sys.executable).resolve())
    assert inspection.definition.arguments == ("-m", "pytest", "-q")
    assert inspection.definition.working_directory_rules == ()
    assert inspection.definition.timeout_seconds == 300
    assert inspection.definition.verification_hooks == (
        "exit-status",
        "stdout",
        "stderr",
    )
    assert inspection.environment_access == ("PATH",)
    assert inspection.definition.side_effect_class is SideEffectClass.READ_ONLY
    assert not list_capability_approvals(
        initialized.layout,
        capability_id="validator.project.tests",
    )

    result = approve_capability(
        initialized.layout,
        capability_id="validator.project.tests",
        scope=CapabilityTrustState.APPROVED_FOR_PROJECT,
        rationale="Approve only this declared non-shell validator profile",
        actor=owner_actor(initialized.configuration.owner),
    )
    view = list_capability_approvals(
        initialized.layout,
        capability_id="validator.project.tests",
    )[0]
    assert view.active
    assert result.approval.capability_digest == inspection.definition_digest
    assert result.approval.arguments == ("-m", "pytest", "-q")
    assert result.approval.environment_access == ("PATH",)
    assert list_checks(initialized.layout) == ()
    assert not any(initialized.layout.governed_run_directory.glob("*.json"))

    configuration = initialized.configuration.model_copy(
        update={
            "capabilities": initialized.configuration.capabilities.model_copy(
                update={
                    "local_validators": (
                        _validator(arguments=("-m", "pytest", "-q", "--disable-warnings")),
                    )
                }
            )
        }
    )
    initialized.layout.configuration_file.write_bytes(render_configuration(configuration))
    changed = list_capability_approvals(
        initialized.layout,
        capability_id="validator.project.tests",
    )[0]
    assert not changed.applicable
    assert not changed.active


def test_validator_cli_preview_is_read_only_and_shows_the_complete_profile(
    tmp_path: Path,
) -> None:
    initialized = _initiative_with_validator(tmp_path)
    before = initialized.layout.event_journal_file.read_bytes()

    inspected = runner.invoke(
        app,
        [
            "capability",
            "inspect",
            "validator.project.tests",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert inspected.exit_code == 0, inspected.stdout
    assert "Capability type: validator" in inspected.stdout
    assert "Argument construction: declared argument vector; no shell string" in inspected.stdout
    assert "Working-directory rules:\n- repository root" in inspected.stdout
    assert "Timeout: 300 seconds" in inspected.stdout
    assert "Expected outputs:\n- exit-status\n- stdout\n- stderr" in inspected.stdout
    assert "Approval readiness: ready" in inspected.stdout

    preview = runner.invoke(
        app,
        [
            "capability",
            "approve",
            "validator.project.tests",
            "--scope",
            "approved-once",
            "--rationale",
            "Review the exact validator profile",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert preview.exit_code == 0, preview.stdout
    assert "Preview only" in preview.stdout
    assert initialized.layout.event_journal_file.read_bytes() == before
    assert not list_capability_approvals(initialized.layout)


def test_unavailable_and_batch_validator_profiles_fail_closed(tmp_path: Path) -> None:
    missing = _initiative_with_validator(
        tmp_path / "missing",
        _validator(executable="forge-validator-that-does-not-exist"),
    )
    inspection = inspect_capability(missing.layout, "validator.project.tests")
    assert not inspection.compatible
    assert "not found on PATH" in inspection.availability_detail
    with pytest.raises(ConflictError, match="cannot be approved"):
        approve_capability(
            missing.layout,
            capability_id="validator.project.tests",
            scope=CapabilityTrustState.APPROVED_ONCE,
            rationale="This must fail before any execution authority is recorded",
            actor=owner_actor(missing.configuration.owner),
        )

    batch_root = tmp_path / "batch"
    tools = batch_root / "tools"
    tools.mkdir(parents=True)
    batch = tools / "validator.cmd"
    batch.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
    batch_initialized = _initiative_with_validator(
        batch_root,
        _validator(executable="tools/validator.cmd"),
    )
    batch_inspection = inspect_capability(
        batch_initialized.layout,
        "validator.project.tests",
    )
    assert not batch_inspection.compatible
    assert "batch command shims are not accepted" in batch_inspection.availability_detail

    invalid_working_directory = _initiative_with_validator(
        tmp_path / "working-directory",
        _validator(working_directory="missing-directory"),
    )
    working_directory_inspection = inspect_capability(
        invalid_working_directory.layout,
        "validator.project.tests",
    )
    assert not working_directory_inspection.compatible
    assert "working directory cannot be resolved safely" in (
        working_directory_inspection.availability_detail
    )


def test_pack_data_does_not_register_a_validator_capability(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Pack Boundary Owner")
    fixture = Path(__file__).parent / "fixtures" / "packs" / "community-research"
    local_pack = tmp_path / "packs" / "community-research"
    shutil.copytree(fixture, local_pack)
    loaded = load_pack(local_pack)
    declared = loaded.manifest.model_copy(
        update={
            "declared_capability_ids": ("validator.pack.only",),
            "integrity_digest": f"sha256:{'0' * 64}",
        }
    )
    digest = calculate_pack_digest(declared, loaded.workflows)
    (local_pack / "manifest.yaml").write_text(
        "schema_version: '1.0'\n"
        "id: community-research-test\n"
        "version: 1.0.0\n"
        "schema_compatibility:\n"
        "  - forge-contracts-1\n"
        "provided_workflow_ids:\n"
        "  - community-research\n"
        "template_paths: []\n"
        "explanation_paths: []\n"
        "data_resource_paths: []\n"
        "declared_capability_ids:\n"
        "  - validator.pack.only\n"
        f"integrity_digest: {digest}\n",
        encoding="utf-8",
    )
    configured = initialized.configuration.model_copy(
        update={
            "packs": initialized.configuration.packs.model_copy(
                update={"local_paths": ("packs/community-research",)}
            )
        }
    )
    initialized.layout.configuration_file.write_bytes(render_configuration(configured))
    configuration = load_configuration(initialized.layout.configuration_file)
    packs = available_packs(initialized.layout, configuration)
    assert any(
        "validator.pack.only" in item.manifest.declared_capability_ids
        for item in packs
    )

    capabilities = {
        item.definition.id
        for item in list_capabilities(initialized.layout)
    }

    assert capabilities == {"agent.claude.execute", "agent.codex.execute"}
