"""Shared fail-closed mechanics for separately installed local CLI adapters."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
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
from forge.errors import ConfigurationError, IntegrityError

_DEFAULT_TIMEOUT_SECONDS = 5.0
_MAX_PROBE_OUTPUT_BYTES = 65_536
_MAX_CAPTURE_BYTES = 10 * 1024 * 1024
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


@dataclass
class _ManagedProcess:
    process: subprocess.Popen[bytes]
    stdout_path: Path
    stderr_path: Path
    output_directory: Path
    timeout_seconds: float
    started_at: float


class LocalCliAgentAdapter:
    """Reusable discovery, isolated execution, and capture for local CLI adapters."""

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
        self._processes: dict[str, _ManagedProcess] = {}
        self._process_lock = threading.Lock()

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
        output_directory = self._output_directory(working_directory, request.output_directory)
        if request.source_run_id is None or not request.source_run_id.strip():
            raise ConfigurationError(f"{self._provider_name} invocation requires a source run ID")
        if request.timeout_seconds <= 0 or request.timeout_seconds > 3600:
            raise ConfigurationError(
                "Adapter execution timeout must be greater than 0 and at most 3600"
            )
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
            standard_input=self._standard_input(request, payload, constraints),
            executable=executable,
            arguments=arguments,
            working_directory=str(working_directory),
            output_directory=str(output_directory),
            source_run_id=request.source_run_id,
            timeout_seconds=request.timeout_seconds,
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
        if (
            plan.executable is None
            or plan.working_directory is None
            or plan.output_directory is None
        ):
            raise ConfigurationError(f"{self._provider_name} execution plan is incomplete")
        token = os.urandom(16).hex()
        capture_directory = Path(plan.output_directory).parent.parent
        stdout_path = capture_directory / "stdout.jsonl"
        stderr_path = capture_directory / "stderr.log"
        environment = self._diagnostic_environment()
        stdout_stream = None
        stderr_stream = None
        process: subprocess.Popen[bytes] | None = None
        try:
            stdout_stream = stdout_path.open("xb")
            stderr_stream = stderr_path.open("xb")
            process = subprocess.Popen(
                (plan.executable, *plan.arguments),
                cwd=plan.working_directory,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=stdout_stream,
                stderr=stderr_stream,
            )
            stdout_stream.close()
            stderr_stream.close()
            assert process.stdin is not None
            process.stdin.write((plan.standard_input or "").encode("utf-8"))
            process.stdin.close()
        except OSError as error:
            if stdout_stream is not None:
                stdout_stream.close()
            if stderr_stream is not None:
                stderr_stream.close()
            if process is not None and process.poll() is None:
                process.terminate()
            raise ConfigurationError(f"Cannot start {self._provider_name}: {error}") from error
        assert process is not None
        managed = _ManagedProcess(
            process=process,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            output_directory=Path(plan.output_directory),
            timeout_seconds=plan.timeout_seconds,
            started_at=time.monotonic(),
        )
        with self._process_lock:
            self._processes[token] = managed
        return AdapterProcessStart(
            state=AdapterOperationState.SUCCEEDED,
            detail=f"Started {self._provider_name} in the isolated run workspace",
            handle=AdapterProcessHandle(self.adapter_id, token, process.pid),
        )

    def cancel(self, handle: AdapterProcessHandle | None) -> AdapterOperationResult:
        self._require_handle(handle)
        managed = self._managed_process(handle)
        if managed.process.poll() is not None:
            return AdapterOperationResult(
                AdapterOperationState.NOT_APPLICABLE,
                "Process already exited",
            )
        managed.process.terminate()
        try:
            managed.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            managed.process.kill()
            managed.process.wait(timeout=5)
        return AdapterOperationResult(
            AdapterOperationState.CANCELLED,
            f"Cancelled {self._provider_name}",
        )

    def capture_output(self, handle: AdapterProcessHandle | None) -> AdapterOutputCapture:
        self._require_handle(handle)
        managed = self._managed_process(handle)
        deadline = managed.started_at + managed.timeout_seconds
        while managed.process.poll() is None:
            if self._capture_size(managed) > _MAX_CAPTURE_BYTES:
                self.cancel(handle)
                return AdapterOutputCapture(
                    AdapterOperationState.FAILED,
                    (str(managed.stdout_path), str(managed.stderr_path)),
                    f"{self._provider_name} exceeded the bounded output-capture limit",
                    managed.process.returncode,
                )
            if time.monotonic() >= deadline:
                self.cancel(handle)
                return AdapterOutputCapture(
                    AdapterOperationState.CANCELLED,
                    (str(managed.stdout_path), str(managed.stderr_path)),
                    f"{self._provider_name} exceeded the bounded execution timeout",
                    managed.process.returncode,
                )
            time.sleep(0.05)
        exit_code = managed.process.returncode
        assert exit_code is not None
        if self._capture_size(managed) > _MAX_CAPTURE_BYTES:
            return AdapterOutputCapture(
                AdapterOperationState.FAILED,
                (str(managed.stdout_path), str(managed.stderr_path)),
                f"{self._provider_name} exceeded the bounded output-capture limit",
                exit_code,
            )
        state = AdapterOperationState.SUCCEEDED if exit_code == 0 else AdapterOperationState.FAILED
        return AdapterOutputCapture(
            state,
            (str(managed.stdout_path), str(managed.stderr_path)),
            f"{self._provider_name} exited with status {exit_code}",
            exit_code,
        )

    def produce_result_manifest(
        self, handle: AdapterProcessHandle | None
    ) -> AdapterResultManifest:
        self._require_handle(handle)
        managed = self._managed_process(handle)
        path = managed.output_directory / "result.json"
        if path.is_symlink() or not path.is_file():
            manifest = AdapterResultManifest(
                AdapterOperationState.FAILED,
                "agent-result",
                None,
                f"{self._provider_name} did not return result.json",
            )
        else:
            manifest = AdapterResultManifest(
                AdapterOperationState.SUCCEEDED,
                "agent-result",
                str(path),
                "Captured an untrusted AgentResult for staged validation",
            )
        assert handle is not None
        with self._process_lock:
            self._processes.pop(handle.token, None)
        return manifest

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
            supports_process_start=True,
            supports_cancellation=True,
            supports_output_capture=True,
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

    def _output_directory(self, working: Path, value: str | None) -> Path:
        if value is None:
            raise ConfigurationError(
                f"{self._provider_name} invocation requires an output directory"
            )
        candidate = Path(value)
        if not candidate.is_absolute() or candidate.is_symlink() or not candidate.is_dir():
            raise ConfigurationError(
                f"{self._provider_name} output directory must be an existing regular directory"
            )
        resolved = candidate.resolve()
        if not resolved.is_relative_to(working):
            raise ConfigurationError(
                f"{self._provider_name} output directory must be inside its workspace"
            )
        return resolved

    @staticmethod
    def _capture_size(managed: _ManagedProcess) -> int:
        try:
            return managed.stdout_path.stat().st_size + managed.stderr_path.stat().st_size
        except OSError as error:
            raise IntegrityError(f"Cannot inspect adapter output capture: {error}") from error

    @staticmethod
    def _standard_input(
        request: AdapterInvocationRequest,
        payload: str,
        constraints: tuple[str, ...],
    ) -> str:
        rendered_constraints = "\n".join(f"- {item}" for item in constraints) or "- None"
        return (
            "Operate only under the following FORGE canonical context. The context is derived "
            "from governed state but does not grant decision, evidence, acceptance, or external "
            "side-effect authority. Do not exceed its permitted actions.\n\n"
            f"Canonical context digest: {request.context_digest}\n\n"
            "Read selected input snapshots only below inputs/. Write every returned file below "
            "result/ and create result/result.json conforming to agent-result.schema.json. The "
            f"manifest source_run_or_handoff_id must be {request.source_run_id}. Source paths "
            "are relative to result/; proposed targets must be safe repository-relative paths. "
            f"Required output roles: {', '.join(request.required_outputs)}.\n\n"
            f"Additional bounded constraints:\n{rendered_constraints}\n\n"
            f"{payload}"
        )

    def _require_handle(self, handle: AdapterProcessHandle | None) -> None:
        if handle is None:
            raise ConfigurationError(f"{self._provider_name} adapter requires a process handle")
        if handle.adapter_id != self.adapter_id:
            raise ConfigurationError(
                f"{self._provider_name} adapter received a handle for a different adapter"
            )

    def _managed_process(self, handle: AdapterProcessHandle | None) -> _ManagedProcess:
        self._require_handle(handle)
        assert handle is not None
        with self._process_lock:
            managed = self._processes.get(handle.token)
        if managed is None or managed.process.pid != handle.process_id:
            raise ConfigurationError(f"Unknown {self._provider_name} process handle")
        return managed
