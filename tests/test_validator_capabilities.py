from __future__ import annotations

import shutil
import sys
from pathlib import Path
from uuid import UUID

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
from forge.contracts.state import StepState
from forge.contracts.verification import CheckExecutionStatus, CheckOutcome
from forge.core.acceptance import list_acceptances
from forge.core.artifacts import add_artifact
from forge.core.authorization import owner_actor
from forge.core.capabilities import (
    approve_capability,
    inspect_capability,
    list_capabilities,
    list_capability_approvals,
    revoke_capability_approval,
)
from forge.core.lifecycle import (
    begin_manual_run,
    create_initiative,
    load_active_initiative,
)
from forge.core.validators import (
    MAX_VALIDATOR_CAPTURE_BYTES,
    execute_validator_check,
)
from forge.core.verification import complete_step, list_checks, list_evidence
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
    timeout_seconds: int = 300,
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
        timeout_seconds=timeout_seconds,
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


def _fake_validator(tmp_path: Path) -> Path:
    path = tmp_path / "fake_validator.py"
    path.write_text(
        "import json\n"
        "import os\n"
        "import sys\n"
        "import time\n"
        "mode = sys.argv[1]\n"
        "if mode == 'success':\n"
        "    print('validator succeeded')\n"
        "    print('diagnostic only', file=sys.stderr)\n"
        "elif mode == 'failure':\n"
        "    print('validator failed', file=sys.stderr)\n"
        "    raise SystemExit(7)\n"
        "elif mode == 'timeout':\n"
        "    time.sleep(5)\n"
        "elif mode == 'overflow':\n"
        f"    sys.stdout.buffer.write(b'x' * ({MAX_VALIDATOR_CAPTURE_BYTES} + 65536))\n"
        "    sys.stdout.buffer.flush()\n"
        "elif mode == 'environment':\n"
        "    print(json.dumps({\n"
        "        'allowed': os.environ.get('FORGE_TEST_ALLOWED'),\n"
        "        'credential_present': 'OPENAI_API_KEY' in os.environ,\n"
        "        'home_present': 'HOME' in os.environ,\n"
        "    }, sort_keys=True))\n",
        encoding="utf-8",
    )
    return path


def _awaiting_verification(
    tmp_path: Path,
    validator: LocalValidatorDefinition,
) -> tuple[InitializationResult, tuple[UUID, ...]]:
    initialized = _initiative_with_validator(tmp_path, validator)
    actor = owner_actor(initialized.configuration.owner)
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    revisions: list[UUID] = []
    for path, role in (
        ("objective.md", "objective-and-constraints"),
        ("requirements.md", "requirements"),
    ):
        (tmp_path / path).write_text(f"# {role}\n", encoding="utf-8")
        revisions.append(
            add_artifact(
                initialized.layout,
                path=path,
                role=role,
                title=role,
                actor=actor,
                media_type="text/markdown",
            ).revision.id
        )
    complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Declared discovery outputs were produced",
        actor=actor,
    )
    return initialized, tuple(revisions)


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


def test_approved_validator_records_a_bound_check_without_advancing_lifecycle(
    tmp_path: Path,
) -> None:
    fake = _fake_validator(tmp_path)
    initialized, revision_ids = _awaiting_verification(
        tmp_path,
        _validator(arguments=(str(fake), "success")),
    )
    approval = approve_capability(
        initialized.layout,
        capability_id="validator.project.tests",
        scope=CapabilityTrustState.APPROVED_ONCE,
        rationale="Execute this exact deterministic success profile once",
        actor=owner_actor(initialized.configuration.owner),
    )

    result = execute_validator_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        capability_id="validator.project.tests",
    )

    assert result.check.outcome is CheckOutcome.PASSED
    assert result.check.execution_status is CheckExecutionStatus.COMPLETED
    assert result.check.exit_status == 0
    assert set(result.check.target_artifact_revision_ids) == set(revision_ids)
    assert result.check.capability_id == "validator.project.tests"
    assert result.check.capability_approval_id == approval.approval.id
    assert result.check.run_id == result.run.id
    assert result.check.invocation_digest == result.run.input_context_digest
    assert result.check.stdout_byte_count is not None
    assert result.check.stderr_byte_count is not None
    assert result.check.stdout_byte_count > 0
    assert result.check.stderr_byte_count > 0
    assert result.check.stdout_capture_path is not None
    assert "validator succeeded" in (
        initialized.layout.root / result.check.stdout_capture_path
    ).read_text(encoding="utf-8")
    assert list_checks(initialized.layout) == (result.check,)
    assert list_evidence(initialized.layout) == ()
    assert list_acceptances(initialized.layout) == ()
    restarted = load_active_initiative(initialized.layout)
    assert restarted.state.step_states["discover"] is StepState.AWAITING_VERIFICATION
    assert restarted.state.active_run_ids == ()
    view = list_capability_approvals(
        initialized.layout,
        capability_id="validator.project.tests",
    )[0]
    assert view.consumed
    assert not view.active
    with pytest.raises(ConflictError, match="disabled"):
        execute_validator_check(
            initialized.layout,
            step_id="discover",
            check_id="outputs-present",
            check_version="1",
            capability_id="validator.project.tests",
        )
    assert list_checks(initialized.layout) == (result.check,)


@pytest.mark.parametrize(
    ("mode", "timeout_seconds", "expected_status", "expected_outcome", "exit_status"),
    [
        ("failure", 10, CheckExecutionStatus.COMPLETED, CheckOutcome.FAILED, 7),
        ("timeout", 1, CheckExecutionStatus.TIMED_OUT, CheckOutcome.ERROR, None),
        (
            "overflow",
            10,
            CheckExecutionStatus.OUTPUT_LIMIT_EXCEEDED,
            CheckOutcome.ERROR,
            None,
        ),
    ],
)
def test_validator_preserves_failure_timeout_and_output_overflow_attempts(
    tmp_path: Path,
    mode: str,
    timeout_seconds: int,
    expected_status: CheckExecutionStatus,
    expected_outcome: CheckOutcome,
    exit_status: int | None,
) -> None:
    fake = _fake_validator(tmp_path)
    initialized, _ = _awaiting_verification(
        tmp_path,
        _validator(
            arguments=(str(fake), mode),
            timeout_seconds=timeout_seconds,
        ),
    )
    approve_capability(
        initialized.layout,
        capability_id="validator.project.tests",
        scope=CapabilityTrustState.APPROVED_FOR_PROJECT,
        rationale=f"Exercise the deterministic {mode} validator profile",
        actor=owner_actor(initialized.configuration.owner),
    )

    result = execute_validator_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        capability_id="validator.project.tests",
    )

    assert result.check.execution_status is expected_status
    assert result.check.outcome is expected_outcome
    if exit_status is not None:
        assert result.check.exit_status == exit_status
    assert result.check.stdout_byte_count is not None
    assert result.check.stderr_byte_count is not None
    assert (
        result.check.stdout_byte_count + result.check.stderr_byte_count
        <= MAX_VALIDATOR_CAPTURE_BYTES
    )
    assert load_active_initiative(initialized.layout).state.step_states[
        "discover"
    ] is StepState.AWAITING_VERIFICATION
    assert list_evidence(initialized.layout) == ()


def test_validator_environment_is_allowlisted_without_inherited_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FORGE_TEST_ALLOWED", "visible")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-inherited")
    monkeypatch.setenv("HOME", str(tmp_path / "sensitive-home"))
    fake = _fake_validator(tmp_path)
    initialized, _ = _awaiting_verification(
        tmp_path,
        _validator(
            arguments=(str(fake), "environment"),
            environment_access=("FORGE_TEST_ALLOWED",),
        ),
    )
    approve_capability(
        initialized.layout,
        capability_id="validator.project.tests",
        scope=CapabilityTrustState.APPROVED_FOR_PROJECT,
        rationale="Allow only the explicit non-credential test variable",
        actor=owner_actor(initialized.configuration.owner),
    )

    result = execute_validator_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        capability_id="validator.project.tests",
    )

    assert result.check.stdout_capture_path is not None
    captured = (
        initialized.layout.root / result.check.stdout_capture_path
    ).read_text(encoding="utf-8")
    assert '"allowed": "visible"' in captured
    assert '"credential_present": false' in captured
    assert '"home_present": false' in captured
    assert "must-not-be-inherited" not in captured
    assert "must-not-be-inherited" not in result.check.model_dump_json()

    unsafe = _initiative_with_validator(
        tmp_path / "unsafe-name",
        _validator(environment_access=("OPENAI_API_KEY",)),
    )
    inspection = inspect_capability(unsafe.layout, "validator.project.tests")
    assert not inspection.compatible
    assert "credential-bearing environment names" in inspection.availability_detail
    with pytest.raises(ConflictError, match="cannot be approved"):
        approve_capability(
            unsafe.layout,
            capability_id="validator.project.tests",
            scope=CapabilityTrustState.APPROVED_ONCE,
            rationale="Credential inheritance must remain unavailable",
            actor=owner_actor(unsafe.configuration.owner),
        )


def test_validator_execution_refuses_missing_revoked_and_drifted_approval(
    tmp_path: Path,
) -> None:
    fake = _fake_validator(tmp_path)
    initialized, _ = _awaiting_verification(
        tmp_path,
        _validator(arguments=(str(fake), "success")),
    )
    with pytest.raises(ConflictError, match="disabled"):
        execute_validator_check(
            initialized.layout,
            step_id="discover",
            check_id="outputs-present",
            check_version="1",
            capability_id="validator.project.tests",
        )
    assert not initialized.layout.validator_run_directory.exists()

    approved = approve_capability(
        initialized.layout,
        capability_id="validator.project.tests",
        scope=CapabilityTrustState.APPROVED_FOR_PROJECT,
        rationale="Approve before testing immutable revocation",
        actor=owner_actor(initialized.configuration.owner),
    )
    revoke_capability_approval(
        initialized.layout,
        approval_id=approved.approval.id,
        reason="Do not execute this profile",
        actor=owner_actor(initialized.configuration.owner),
    )
    with pytest.raises(ConflictError, match="disabled"):
        execute_validator_check(
            initialized.layout,
            step_id="discover",
            check_id="outputs-present",
            check_version="1",
            capability_id="validator.project.tests",
        )

    replacement = approve_capability(
        initialized.layout,
        capability_id="validator.project.tests",
        scope=CapabilityTrustState.APPROVED_FOR_PROJECT,
        rationale="Approve before testing exact profile drift",
        actor=owner_actor(initialized.configuration.owner),
    )
    configuration = load_configuration(initialized.layout.configuration_file)
    drifted = configuration.model_copy(
        update={
            "capabilities": configuration.capabilities.model_copy(
                update={
                    "local_validators": (
                        _validator(arguments=(str(fake), "failure")),
                    )
                }
            )
        }
    )
    initialized.layout.configuration_file.write_bytes(render_configuration(drifted))
    with pytest.raises(ConflictError, match="disabled"):
        execute_validator_check(
            initialized.layout,
            step_id="discover",
            check_id="outputs-present",
            check_version="1",
            capability_id="validator.project.tests",
        )
    views = list_capability_approvals(
        initialized.layout,
        capability_id="validator.project.tests",
    )
    replacement_view = next(
        item for item in views if item.approval.id == replacement.approval.id
    )
    assert not replacement_view.applicable
    assert not initialized.layout.validator_run_directory.exists()


def test_validator_cli_run_records_result_without_rendering_raw_output(
    tmp_path: Path,
) -> None:
    fake = _fake_validator(tmp_path)
    initialized, _ = _awaiting_verification(
        tmp_path,
        _validator(arguments=(str(fake), "success")),
    )
    approve_capability(
        initialized.layout,
        capability_id="validator.project.tests",
        scope=CapabilityTrustState.APPROVED_ONCE,
        rationale="Exercise the public validator execution command",
        actor=owner_actor(initialized.configuration.owner),
    )

    executed = runner.invoke(
        app,
        [
            "check",
            "run",
            "discover",
            "outputs-present",
            "--validator",
            "validator.project.tests",
            "-C",
            str(initialized.layout.root),
            "--idempotency-key",
            "validator-cli-success",
        ],
    )

    assert executed.exit_code == 0, executed.stdout
    assert "Execution status: completed" in executed.stdout
    assert "Recorded check result" in executed.stdout
    assert "validator succeeded" not in executed.stdout
    assert "does not create evidence" in executed.stdout
    checks = list_checks(initialized.layout)
    assert len(checks) == 1
    shown = runner.invoke(
        app,
        [
            "check",
            "show",
            str(checks[0].id),
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert shown.exit_code == 0, shown.stdout
    assert f"Validator run: {checks[0].run_id}" in shown.stdout
    assert "validator succeeded" not in shown.stdout
