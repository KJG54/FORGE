"""Always-available manual handoff adapter baseline."""

from __future__ import annotations

import re

from forge import __version__
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
)
from forge.errors import ConfigurationError

_SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_LIMITATIONS = (
    "FORGE prepares files but does not start or supervise a worker process",
    "A person must transfer the handoff to the worker and return an AgentResult manifest",
    "Returned files and claims remain untrusted until staged import succeeds",
)


class ManualAgentAdapter:
    """Represent the portable manual-file workflow through the common adapter boundary."""

    @property
    def adapter_id(self) -> str:
        return "manual"

    @property
    def display_name(self) -> str:
        return "Manual file handoff"

    def detect_availability(self) -> AdapterAvailability:
        return AdapterAvailability(
            available=True,
            detail="Built into FORGE; no external executable is required",
        )

    def report_version(self) -> str:
        return __version__

    def assess_compatibility(self, version: str | None) -> AdapterCompatibility:
        if version == __version__:
            return AdapterCompatibility(
                state=AdapterCompatibilityState.COMPATIBLE,
                detail=f"Built-in adapter matches FORGE {__version__}",
            )
        return AdapterCompatibility(
            state=AdapterCompatibilityState.INCOMPATIBLE,
            detail="Built-in manual adapter version does not match this FORGE installation",
        )

    def prepare_invocation(self, request: AdapterInvocationRequest) -> AdapterInvocationPlan:
        step_id = request.step_id.strip()
        if not step_id:
            raise ConfigurationError("Adapter invocation step ID must not be empty")
        if _SHA256_PATTERN.fullmatch(request.context_digest) is None:
            raise ConfigurationError(
                "Adapter context digest must use the sha256:<lowercase-hex> form"
            )
        constraints = tuple(
            self._require_text("Adapter constraint", item) for item in request.constraints
        )
        outputs = tuple(
            self._require_text("Adapter required output", item)
            for item in request.required_outputs
        )
        return AdapterInvocationPlan(
            adapter_id=self.adapter_id,
            adapter_version=self.report_version(),
            mode=AdapterInvocationMode.MANUAL_HANDOFF,
            step_id=step_id,
            context_digest=request.context_digest,
            required_outputs=outputs,
            constraints=constraints,
            standard_input=None,
            executable=None,
            arguments=(),
            working_directory=None,
            output_directory=None,
            result_manifest_contract="agent-result",
            limitations=_LIMITATIONS,
        )

    def start_process(self, plan: AdapterInvocationPlan) -> AdapterProcessStart:
        self._require_manual_plan(plan)
        return AdapterProcessStart(
            state=AdapterOperationState.NOT_APPLICABLE,
            detail="Manual handoff does not start an external process",
        )

    def cancel(self, handle: AdapterProcessHandle | None) -> AdapterOperationResult:
        self._require_manual_handle(handle)
        return AdapterOperationResult(
            state=AdapterOperationState.NOT_APPLICABLE,
            detail="Manual handoff has no FORGE-managed process to cancel",
        )

    def capture_output(self, handle: AdapterProcessHandle | None) -> AdapterOutputCapture:
        self._require_manual_handle(handle)
        return AdapterOutputCapture(
            state=AdapterOperationState.NOT_APPLICABLE,
            paths=(),
            detail="Manual handoff output is returned outside process capture",
        )

    def produce_result_manifest(
        self, handle: AdapterProcessHandle | None
    ) -> AdapterResultManifest:
        self._require_manual_handle(handle)
        return AdapterResultManifest(
            state=AdapterOperationState.MANUAL_REQUIRED,
            contract="agent-result",
            path=None,
            detail="The worker must return an AgentResult manifest for staged import",
        )

    def diagnostics(self) -> AdapterDiagnostic:
        version = self.report_version()
        return AdapterDiagnostic(
            adapter_id=self.adapter_id,
            display_name=self.display_name,
            availability=self.detect_availability(),
            detected_version=version,
            compatibility=self.assess_compatibility(version),
            authentication_state="not-required",
            supports_process_start=False,
            supports_cancellation=False,
            supports_output_capture=False,
            limitations=_LIMITATIONS,
        )

    @staticmethod
    def _require_text(label: str, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ConfigurationError(f"{label} must not be empty")
        return normalized

    def _require_manual_plan(self, plan: AdapterInvocationPlan) -> None:
        if (
            plan.adapter_id != self.adapter_id
            or plan.mode is not AdapterInvocationMode.MANUAL_HANDOFF
        ):
            raise ConfigurationError("Manual adapter received a plan for a different adapter mode")

    def _require_manual_handle(self, handle: AdapterProcessHandle | None) -> None:
        if handle is not None and handle.adapter_id != self.adapter_id:
            raise ConfigurationError("Manual adapter received a handle for a different adapter")
