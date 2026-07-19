import sys
from pathlib import Path
from typing import cast

import pytest
from typer.testing import CliRunner

import forge.core.agent_adapters as adapter_core
from forge.adapters import AdapterOperationState, AgentAdapter, CodexAgentAdapter
from forge.cli.app import app
from forge.contracts.actors import ActorType
from forge.contracts.capabilities import CapabilityTrustState
from forge.contracts.state import RunState, StepState
from forge.core.agent_runs import execute_agent_run
from forge.core.authorization import owner_actor
from forge.core.capabilities import approve_capability, revoke_capability_approval
from forge.core.imports import apply_result_import
from forge.core.lifecycle import create_initiative, load_active_initiative
from forge.core.runs import show_run
from forge.core.verification import complete_step
from forge.errors import ConflictError
from forge.storage.journal import read_journal
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _fake_codex_command(tmp_path: Path, *, behavior: str = "success") -> tuple[str, ...]:
    script = tmp_path / f"fake-codex-run-{behavior}.py"
    script.write_text(
        "import json\n"
        "import os\n"
        "import re\n"
        "import sys\n"
        "import time\n"
        "from pathlib import Path\n"
        "from uuid import uuid4\n"
        f"behavior = {behavior!r}\n"
        "arguments = sys.argv[1:]\n"
        "if arguments == ['--version']:\n"
        "    print('codex-cli 1.2.3')\n"
        "    raise SystemExit(0)\n"
        "if arguments == ['exec', '--help']:\n"
        "    print('--json --ephemeral --sandbox --ask-for-approval "
        "--ignore-user-config --ignore-rules --skip-git-repo-check')\n"
        "    raise SystemExit(0)\n"
        "if arguments == ['login', 'status']:\n"
        "    print('authenticated')\n"
        "    raise SystemExit(0)\n"
        "if 'OPENAI_API_KEY' in os.environ:\n"
        "    raise SystemExit(9)\n"
        "prompt = sys.stdin.read()\n"
        "if behavior == 'timeout':\n"
        "    time.sleep(2)\n"
        "    raise SystemExit(0)\n"
        "match = re.search(r'source_run_or_handoff_id must be "
        "([0-9a-f-]{36})', prompt)\n"
        "if match is None:\n"
        "    raise SystemExit(8)\n"
        "source_id = str(uuid4()) if behavior == 'wrong-source' else match.group(1)\n"
        "result = Path.cwd() / 'result'\n"
        "(result / 'objective.md').write_text('# Objective\\nBounded work.\\n', "
        "encoding='utf-8')\n"
        "(result / 'requirements.md').write_text('# Requirements\\n- Safe.\\n', "
        "encoding='utf-8')\n"
        "manifest = {\n"
        "    'schema_version': '1.0',\n"
        "    'id': str(uuid4()),\n"
        "    'source_run_or_handoff_id': source_id,\n"
        "    'worker_claims': ['Returned requested files'],\n"
        "    'returned_files': [\n"
        "        {\n"
        "            'schema_version': '1.0',\n"
        "            'source_path': 'objective.md',\n"
        "            'proposed_target_path': 'objective.md',\n"
        "            'media_type': 'text/markdown',\n"
        "        },\n"
        "        {\n"
        "            'schema_version': '1.0',\n"
        "            'source_path': 'requirements.md',\n"
        "            'proposed_target_path': 'requirements.md',\n"
        "            'media_type': 'text/markdown',\n"
        "        },\n"
        "    ],\n"
        "    'declared_limitations': ['Untrusted fake provider'],\n"
        "    'tool_metadata': {'provider': 'fake-codex'},\n"
        "}\n"
        "(result / 'result.json').write_text(json.dumps(manifest), encoding='utf-8')\n"
        "print(json.dumps({'type': 'completed'}))\n",
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


def _approve_codex(
    initialized: InitializationResult,
    *,
    scope: CapabilityTrustState = CapabilityTrustState.APPROVED_ONCE,
):
    return approve_capability(
        initialized.layout,
        capability_id="agent.codex.execute",
        scope=scope,
        rationale="Allow bounded isolated test execution",
        actor=owner_actor(initialized.configuration.owner),
    ).approval


def test_agent_run_stages_untrusted_output_then_completes_as_recorded_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(tmp_path)
    _register_codex(
        monkeypatch,
        CodexAgentAdapter(command=_fake_codex_command(tmp_path)),
    )
    _approve_codex(initialized)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-provider")

    result = execute_agent_run(
        initialized.layout,
        step_id="discover",
        requested_adapter_id="codex",
        constraints=("Return only declared discovery files",),
        timeout_seconds=5,
    )

    assert result.state is AdapterOperationState.SUCCEEDED
    assert result.exit_code == 0
    assert result.staged_result is not None
    assert result.staged_result.result.source_run_or_handoff_id == result.run_id
    assert (result.run_directory / "stdout.jsonl").is_file()
    assert (result.run_directory / "stderr.log").is_file()
    assert (result.run_directory / "workspace" / "context.json").is_file()
    assert not (initialized.layout.root / "objective.md").exists()
    run = show_run(initialized.layout, result.run_id)
    assert run.status is RunState.SUCCEEDED
    assert run.record.worker.actor_type is ActorType.AGENT_ADAPTER
    assert load_active_initiative(initialized.layout).state.step_states[
        "discover"
    ] is StepState.IN_PROGRESS

    apply_result_import(
        initialized.layout,
        manifest_path=result.manifest_path or Path(),
        actor=owner_actor(initialized.configuration.owner),
        role_assignments={
            "objective.md": "objective-and-constraints",
            "requirements.md": "requirements",
        },
    )
    with pytest.raises(ConflictError, match="exactly match"):
        complete_step(
            initialized.layout,
            step_id="discover",
            assertion="Caller-invented adapter claim",
            actor=run.record.worker,
        )
    completed = runner.invoke(
        app,
        [
            "complete",
            "discover",
            "--assertion",
            "Returned requested files",
            "--run-id",
            str(result.run_id),
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert completed.exit_code == 0, completed.stdout
    assert "Claim actor: OpenAI Codex CLI" in completed.stdout
    assert load_active_initiative(initialized.layout).state.step_states[
        "discover"
    ] is StepState.AWAITING_VERIFICATION


def test_agent_run_cli_reports_staging_without_applying_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(tmp_path)
    _register_codex(
        monkeypatch,
        CodexAgentAdapter(command=_fake_codex_command(tmp_path)),
    )
    _approve_codex(initialized)

    invoked = runner.invoke(
        app,
        [
            "agent",
            "run",
            "discover",
            "--adapter",
            "codex",
            "--timeout",
            "5",
            "--idempotency-key",
            "fake-agent-run",
            "-C",
            str(initialized.layout.root),
        ],
    )

    assert invoked.exit_code == 0, invoked.stdout
    assert "Execution state: succeeded" in invoked.stdout
    assert "Review with forge import-result" in invoked.stdout
    assert not (initialized.layout.root / "objective.md").exists()
    assert len(load_active_initiative(initialized.layout).state.active_run_ids) == 1


@pytest.mark.parametrize("behavior", ["timeout", "wrong-source"])
def test_agent_run_failure_is_audited_and_releases_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    behavior: str,
) -> None:
    initialized = _initiative(tmp_path)
    _register_codex(
        monkeypatch,
        CodexAgentAdapter(command=_fake_codex_command(tmp_path, behavior=behavior)),
    )
    _approve_codex(initialized)

    result = execute_agent_run(
        initialized.layout,
        step_id="discover",
        requested_adapter_id="codex",
        timeout_seconds=0.1 if behavior == "timeout" else 5,
    )

    expected = (
        AdapterOperationState.CANCELLED
        if behavior == "timeout"
        else AdapterOperationState.FAILED
    )
    assert result.state is expected
    assert result.staged_result is None
    assert show_run(initialized.layout, result.run_id).status is RunState.CANCELLED
    assert load_active_initiative(initialized.layout).state.step_states[
        "discover"
    ] is StepState.READY
    event_types = [
        event.event_type
        for event in read_journal(initialized.layout.event_journal_file)
    ]
    assert event_types[-2:] == ["adapter-run-executed", "run-cancelled"]


def test_agent_run_is_disabled_without_approval_and_once_is_consumed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(tmp_path)
    _register_codex(
        monkeypatch,
        CodexAgentAdapter(command=_fake_codex_command(tmp_path, behavior="wrong-source")),
    )

    with pytest.raises(ConflictError, match="is disabled"):
        execute_agent_run(
            initialized.layout,
            step_id="discover",
            requested_adapter_id="codex",
            timeout_seconds=5,
        )

    _approve_codex(initialized)
    failed = execute_agent_run(
        initialized.layout,
        step_id="discover",
        requested_adapter_id="codex",
        timeout_seconds=5,
    )
    assert failed.state is AdapterOperationState.FAILED
    with pytest.raises(ConflictError, match="is disabled"):
        execute_agent_run(
            initialized.layout,
            step_id="discover",
            requested_adapter_id="codex",
            timeout_seconds=5,
        )


def test_revoked_capability_approval_prevents_future_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(tmp_path)
    _register_codex(
        monkeypatch,
        CodexAgentAdapter(command=_fake_codex_command(tmp_path)),
    )
    approval = _approve_codex(
        initialized,
        scope=CapabilityTrustState.APPROVED_FOR_VERSION,
    )
    revoke_capability_approval(
        initialized.layout,
        approval_id=approval.id,
        reason="Provider authority no longer required",
        actor=owner_actor(initialized.configuration.owner),
    )

    with pytest.raises(ConflictError, match="is disabled"):
        execute_agent_run(
            initialized.layout,
            step_id="discover",
            requested_adapter_id="codex",
            timeout_seconds=5,
        )


def test_capability_profile_drift_requires_new_owner_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(tmp_path)
    _register_codex(
        monkeypatch,
        CodexAgentAdapter(command=_fake_codex_command(tmp_path)),
    )
    _approve_codex(
        initialized,
        scope=CapabilityTrustState.APPROVED_FOR_PROJECT,
    )
    _register_codex(
        monkeypatch,
        CodexAgentAdapter(command=_fake_codex_command(tmp_path, behavior="wrong-source")),
    )

    with pytest.raises(ConflictError, match="is disabled"):
        execute_agent_run(
            initialized.layout,
            step_id="discover",
            requested_adapter_id="codex",
            timeout_seconds=5,
        )


def test_capability_cli_previews_and_applies_exact_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(tmp_path)
    command = _fake_codex_command(tmp_path)
    _register_codex(monkeypatch, CodexAgentAdapter(command=command))

    preview = runner.invoke(
        app,
        [
            "capability",
            "approve",
            "agent.codex.execute",
            "--rationale",
            "Bounded disposable execution",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert preview.exit_code == 0, preview.stdout
    assert f"Exact executable: {command[0]}" in preview.stdout
    assert "Environment access:" in preview.stdout
    assert "Side-effect class: repository_write" in preview.stdout
    assert "Preview only" in preview.stdout

    applied = runner.invoke(
        app,
        [
            "capability",
            "approve",
            "agent.codex.execute",
            "--rationale",
            "Bounded disposable execution",
            "--scope",
            "approved-for-version",
            "--apply",
            "--idempotency-key",
            "approve-fake-codex",
            "-C",
            str(initialized.layout.root),
        ],
    )
    assert applied.exit_code == 0, applied.stdout
    assert "Capability approval recorded:" in applied.stdout
