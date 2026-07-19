"""Governed synchronous adapter execution in disposable local workspaces."""

from __future__ import annotations

import json
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from forge.adapters import AdapterInvocationRequest, AdapterOperationState, AdapterProcessHandle
from forge.contracts.actors import Actor, ActorType
from forge.contracts.agents import AgentResult, CanonicalAgentContext
from forge.contracts.base import utc_now
from forge.contracts.capabilities import SideEffectClass
from forge.contracts.events import AuditEvent
from forge.core.agent_adapters import AdapterSelection, select_agent_adapter
from forge.core.agent_context import build_agent_context
from forge.core.lifecycle import begin_manual_run, load_active_initiative
from forge.core.runs import cancel_run
from forge.core.transitions import ADAPTER_RUN_EXECUTED
from forge.errors import (
    ConfigurationError,
    ConflictError,
    ForgeError,
    IntegrityError,
    SecurityError,
)
from forge.security.imports import StagedResult, stage_result
from forge.storage.atomic import atomic_write_bytes
from forge.storage.canonical import sha256_digest
from forge.storage.configuration import load_configuration
from forge.storage.records import render_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class AgentExecutionResult:
    selection: AdapterSelection
    run_id: UUID
    state: AdapterOperationState
    exit_code: int | None
    run_directory: Path
    manifest_path: Path | None
    staged_result: StagedResult | None
    detail: str
    event: AuditEvent


def _adapter_actor(layout: RepositoryLayout, selection: AdapterSelection) -> Actor:
    configuration = load_configuration(layout.configuration_file)
    adapter = selection.adapter
    version = selection.diagnostic.detected_version or "unknown"
    return Actor(
        id=uuid5(
            NAMESPACE_URL,
            f"forge:{configuration.project_id}:agent-adapter:{adapter.adapter_id}:{version}",
        ),
        actor_type=ActorType.AGENT_ADAPTER,
        display_label=selection.diagnostic.display_name,
        tool_reference=f"{adapter.adapter_id}@{version}",
    )


def _safe_directory(path: Path) -> None:
    if path.is_symlink():
        raise SecurityError(f"Adapter workspace path is a symbolic link: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Adapter workspace path is not a directory: {path}")
        return
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(
            f"Cannot create adapter workspace directory {path}: {error}"
        ) from error


def _materialize_workspace(
    layout: RepositoryLayout,
    *,
    run_id: UUID,
    context: CanonicalAgentContext,
    context_bytes: bytes,
    context_digest: str,
) -> tuple[Path, Path]:
    run_directory = layout.run_directory / str(run_id)
    workspace = run_directory / "workspace"
    inputs = workspace / "inputs"
    result = workspace / "result"
    for path in (run_directory, workspace, inputs, result):
        _safe_directory(path)
    context_path = workspace / "context.json"
    if context_path.exists() and context_path.read_bytes() != context_bytes:
        raise IntegrityError(f"Adapter run {run_id} has a different existing context")
    atomic_write_bytes(context_path, context_bytes)
    schema = json.dumps(
        AgentResult.model_json_schema(), ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    atomic_write_bytes(workspace / "agent-result.schema.json", schema)
    for selected in context.active_step.required_inputs:
        source = layout.root / selected.path
        if source.is_symlink() or not source.is_file():
            raise SecurityError(f"Selected adapter input is missing or unsafe: {selected.path}")
        content = source.read_bytes()
        if sha256_digest(content) != selected.content_digest:
            raise IntegrityError(
                f"Selected adapter input changed before execution: {selected.path}"
            )
        destination = inputs / selected.path
        cursor = inputs
        for part in Path(selected.path).parts[:-1]:
            cursor /= part
            _safe_directory(cursor)
        atomic_write_bytes(destination, content)
    metadata = json.dumps(
        {
            "context_digest": context_digest,
            "input_prefix": "inputs/",
            "result_directory": "result/",
            "run_id": str(run_id),
        },
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    atomic_write_bytes(workspace / "run.json", metadata)
    return run_directory, result


def execute_agent_run(
    layout: RepositoryLayout,
    *,
    step_id: str,
    requested_adapter_id: str,
    constraints: tuple[str, ...] = (),
    timeout_seconds: float = 300.0,
) -> AgentExecutionResult:
    """Run one compatible provider in an isolated local workspace and stage its result."""

    if timeout_seconds <= 0 or timeout_seconds > 3600:
        raise ConfigurationError(
            "Adapter execution timeout must be greater than 0 and at most 3600"
        )
    selection = select_agent_adapter(layout, requested_adapter_id=requested_adapter_id)
    if selection.adapter.adapter_id == "manual":
        reason = selection.fallback_reason or "manual adapter does not start a process"
        raise ConflictError(f"{reason}; use 'forge handoff' instead")
    context = build_agent_context(layout)
    if context.active_step.id != step_id:
        raise ConflictError(
            f"Adapter run step {step_id!r} is not the active step {context.active_step.id!r}"
        )
    context_bytes = render_record(context)
    context_digest = sha256_digest(context_bytes)
    actor = _adapter_actor(layout, selection)
    begun = begin_manual_run(
        layout,
        step_id=step_id,
        actor=actor,
        side_effect_class=SideEffectClass.REPOSITORY_WRITE,
        adapter_reference=selection.adapter.adapter_id,
        input_context_digest=context_digest,
    )
    run_id = begun.run.id
    run_directory = layout.run_directory / str(run_id)
    manifest_path: Path | None = None
    staged: StagedResult | None = None
    state = AdapterOperationState.FAILED
    exit_code: int | None = None
    detail = "Adapter execution did not start"
    handle: AdapterProcessHandle | None = None
    try:
        run_directory, result_directory = _materialize_workspace(
            layout,
            run_id=run_id,
            context=context,
            context_bytes=context_bytes,
            context_digest=context_digest,
        )
        plan = selection.adapter.prepare_invocation(
            AdapterInvocationRequest(
                step_id=step_id,
                context_digest=context_digest,
                required_outputs=context.required_outputs,
                constraints=constraints,
                context_payload=context_bytes.decode("utf-8"),
                working_directory=str(result_directory.parent),
                output_directory=str(result_directory),
                source_run_id=str(run_id),
                timeout_seconds=timeout_seconds,
            )
        )
        started = selection.adapter.start_process(plan)
        if started.state is not AdapterOperationState.SUCCEEDED or started.handle is None:
            raise IntegrityError(
                f"Adapter {selection.adapter.adapter_id} did not start successfully: "
                f"{started.detail}"
            )
        handle = started.handle
        capture = selection.adapter.capture_output(handle)
        manifest = selection.adapter.produce_result_manifest(handle)
        manifest_path = Path(manifest.path) if manifest.path is not None else None
        state = capture.state
        exit_code = capture.exit_code
        detail = capture.detail
        if (
            state is AdapterOperationState.SUCCEEDED
            and manifest.state is AdapterOperationState.SUCCEEDED
            and manifest_path is not None
        ):
            staged = stage_result(layout, manifest_path, expected_source_id=run_id)
        elif state is AdapterOperationState.SUCCEEDED:
            state = AdapterOperationState.FAILED
            detail = manifest.detail
        elif state not in {AdapterOperationState.FAILED, AdapterOperationState.CANCELLED}:
            state = AdapterOperationState.FAILED
            detail = f"Adapter returned unsupported capture state: {capture.state.value}"
    except ForgeError as error:
        if handle is not None:
            with suppress(ForgeError):
                selection.adapter.cancel(handle)
        state = AdapterOperationState.FAILED
        detail = f"Provider execution or staged validation failed: {error}"
    active = load_active_initiative(layout)
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=active.state.journal_head_sequence + 1,
        timestamp=utc_now(),
        event_type=ADAPTER_RUN_EXECUTED,
        actor=actor,
        run_id=run_id,
        authorization_basis="approved adapter executed in a disposable isolated workspace",
        affected_record_ids=(run_id,),
        affected_digests=(context_digest,),
        metadata={
            "adapter_id": selection.adapter.adapter_id,
            "exit_code": exit_code,
            "state": state.value,
            "step_id": step_id,
            "staged_result_id": str(staged.result.id) if staged is not None else None,
        },
    )
    append_event_and_update_snapshot(
        layout.event_journal_file, layout.state_file, event, active.reducer
    )
    if state is not AdapterOperationState.SUCCEEDED:
        cancel_run(
            layout,
            run_id=run_id,
            reason=f"Adapter execution did not succeed: {detail}",
            actor=actor,
        )
    return AgentExecutionResult(
        selection,
        run_id,
        state,
        exit_code,
        run_directory,
        manifest_path,
        staged,
        detail,
        event,
    )
