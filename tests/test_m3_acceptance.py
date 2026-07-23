from __future__ import annotations

import sys
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest

import forge.core.agent_adapters as adapter_core
from forge.adapters import (
    AdapterOperationState,
    AgentAdapter,
    ClaudeAgentAdapter,
    CodexAgentAdapter,
)
from forge.contracts.agents import AgentResult, ReturnedFile
from forge.contracts.capabilities import CapabilityTrustState
from forge.contracts.state import StepState
from forge.core.acceptance import record_acceptance
from forge.core.agent_adapters import prepare_agent_handoff
from forge.core.agent_runs import execute_agent_run
from forge.core.artifacts import list_artifacts
from forge.core.authorization import owner_actor
from forge.core.capabilities import approve_capability
from forge.core.imports import apply_result_import
from forge.core.lifecycle import begin_manual_run, create_initiative, load_active_initiative
from forge.core.runs import show_run
from forge.core.verification import complete_step
from forge.errors import AuthorizationError
from forge.storage.journal import read_journal
from forge.storage.records import render_record
from forge.storage.repository import InitializationResult, initialize_repository


def _new_initiative(path: Path) -> InitializationResult:
    path.mkdir()
    initialized = initialize_repository(path, owner_display_name="M3 Acceptance Owner")
    create_initiative(
        initialized.layout,
        objective="Prove replaceable worker boundaries",
        declared_scope_summary="The discovery step and its two declared outputs",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
    )
    return initialized


def _result_manifest(directory: Path, source_id: UUID, provider: str) -> Path:
    directory.mkdir()
    (directory / "objective.md").write_text(
        "# Objective\n\nBounded M3 acceptance work.\n",
        encoding="utf-8",
    )
    (directory / "requirements.md").write_text(
        "# Requirements\n\n- Preserve owner authority.\n",
        encoding="utf-8",
    )
    result = AgentResult(
        id=uuid4(),
        source_run_or_handoff_id=source_id,
        worker_claims=("Returned the two declared discovery outputs",),
        returned_files=(
            ReturnedFile(
                source_path="objective.md",
                proposed_target_path="objective.md",
                media_type="text/markdown",
            ),
            ReturnedFile(
                source_path="requirements.md",
                proposed_target_path="requirements.md",
                media_type="text/markdown",
            ),
        ),
        declared_limitations=(f"Untrusted {provider} acceptance fixture",),
        tool_metadata={"provider": provider},
    )
    manifest = directory / "result.json"
    manifest.write_bytes(render_record(result))
    return manifest


def _fake_provider_command(tmp_path: Path, provider: str) -> tuple[str, ...]:
    script = tmp_path / f"fake-{provider}-m3-acceptance.py"
    codex_help = (
        "--json --ephemeral --sandbox --ask-for-approval --ignore-user-config "
        "--ignore-rules --skip-git-repo-check"
    )
    claude_help = (
        "--print --input-format --output-format --permission-mode "
        "--no-session-persistence --bare --tools --strict-mcp-config --no-chrome"
    )
    script.write_text(
        "import json\n"
        "import re\n"
        "import sys\n"
        "from pathlib import Path\n"
        "from uuid import uuid4\n"
        f"provider = {provider!r}\n"
        "arguments = sys.argv[1:]\n"
        "if arguments == ['--version']:\n"
        "    print('codex-cli 1.2.3' if provider == 'codex' "
        "else 'claude-code v2.1.118')\n"
        "    raise SystemExit(0)\n"
        "if arguments == ['exec', '--help'] and provider == 'codex':\n"
        f"    print({codex_help!r})\n"
        "    raise SystemExit(0)\n"
        "if arguments == ['--help'] and provider == 'claude':\n"
        f"    print({claude_help!r})\n"
        "    raise SystemExit(0)\n"
        "if arguments in (['login', 'status'], ['auth', 'status']):\n"
        "    print('authenticated')\n"
        "    raise SystemExit(0)\n"
        "prompt = sys.stdin.read()\n"
        "match = re.search(r'source_run_or_handoff_id must be "
        "([0-9a-f-]{36})', prompt)\n"
        "if match is None:\n"
        "    raise SystemExit(8)\n"
        "result_directory = Path.cwd() / 'result'\n"
        "(result_directory / 'objective.md').write_text(\n"
        "    '# Objective\\n\\nBounded M3 acceptance work.\\n', encoding='utf-8'\n"
        ")\n"
        "(result_directory / 'requirements.md').write_text(\n"
        "    '# Requirements\\n\\n- Preserve owner authority.\\n', encoding='utf-8'\n"
        ")\n"
        "manifest = {\n"
        "    'schema_version': '1.0',\n"
        "    'id': str(uuid4()),\n"
        "    'source_run_or_handoff_id': match.group(1),\n"
        "    'worker_claims': ['Returned the two declared discovery outputs'],\n"
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
        "    'declared_limitations': [f'Untrusted {provider} acceptance fixture'],\n"
        "    'tool_metadata': {'provider': provider},\n"
        "}\n"
        "(result_directory / 'result.json').write_text(\n"
        "    json.dumps(manifest), encoding='utf-8'\n"
        ")\n",
        encoding="utf-8",
    )
    return (sys.executable, str(script))


def _artifact_boundary(initialized: InitializationResult) -> tuple[set[str], bool]:
    views = list_artifacts(initialized.layout)
    return (
        {item.artifact.role for item in views},
        all(item.current_revision.provenance.metadata == {"untrusted": True} for item in views),
    )


def _exercise_local_adapter(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
) -> tuple[set[str], bool, StepState]:
    initialized = _new_initiative(root / provider)
    command = _fake_provider_command(root, provider)
    adapter: AgentAdapter
    capability_id: str
    if provider == "codex":
        adapter = CodexAgentAdapter(command=command)
        capability_id = "agent.codex.execute"
    else:
        adapter = ClaudeAgentAdapter(command=command)
        capability_id = "agent.claude.execute"
    registry = cast("dict[str, AgentAdapter]", vars(adapter_core)["_ADAPTERS"])
    monkeypatch.setitem(registry, provider, adapter)
    approve_capability(
        initialized.layout,
        capability_id=capability_id,
        scope=CapabilityTrustState.APPROVED_ONCE,
        rationale=f"Exercise the exact {provider} M3 acceptance profile",
        actor=owner_actor(initialized.configuration.owner),
    )

    executed = execute_agent_run(
        initialized.layout,
        step_id="discover",
        requested_adapter_id=provider,
        constraints=("Return only the declared discovery outputs",),
        timeout_seconds=5,
    )
    assert executed.state is AdapterOperationState.SUCCEEDED
    assert executed.manifest_path is not None
    assert not (initialized.layout.root / "objective.md").exists()
    apply_result_import(
        initialized.layout,
        manifest_path=executed.manifest_path,
        actor=owner_actor(initialized.configuration.owner),
        role_assignments={
            "objective.md": "objective-and-constraints",
            "requirements.md": "requirements",
        },
    )
    run = show_run(initialized.layout, executed.run_id)
    complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Returned the two declared discovery outputs",
        actor=run.record.worker,
    )
    with pytest.raises(AuthorizationError, match="Only configured owner"):
        record_acceptance(
            initialized.layout,
            step_id="discover",
            accepted_scope="Agent attempted to accept its own output",
            actor=run.record.worker,
        )
    events = read_journal(initialized.layout.event_journal_file)
    assert [item.event_type for item in events][-4:] == [
        "adapter-run-executed",
        "result-imported",
        "claim-recorded",
        "step-transitioned",
    ]
    state = load_active_initiative(initialized.layout).state.step_states["discover"]
    roles, untrusted = _artifact_boundary(initialized)
    return roles, untrusted, state


def _exercise_manual_handoff(root: Path) -> tuple[set[str], bool, StepState]:
    initialized = _new_initiative(root / "manual")
    before = initialized.layout.event_journal_file.read_bytes()
    prepared = prepare_agent_handoff(
        initialized.layout,
        step_id="discover",
        constraints=("Return only the declared discovery outputs",),
    )
    assert prepared.selection.adapter.adapter_id == "manual"
    assert initialized.layout.event_journal_file.read_bytes() == before
    manifest = _result_manifest(
        root / "manual-result",
        prepared.handoff.handoff.id,
        "manual",
    )
    actor = owner_actor(initialized.configuration.owner)
    apply_result_import(
        initialized.layout,
        manifest_path=manifest,
        actor=actor,
        role_assignments={
            "objective.md": "objective-and-constraints",
            "requirements.md": "requirements",
        },
    )
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Returned the two declared discovery outputs",
        actor=actor,
    )
    state = load_active_initiative(initialized.layout).state.step_states["discover"]
    roles, untrusted = _artifact_boundary(initialized)
    return roles, untrusted, state


def test_manual_codex_and_claude_share_lifecycle_and_import_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = (
        {"objective-and-constraints", "requirements"},
        True,
        StepState.AWAITING_VERIFICATION,
    )

    assert _exercise_manual_handoff(tmp_path) == expected
    assert _exercise_local_adapter(tmp_path, monkeypatch, "codex") == expected
    assert _exercise_local_adapter(tmp_path, monkeypatch, "claude") == expected
