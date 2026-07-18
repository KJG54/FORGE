"""Provider-neutral, mutation-free agent adapter contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class AdapterCompatibilityState(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


class AdapterInvocationMode(StrEnum):
    MANUAL_HANDOFF = "manual-handoff"
    LOCAL_PROCESS = "local-process"


class AdapterOperationState(StrEnum):
    NOT_APPLICABLE = "not-applicable"
    MANUAL_REQUIRED = "manual-required"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class AdapterAvailability:
    available: bool
    detail: str


@dataclass(frozen=True)
class AdapterCompatibility:
    state: AdapterCompatibilityState
    detail: str


@dataclass(frozen=True)
class AdapterInvocationRequest:
    step_id: str
    context_digest: str
    required_outputs: tuple[str, ...]
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdapterInvocationPlan:
    adapter_id: str
    adapter_version: str | None
    mode: AdapterInvocationMode
    step_id: str
    context_digest: str
    required_outputs: tuple[str, ...]
    constraints: tuple[str, ...]
    executable: str | None
    arguments: tuple[str, ...]
    working_directory: str | None
    output_directory: str | None
    result_manifest_contract: str
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class AdapterProcessHandle:
    adapter_id: str
    token: str
    process_id: int | None


@dataclass(frozen=True)
class AdapterProcessStart:
    state: AdapterOperationState
    detail: str
    handle: AdapterProcessHandle | None = None


@dataclass(frozen=True)
class AdapterOperationResult:
    state: AdapterOperationState
    detail: str


@dataclass(frozen=True)
class AdapterOutputCapture:
    state: AdapterOperationState
    paths: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class AdapterResultManifest:
    state: AdapterOperationState
    contract: str
    path: str | None
    detail: str


@dataclass(frozen=True)
class AdapterDiagnostic:
    adapter_id: str
    display_name: str
    availability: AdapterAvailability
    detected_version: str | None
    compatibility: AdapterCompatibility
    authentication_state: str
    supports_process_start: bool
    supports_cancellation: bool
    supports_output_capture: bool
    limitations: tuple[str, ...]


@runtime_checkable
class AgentAdapter(Protocol):
    """Neutral boundary implemented by manual and future installed-tool adapters."""

    @property
    def adapter_id(self) -> str: ...

    @property
    def display_name(self) -> str: ...

    def detect_availability(self) -> AdapterAvailability: ...

    def report_version(self) -> str | None: ...

    def assess_compatibility(self, version: str | None) -> AdapterCompatibility: ...

    def prepare_invocation(self, request: AdapterInvocationRequest) -> AdapterInvocationPlan: ...

    def start_process(self, plan: AdapterInvocationPlan) -> AdapterProcessStart: ...

    def cancel(self, handle: AdapterProcessHandle | None) -> AdapterOperationResult: ...

    def capture_output(self, handle: AdapterProcessHandle | None) -> AdapterOutputCapture: ...

    def produce_result_manifest(
        self, handle: AdapterProcessHandle | None
    ) -> AdapterResultManifest: ...

    def diagnostics(self) -> AdapterDiagnostic: ...
