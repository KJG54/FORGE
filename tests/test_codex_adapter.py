import hashlib
import sys
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from typer.testing import CliRunner

import forge.core.agent_adapters as adapter_core
from forge.adapters import (
    AdapterCompatibilityState,
    AdapterInvocationMode,
    AdapterInvocationRequest,
    AgentAdapter,
    CodexAgentAdapter,
)
from forge.cli.app import app
from forge.contracts.configuration import AgentConfiguration
from forge.core.agent_adapters import prepare_agent_handoff, select_agent_adapter
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative
from forge.errors import ConfigurationError
from forge.storage.configuration import render_configuration
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _fake_codex_command(
    tmp_path: Path,
    *,
    version_output: str = "codex-cli 1.2.3",
    help_output: str = (
        "--json --ephemeral --sandbox --ask-for-approval --ignore-user-config "
        "--ignore-rules --skip-git-repo-check"
    ),
    authenticated: bool = True,
) -> tuple[str, ...]:
    script = tmp_path / f"fake-codex-{len(tuple(tmp_path.glob('fake-codex-*.py')))}.py"
    script.write_text(
        "import sys\n"
        "arguments = sys.argv[1:]\n"
        "if arguments == ['--version']:\n"
        f"    print({version_output!r})\n"
        "    raise SystemExit(0)\n"
        "if arguments == ['exec', '--help']:\n"
        f"    print({help_output!r})\n"
        "    raise SystemExit(0)\n"
        "if arguments == ['login', 'status']:\n"
        f"    print({'authenticated' if authenticated else 'not logged in'!r})\n"
        f"    raise SystemExit({0 if authenticated else 1})\n"
        "raise SystemExit(2)\n",
        encoding="utf-8",
    )
    return (sys.executable, str(script))


def _initiative(tmp_path: Path) -> InitializationResult:
    repository = tmp_path / "repository"
    repository.mkdir()
    initialized = initialize_repository(repository, owner_display_name="Repository Owner")
    create_initiative(
        initialized.layout,
        objective="Produce bounded discovery outputs",
        declared_scope_summary="Objective and requirements only",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
    )
    return initialized


def _register_codex(
    monkeypatch: pytest.MonkeyPatch,
    adapter: CodexAgentAdapter,
) -> None:
    registry = cast("dict[str, AgentAdapter]", vars(adapter_core)["_ADAPTERS"])
    monkeypatch.setitem(registry, "codex", adapter)


def test_codex_adapter_detects_stable_features_and_persisted_auth(tmp_path: Path) -> None:
    adapter = CodexAgentAdapter(command=_fake_codex_command(tmp_path))
    diagnostic = adapter.diagnostics()

    assert isinstance(adapter, AgentAdapter)
    assert diagnostic.availability.available
    assert diagnostic.detected_version == "1.2.3"
    assert diagnostic.compatibility.state is AdapterCompatibilityState.COMPATIBLE
    assert diagnostic.authentication_state == "authenticated"
    assert diagnostic.supports_process_start
    assert diagnostic.supports_cancellation
    assert diagnostic.supports_output_capture


def test_codex_preparation_is_context_bound_and_isolated(
    tmp_path: Path,
) -> None:
    command = _fake_codex_command(tmp_path)
    adapter = CodexAgentAdapter(command=command)
    payload = '{"active_step":{"id":"discover"}}\n'
    digest = f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
    result_directory = tmp_path / "result"
    result_directory.mkdir()
    source_id = uuid4()

    plan = adapter.prepare_invocation(
        AdapterInvocationRequest(
            step_id="discover",
            context_digest=digest,
            required_outputs=("requirements",),
            constraints=("Do not modify governed state",),
            context_payload=payload,
            working_directory=str(tmp_path.resolve()),
            output_directory=str(result_directory.resolve()),
            source_run_id=str(source_id),
        )
    )

    assert plan.adapter_id == "codex"
    assert plan.adapter_version == "1.2.3"
    assert plan.mode is AdapterInvocationMode.LOCAL_PROCESS
    assert Path(plan.executable or "").resolve() == Path(sys.executable).resolve()
    assert plan.arguments == (
        command[1],
        "exec",
        "--json",
        "--ephemeral",
        "--sandbox",
        "workspace-write",
        "--ask-for-approval",
        "never",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-",
    )
    assert plan.standard_input is not None
    assert digest in plan.standard_input
    assert str(source_id) in plan.standard_input
    assert plan.standard_input.endswith(payload)
    assert plan.output_directory == str(result_directory.resolve())


def test_codex_diagnostics_fail_closed_for_missing_features_auth_and_binary(
    tmp_path: Path,
) -> None:
    unlabelled_version = CodexAgentAdapter(
        command=_fake_codex_command(tmp_path, version_output="launcher warning 1.2.3")
    ).diagnostics()
    assert unlabelled_version.availability.available
    assert unlabelled_version.detected_version is None
    assert unlabelled_version.compatibility.state is AdapterCompatibilityState.UNKNOWN
    assert unlabelled_version.authentication_state == "not-checked"

    incompatible = CodexAgentAdapter(
        command=_fake_codex_command(tmp_path, help_output="--json --sandbox")
    ).diagnostics()
    assert incompatible.availability.available
    assert incompatible.compatibility.state is AdapterCompatibilityState.INCOMPATIBLE
    assert incompatible.authentication_state == "not-checked"

    unauthenticated = CodexAgentAdapter(
        command=_fake_codex_command(tmp_path, authenticated=False)
    )
    diagnostic = unauthenticated.diagnostics()
    assert diagnostic.compatibility.state is AdapterCompatibilityState.COMPATIBLE
    assert diagnostic.authentication_state == "unauthenticated"
    with pytest.raises(ConfigurationError, match="not authenticated"):
        unauthenticated.prepare_invocation(
            AdapterInvocationRequest(
                step_id="discover",
                context_digest=f"sha256:{'0' * 64}",
                required_outputs=("requirements",),
                context_payload="{}",
                working_directory=str(tmp_path.resolve()),
            )
        )

    unavailable = CodexAgentAdapter(command=(str(tmp_path / "missing-codex"),)).diagnostics()
    assert not unavailable.availability.available
    assert unavailable.detected_version is None
    assert unavailable.compatibility.state is AdapterCompatibilityState.UNKNOWN
    assert unavailable.authentication_state == "not-checked"


def test_registered_codex_is_diagnosed_but_portable_handoff_stays_manual(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(tmp_path)
    adapter = CodexAgentAdapter(command=_fake_codex_command(tmp_path))
    _register_codex(monkeypatch, adapter)
    configured = initialized.configuration.model_copy(
        update={"agents": AgentConfiguration(preferred_adapter="codex")}
    )
    initialized.layout.configuration_file.write_bytes(render_configuration(configured))

    selected = select_agent_adapter(initialized.layout)
    assert selected.adapter.adapter_id == "codex"
    assert selected.fallback_reason is None
    assert selected.requested_diagnostic == selected.diagnostic
    prepared = prepare_agent_handoff(initialized.layout, step_id="discover")
    assert prepared.selection.requested_adapter_id == "codex"
    assert prepared.selection.adapter.adapter_id == "manual"
    assert "cannot create a portable handoff" in (prepared.selection.fallback_reason or "")
    assert prepared.handoff.json_path.is_file()

    doctor = runner.invoke(
        app,
        ["agent", "doctor", "--adapter", "codex", "-C", str(initialized.layout.root)],
    )
    assert doctor.exit_code == 0, doctor.stdout
    assert "Requested adapter: codex" in doctor.stdout
    assert "Selected adapter: codex" in doctor.stdout
    assert "Version: 1.2.3" in doctor.stdout
    assert "Authentication: authenticated" in doctor.stdout

    unauthenticated = CodexAgentAdapter(
        command=_fake_codex_command(tmp_path, authenticated=False)
    )
    _register_codex(monkeypatch, unauthenticated)
    fallback = runner.invoke(
        app,
        ["agent", "doctor", "--adapter", "codex", "-C", str(initialized.layout.root)],
    )
    assert fallback.exit_code == 0, fallback.stdout
    assert "Requested availability: available" in fallback.stdout
    assert "Requested compatibility: compatible" in fallback.stdout
    assert "Requested authentication: unauthenticated" in fallback.stdout
    assert "Fallback: Adapter 'codex' is not authenticated" in fallback.stdout
    assert "Selected adapter: manual" in fallback.stdout
