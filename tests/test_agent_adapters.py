from pathlib import Path

from typer.testing import CliRunner

from forge import __version__
from forge.adapters import (
    AdapterCompatibilityState,
    AdapterInvocationMode,
    AdapterInvocationRequest,
    AdapterOperationState,
    AgentAdapter,
    ManualAgentAdapter,
)
from forge.cli.app import app
from forge.core.agent_adapters import (
    inspect_agent_adapter,
    prepare_agent_handoff,
    select_agent_adapter,
)
from forge.core.agent_context import build_agent_context
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative
from forge.storage.canonical import sha256_digest
from forge.storage.configuration import render_configuration
from forge.storage.records import render_record
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> InitializationResult:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    create_initiative(
        initialized.layout,
        objective="Produce bounded discovery outputs",
        declared_scope_summary="Objective and requirements only",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
    )
    return initialized


def test_manual_adapter_fulfils_the_neutral_contract_without_process_execution() -> None:
    adapter = ManualAgentAdapter()
    assert isinstance(adapter, AgentAdapter)
    diagnostic = adapter.diagnostics()
    assert diagnostic.availability.available
    assert diagnostic.detected_version == __version__
    assert diagnostic.compatibility.state is AdapterCompatibilityState.COMPATIBLE
    assert diagnostic.authentication_state == "not-required"
    assert not diagnostic.supports_process_start
    assert not diagnostic.supports_cancellation
    assert not diagnostic.supports_output_capture

    plan = adapter.prepare_invocation(
        AdapterInvocationRequest(
            step_id="discover",
            context_digest=f"sha256:{'a' * 64}",
            required_outputs=("requirements",),
            constraints=("Stay in scope",),
        )
    )
    assert plan.mode is AdapterInvocationMode.MANUAL_HANDOFF
    assert plan.executable is None
    assert plan.arguments == ()
    assert plan.working_directory is None
    assert plan.output_directory is None
    assert plan.result_manifest_contract == "agent-result"
    assert adapter.start_process(plan).state is AdapterOperationState.NOT_APPLICABLE

    assert adapter.cancel(None).state is AdapterOperationState.NOT_APPLICABLE
    assert adapter.capture_output(None).state is AdapterOperationState.NOT_APPLICABLE
    manifest = adapter.produce_result_manifest(None)
    assert manifest.state is AdapterOperationState.MANUAL_REQUIRED
    assert manifest.contract == "agent-result"
    assert manifest.path is None


def test_manual_adapter_handoff_is_context_bound_and_non_governing(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    before = initialized.layout.event_journal_file.read_bytes()
    context = build_agent_context(initialized.layout)
    expected_digest = sha256_digest(render_record(context))

    result = prepare_agent_handoff(
        initialized.layout,
        step_id="discover",
        constraints=("Do not modify unrelated files",),
    )

    assert result.selection.adapter.adapter_id == "manual"
    assert result.selection.fallback_reason is None
    assert result.plan.context_digest == expected_digest
    assert result.plan.required_outputs == context.required_outputs
    assert result.handoff.handoff.constraints == ("Do not modify unrelated files",)
    assert result.handoff.json_path.is_file()
    assert initialized.layout.event_journal_file.read_bytes() == before
    assert not initialized.layout.current_agent_context_json_file.exists()
    assert not initialized.layout.current_agent_context_markdown_file.exists()


def test_missing_preferred_adapter_degrades_explicitly_to_manual(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    configured = initialized.configuration.model_copy(
        update={
            "agents": initialized.configuration.agents.model_copy(
                update={"preferred_adapter": "claude"}
            )
        }
    )
    initialized.layout.configuration_file.write_bytes(render_configuration(configured))

    selected = select_agent_adapter(initialized.layout)
    assert selected.requested_adapter_id == "claude"
    assert selected.adapter.adapter_id == "manual"
    assert selected.fallback_reason == "Adapter 'claude' is not registered; using manual handoff"
    inspection = inspect_agent_adapter(initialized.layout)
    assert inspection.diagnostic.adapter_id == "manual"
    prepared = prepare_agent_handoff(initialized.layout, step_id="discover")
    assert prepared.selection.requested_adapter_id == "claude"
    assert prepared.selection.adapter.adapter_id == "manual"
    assert prepared.selection.fallback_reason is not None
    assert prepared.handoff.json_path.is_file()


def test_agent_doctor_and_handoff_cli_expose_manual_selection(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    before = initialized.layout.event_journal_file.read_bytes()

    doctor = runner.invoke(
        app,
        ["agent", "doctor", "--adapter", "claude", "-C", str(initialized.layout.root)],
    )
    assert doctor.exit_code == 0, doctor.stdout
    assert "Requested adapter: claude" in doctor.stdout
    assert "Selected adapter: manual" in doctor.stdout
    assert "Fallback: Adapter 'claude' is not registered" in doctor.stdout
    assert "Process start: unsupported" in doctor.stdout
    assert initialized.layout.event_journal_file.read_bytes() == before

    handoff = runner.invoke(
        app,
        ["handoff", "discover", "-C", str(initialized.layout.root)],
    )
    assert handoff.exit_code == 0, handoff.stdout
    assert "Adapter: manual" in handoff.stdout
    assert "Context digest:" in handoff.stdout
    assert "Created handoff" in handoff.stdout
