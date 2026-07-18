"""Core orchestration for neutral adapters without granting mutation services."""

from __future__ import annotations

from dataclasses import dataclass

from forge.adapters import (
    AdapterCompatibilityState,
    AdapterDiagnostic,
    AdapterInvocationPlan,
    AdapterInvocationRequest,
    AgentAdapter,
    ManualAgentAdapter,
)
from forge.core.agent_context import build_agent_context
from forge.core.handoffs import HandoffResult, create_handoff
from forge.errors import ConfigurationError, ConflictError, IntegrityError
from forge.storage.canonical import sha256_digest
from forge.storage.configuration import load_configuration
from forge.storage.records import render_record
from forge.storage.repository import RepositoryLayout


@dataclass(frozen=True)
class AdapterSelection:
    requested_adapter_id: str
    adapter: AgentAdapter
    diagnostic: AdapterDiagnostic
    fallback_reason: str | None


@dataclass(frozen=True)
class AdapterHandoffResult:
    selection: AdapterSelection
    plan: AdapterInvocationPlan
    handoff: HandoffResult


_MANUAL_ADAPTER = ManualAgentAdapter()
_ADAPTERS: dict[str, AgentAdapter] = {_MANUAL_ADAPTER.adapter_id: _MANUAL_ADAPTER}


def _manual_selection(requested: str, reason: str | None = None) -> AdapterSelection:
    diagnostic = _MANUAL_ADAPTER.diagnostics()
    if not diagnostic.availability.available:
        raise IntegrityError("Built-in manual adapter unexpectedly reported unavailable")
    if diagnostic.compatibility.state is not AdapterCompatibilityState.COMPATIBLE:
        raise IntegrityError("Built-in manual adapter unexpectedly reported incompatible")
    return AdapterSelection(requested, _MANUAL_ADAPTER, diagnostic, reason)


def select_agent_adapter(
    layout: RepositoryLayout,
    *,
    requested_adapter_id: str | None = None,
) -> AdapterSelection:
    """Select a usable adapter and explicitly degrade to manual handoff."""

    configuration = load_configuration(layout.configuration_file)
    configured = configuration.agents.preferred_adapter or "manual"
    candidate = requested_adapter_id if requested_adapter_id is not None else configured
    requested = candidate.strip().lower()
    if not requested:
        raise ConfigurationError("Requested adapter ID must not be empty")
    adapter = _ADAPTERS.get(requested)
    if adapter is None:
        return _manual_selection(
            requested,
            f"Adapter {requested!r} is not registered; using manual handoff",
        )
    diagnostic = adapter.diagnostics()
    if not diagnostic.availability.available:
        return _manual_selection(
            requested,
            f"Adapter {requested!r} is unavailable; using manual handoff",
        )
    if diagnostic.compatibility.state is not AdapterCompatibilityState.COMPATIBLE:
        return _manual_selection(
            requested,
            f"Adapter {requested!r} is not compatible; using manual handoff",
        )
    return AdapterSelection(requested, adapter, diagnostic, None)


def inspect_agent_adapter(
    layout: RepositoryLayout,
    *,
    requested_adapter_id: str | None = None,
) -> AdapterSelection:
    """Return read-only availability and compatibility information."""

    return select_agent_adapter(layout, requested_adapter_id=requested_adapter_id)


def prepare_agent_handoff(
    layout: RepositoryLayout,
    *,
    step_id: str,
    constraints: tuple[str, ...] = (),
    requested_adapter_id: str | None = None,
) -> AdapterHandoffResult:
    """Prepare a digest-bound adapter assignment and materialize the manual fallback bundle."""

    selection = select_agent_adapter(layout, requested_adapter_id=requested_adapter_id)
    context = build_agent_context(layout)
    if context.active_step.id != step_id:
        raise ConflictError(
            f"Adapter handoff step {step_id!r} is not the active step {context.active_step.id!r}"
        )
    plan = selection.adapter.prepare_invocation(
        AdapterInvocationRequest(
            step_id=step_id,
            context_digest=sha256_digest(render_record(context)),
            required_outputs=context.required_outputs,
            constraints=constraints,
        )
    )
    handoff = create_handoff(layout, step_id=step_id, constraints=plan.constraints)
    return AdapterHandoffResult(selection=selection, plan=plan, handoff=handoff)
