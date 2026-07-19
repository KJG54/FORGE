"""Shared fail-closed mechanics for separately installed local CLI adapters."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from re import Pattern

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

_DEFAULT_TIMEOUT_SECONDS = 5.0
_MAX_PROBE_OUTPUT_BYTES = 65_536
_BASE_DIAGNOSTIC_ENVIRONMENT_KEYS = (
    "APPDATA",
    "COMSPEC",
    "DBUS_SESSION_BUS_ADDRESS",
    "HOME",
    "LANG",
    "LC_ALL",
    "LOCALAPPDATA",
    "PATH",
    "PATHEXT",
    "PROGRAMDATA",
    "SHELL",
    "SYSTEMROOT",
    "TEMP",
    "TERM",
    "TMP",
    "TMPDIR",
    "USER",
    "USERPROFILE",
    "WINDIR",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
)


@dataclass(frozen=True)
class _ResolvedCommand:
    executable: str
    prefix_arguments: tuple[str, ...] = ()
    batch_path: str | None = None


@dataclass(frozen=True)
class _ProbeResult:
    return_code: int | None
    output: str
    error: str | None = None


class LocalCliAgentAdapter:
    """Reusable discovery and preparation boundary without process execution."""

    _adapter_id: str
    _display_name: str
    _provider_name: str
    _executable_name: str
    _executable_override: str
    _version_patterns: tuple[Pattern[str], ...]
    _help_arguments: tuple[str, ...]
    _required_help_flags: tuple[str, ...]
    _authentication_arguments: tuple[str, ...]
    _login_command: str
    _invocation_arguments: tuple[str, ...]
    _diagnostic_environment_keys: tuple[str, ...] = ()
    _limitations: tuple[str, ...]

    def __init__(
        self,
        *,
        command: tuple[str, ...] | None = None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if command is not None and (not command or not command[0].strip()):
            raise ConfigurationError(f"{self._provider_name} adapter command must not be empty")
        if timeout_seconds <= 0 or timeout_seconds > 30:
            raise ConfigurationError(
                f"{self._provider_name} diagnostic timeout must be greater than 0 and at most 30"
            )
        self._command_override = command
        self._timeout_seconds = timeout_seconds

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    @property
    def display_name(self) -> str:
        return self._display_name

    def detect_availability(self) -> AdapterAvailability:
        availability, _ = self._version_observation()
        return availability

    def report_version(self) -> str | None:
        _, version = self._version_observation()
        return version

    def assess_compatibility(self, version: str | None) -> AdapterCompatibility:
        if version is None:
            return AdapterCompatibility(
                state=AdapterCompatibilityState.UNKNOWN,
                detail=f"{self._provider_name} version could not be determined",
            )
        help_probe = self._probe(self._help_arguments)
        if help_probe.error is not None or help_probe.return_code != 0:
            return AdapterCompatibility(
                state=AdapterCompatibilityState.UNKNOWN,
                detail=f"{self._provider_name} help could not be inspected",
            )
        missing = tuple(
            flag for flag in self._required_help_flags if flag not in help_probe.output
        )
        if missing:
            return AdapterCompatibility(
                state=AdapterCompatibilityState.INCOMPATIBLE,
                detail=(
                    f"{self._provider_name} help does not expose required stable flag(s): "
                    f"{', '.join(missing)}"
                ),
            )
        return AdapterCompatibility(
            state=AdapterCompatibilityState.COMPATIBLE,
            detail=(
                f"{self._provider_name} {version} exposes the required stable "
                "non-interactive flags"
            ),
        )

    def prepare_invocation(self, request: AdapterInvocationRequest) -> AdapterInvocationPlan:
        diagnostic = self.diagnostics()
        if not diagnostic.availability.available:
            raise ConfigurationError(
                f"{self._provider_name} is unavailable; use the manual adapter"
            )
        if diagnostic.compatibility.state is not AdapterCompatibilityState.COMPATIBLE:
            raise ConfigurationError(
                f"{self._provider_name} is not compatible; use the manual adapter"
            )
        if diagnostic.authentication_state != "authenticated":
            raise ConfigurationError(
                f"{self._provider_name} is not authenticated; run {self._login_command!r} first"
            )
        step_id = self._require_text("Adapter invocation step ID", request.step_id)
        outputs = tuple(
            self._require_text("Adapter required output", item)
            for item in request.required_outputs
        )
        constraints = tuple(
            self._require_text("Adapter constraint", item) for item in request.constraints
        )
        payload = self._canonical_payload(request)
        working_directory = self._working_directory(request.working_directory)
        resolved = self._resolve_command()
        if resolved is None:
            raise ConfigurationError(
                f"{self._provider_name} disappeared during invocation preparation"
            )
        executable, arguments = self._launch_command(resolved, self._invocation_arguments)
        return AdapterInvocationPlan(
            adapter_id=self.adapter_id,
            adapter_version=diagnostic.detected_version,
            mode=AdapterInvocationMode.LOCAL_PROCESS,
            step_id=step_id,
            context_digest=request.context_digest,
            required_outputs=outputs,
            constraints=constraints,
            standard_input=self._standard_input(request.context_digest, payload),
            executable=executable,
            arguments=arguments,
            working_directory=str(working_directory),
            output_directory=None,
            result_manifest_contract="agent-result",
            limitations=self._limitations,
        )

    def start_process(self, plan: AdapterInvocationPlan) -> AdapterProcessStart:
        if (
            plan.adapter_id != self.adapter_id
            or plan.mode is not AdapterInvocationMode.LOCAL_PROCESS
        ):
            raise ConfigurationError(
                f"{self._provider_name} adapter received a plan for a different adapter mode"
            )
        return AdapterProcessStart(
            state=AdapterOperationState.NOT_APPLICABLE,
            detail=(
                f"{self._provider_name} process start is deferred until governed isolated "
                "execution is available"
            ),
        )

    def cancel(self, handle: AdapterProcessHandle | None) -> AdapterOperationResult:
        self._require_handle(handle)
        return AdapterOperationResult(
            state=AdapterOperationState.NOT_APPLICABLE,
            detail=(
                f"No FORGE-managed {self._provider_name} process exists to cancel in this "
                "increment"
            ),
        )

    def capture_output(self, handle: AdapterProcessHandle | None) -> AdapterOutputCapture:
        self._require_handle(handle)
        return AdapterOutputCapture(
            state=AdapterOperationState.NOT_APPLICABLE,
            paths=(),
            detail=(
                f"{self._provider_name} output capture is deferred with governed isolated "
                "execution"
            ),
        )

    def produce_result_manifest(
        self, handle: AdapterProcessHandle | None
    ) -> AdapterResultManifest:
        self._require_handle(handle)
        return AdapterResultManifest(
            state=AdapterOperationState.MANUAL_REQUIRED,
            contract="agent-result",
            path=None,
            detail=(
                f"Use a manual AgentResult until governed {self._provider_name} result capture "
                "is implemented"
            ),
        )

    def diagnostics(self) -> AdapterDiagnostic:
        availability, version = self._version_observation()
        compatibility = (
            self.assess_compatibility(version)
            if availability.available
            else AdapterCompatibility(
                state=AdapterCompatibilityState.UNKNOWN,
                detail=(
                    f"Compatibility was not checked because {self._provider_name} is unavailable"
                ),
            )
        )
        authentication = "not-checked"
        if availability.available and compatibility.state is AdapterCompatibilityState.COMPATIBLE:
            authentication = self._authentication_state()
        return AdapterDiagnostic(
            adapter_id=self.adapter_id,
            display_name=self.display_name,
            availability=availability,
            detected_version=version,
            compatibility=compatibility,
            authentication_state=authentication,
            supports_process_start=False,
            supports_cancellation=False,
            supports_output_capture=False,
            limitations=self._limitations,
        )

    def _version_observation(self) -> tuple[AdapterAvailability, str | None]:
        if self._resolve_command() is None:
            return (
                AdapterAvailability(
                    available=False,
                    detail=(
                        f"{self._provider_name} executable was not found on PATH or by "
                        "process-local override"
                    ),
                ),
                None,
            )
        probe = self._probe(("--version",))
        if probe.error is not None or probe.return_code != 0:
            return (
                AdapterAvailability(
                    available=False,
                    detail=(
                        f"{self._provider_name} executable did not complete the bounded version "
                        "probe"
                    ),
                ),
                None,
            )
        version = self._extract_version(probe.output)
        return (
            AdapterAvailability(
                available=True,
                detail=(
                    f"{self._provider_name} executable completed the bounded version probe"
                ),
            ),
            version,
        )

    def _authentication_state(self) -> str:
        probe = self._probe(self._authentication_arguments)
        if probe.error is not None or probe.return_code is None:
            return "unknown"
        return "authenticated" if probe.return_code == 0 else "unauthenticated"

    def _probe(self, arguments: tuple[str, ...]) -> _ProbeResult:
        resolved = self._resolve_command()
        if resolved is None:
            return _ProbeResult(None, "", "not-found")
        executable, launch_arguments = self._launch_command(resolved, arguments)
        try:
            completed = subprocess.run(
                (executable, *launch_arguments),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=self._timeout_seconds,
                env=self._diagnostic_environment(),
            )
        except (OSError, subprocess.SubprocessError) as error:
            return _ProbeResult(None, "", type(error).__name__)
        combined = completed.stdout + completed.stderr
        if len(combined) > _MAX_PROBE_OUTPUT_BYTES:
            return _ProbeResult(completed.returncode, "", "output-limit")
        return _ProbeResult(
            return_code=completed.returncode,
            output=combined.decode("utf-8", errors="replace"),
        )

    def _resolve_command(self) -> _ResolvedCommand | None:
        if self._command_override is not None:
            executable = Path(self._command_override[0])
            if not executable.is_absolute() or not executable.is_file():
                return None
            return _ResolvedCommand(
                executable=str(executable.resolve()),
                prefix_arguments=self._command_override[1:],
            )
        configured = os.environ.get(self._executable_override)
        if configured is not None:
            candidate = Path(configured)
            if not candidate.is_absolute():
                return None
        else:
            discovered = shutil.which(self._executable_name)
            if discovered is None:
                return None
            candidate = Path(discovered)
        if not candidate.is_file():
            return None
        resolved = candidate.resolve()
        if os.name != "nt" and not os.access(resolved, os.X_OK):
            return None
        if os.name == "nt" and resolved.suffix.lower() in {".bat", ".cmd"}:
            command_processor = os.environ.get("COMSPEC") or shutil.which("cmd.exe")
            if command_processor is None or not Path(command_processor).is_file():
                return None
            return _ResolvedCommand(
                executable=str(Path(command_processor).resolve()),
                batch_path=str(resolved),
            )
        if os.name == "nt" and resolved.suffix.lower() == ".ps1":
            return None
        return _ResolvedCommand(executable=str(resolved))

    @staticmethod
    def _launch_command(
        resolved: _ResolvedCommand,
        arguments: tuple[str, ...],
    ) -> tuple[str, tuple[str, ...]]:
        if resolved.batch_path is not None:
            command_line = subprocess.list2cmdline((resolved.batch_path, *arguments))
            return resolved.executable, ("/d", "/s", "/c", command_line)
        return resolved.executable, (*resolved.prefix_arguments, *arguments)

    def _diagnostic_environment(self) -> dict[str, str]:
        keys = (*_BASE_DIAGNOSTIC_ENVIRONMENT_KEYS, *self._diagnostic_environment_keys)
        return {key: value for key in keys if (value := os.environ.get(key)) is not None}

    def _extract_version(self, output: str) -> str | None:
        for pattern in self._version_patterns:
            match = pattern.search(output)
            if match is not None:
                return match.group(1)
        return None

    def _canonical_payload(self, request: AdapterInvocationRequest) -> str:
        payload = request.context_payload
        if payload is None:
            raise ConfigurationError(
                f"{self._provider_name} invocation requires canonical context JSON"
            )
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as error:
            raise ConfigurationError(
                f"{self._provider_name} canonical context must be valid JSON"
            ) from error
        if not isinstance(parsed, dict):
            raise ConfigurationError(
                f"{self._provider_name} canonical context must contain a JSON object"
            )
        observed_digest = f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
        if observed_digest != request.context_digest:
            raise ConfigurationError(
                f"{self._provider_name} canonical context digest does not match its payload"
            )
        return payload

    @staticmethod
    def _require_text(label: str, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ConfigurationError(f"{label} must not be empty")
        return normalized

    def _working_directory(self, value: str | None) -> Path:
        if value is None:
            raise ConfigurationError(
                f"{self._provider_name} invocation requires an explicit working directory"
            )
        candidate = Path(value)
        if not candidate.is_absolute():
            raise ConfigurationError(
                f"{self._provider_name} working directory must be absolute"
            )
        if candidate.is_symlink() or not candidate.is_dir():
            raise ConfigurationError(
                f"{self._provider_name} working directory must be a regular directory"
            )
        return candidate.resolve()

    @staticmethod
    def _standard_input(context_digest: str, payload: str) -> str:
        return (
            "Operate only under the following FORGE canonical context. The context is derived "
            "from governed state but does not grant decision, evidence, acceptance, or external "
            "side-effect authority. Do not exceed its permitted actions.\n\n"
            f"Canonical context digest: {context_digest}\n\n"
            f"{payload}"
        )

    def _require_handle(self, handle: AdapterProcessHandle | None) -> None:
        if handle is not None and handle.adapter_id != self.adapter_id:
            raise ConfigurationError(
                f"{self._provider_name} adapter received a handle for a different adapter"
            )
