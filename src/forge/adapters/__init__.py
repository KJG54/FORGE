"""Public provider-neutral adapter boundary and built-in implementations."""

from forge.adapters.base import (
    AdapterAvailability,
    AdapterCompatibility,
    AdapterCompatibilityState,
    AdapterDiagnostic,
    AdapterInvocationMode,
    AdapterInvocationPlan,
    AdapterInvocationRequest,
    AdapterOperationResult,
    AdapterOperationState,
    AdapterOutputCapture,
    AdapterProcessHandle,
    AdapterProcessStart,
    AdapterResultManifest,
    AgentAdapter,
)
from forge.adapters.codex import CodexAgentAdapter
from forge.adapters.manual import ManualAgentAdapter

__all__ = [
    "AdapterAvailability",
    "AdapterCompatibility",
    "AdapterCompatibilityState",
    "AdapterDiagnostic",
    "AdapterInvocationMode",
    "AdapterInvocationPlan",
    "AdapterInvocationRequest",
    "AdapterOperationResult",
    "AdapterOperationState",
    "AdapterOutputCapture",
    "AdapterProcessHandle",
    "AdapterProcessStart",
    "AdapterResultManifest",
    "AgentAdapter",
    "CodexAgentAdapter",
    "ManualAgentAdapter",
]
