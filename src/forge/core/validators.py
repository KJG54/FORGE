"""Supervised local-validator execution and immutable check-result capture."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from forge import __version__
from forge.contracts.actors import Actor, ActorType
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.runs import RunRecord
from forge.contracts.state import RunState, StepState
from forge.contracts.verification import (
    CheckExecutionStatus,
    CheckOutcome,
    CheckResult,
)
from forge.contracts.workflows import StepDefinition
from forge.core.artifacts import current_revisions_for_roles
from forge.core.capabilities import (
    CapabilityInspection,
    require_validator_capability_approval,
)
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.transitions import CHECK_RECORDED, VALIDATOR_RUN_STARTED
from forge.core.verification import check_digest_payload
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.security.paths import resolve_repository_path
from forge.storage.canonical import sha256_digest
from forge.storage.configuration import load_configuration
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot

MAX_VALIDATOR_CAPTURE_BYTES = 1_048_576
_CAPTURE_CHUNK_BYTES = 65_536
_TERMINATION_GRACE_SECONDS = 5.0
_SAFE_INHERITED_ENVIRONMENT_NAMES = (
    "LANG",
    "LC_ALL",
    "SYSTEMROOT",
    "WINDIR",
)
_PROCESS_OUTCOME_LIMITATION = (
    "The process result supports only this declared structural check; it does not establish "
    "semantic or factual truth, create evidence, verify the step, or grant owner acceptance."
)
_OUTPUT_INTERPRETATION_LIMITATION = (
    "Stdout and stderr were captured as bounded local bytes and were not interpreted as "
    "governance authority."
)


@dataclass(frozen=True)
class ValidatorExecutionResult:
    run: RunRecord
    check: CheckResult
    start_event: AuditEvent
    check_event: AuditEvent


@dataclass(frozen=True)
class _ProcessObservation:
    status: CheckExecutionStatus
    exit_status: int | None
    started_at: datetime
    ended_at: datetime
    stdout_digest: str
    stderr_digest: str
    stdout_byte_count: int
    stderr_byte_count: int
    detail: str


class _CaptureBudget:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.total = 0
        self.stdout_bytes = 0
        self.stderr_bytes = 0
        self.lock = threading.Lock()
        self.overflow = threading.Event()
        self.failed = threading.Event()

    def retain(self, stream_name: str, chunk: bytes) -> bytes:
        with self.lock:
            remaining = max(self.limit - self.total, 0)
            retained = chunk[:remaining]
            self.total += len(retained)
            if stream_name == "stdout":
                self.stdout_bytes += len(retained)
            else:
                self.stderr_bytes += len(retained)
            if len(retained) != len(chunk):
                self.overflow.set()
            return retained


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _step(active: ActiveInitiative, step_id: str) -> StepDefinition:
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise ConflictError(f"Unknown workflow step {step_id!r}")
    return step


def _validator_actor(
    layout: RepositoryLayout,
    inspection: CapabilityInspection,
) -> Actor:
    configuration = load_configuration(layout.configuration_file)
    definition = inspection.definition
    provider_version = inspection.provider_version or "unknown"
    return Actor(
        id=uuid5(
            NAMESPACE_URL,
            (
                f"forge:{configuration.project_id}:validator:{definition.id}:"
                f"{definition.version}:{provider_version}"
            ),
        ),
        actor_type=ActorType.EXTERNAL_TOOL,
        display_label=definition.provider,
        tool_reference=f"{definition.id}@{definition.version}",
    )


def _ensure_directory(path: Path) -> bool:
    if path.is_symlink():
        raise SecurityError(f"Validator path is a symbolic link: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Validator path is not a directory: {path}")
        return False
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create validator directory {path}: {error}") from error
    return True


def _prepare_capture_directory(layout: RepositoryLayout, run_id: UUID) -> tuple[Path, Path]:
    _ensure_directory(layout.validator_capture_directory)
    run_directory = layout.validator_capture_directory / str(run_id)
    _ensure_directory(run_directory)
    temporary_directory = run_directory / "tmp"
    _ensure_directory(temporary_directory)
    return run_directory, temporary_directory


def _working_directory(
    layout: RepositoryLayout,
    inspection: CapabilityInspection,
) -> tuple[Path, str]:
    rules = inspection.definition.working_directory_rules
    if len(rules) > 1:
        raise IntegrityError("Local validator has more than one working-directory rule")
    if not rules:
        return layout.root, "."
    resolved = resolve_repository_path(layout.root, rules[0], must_exist=True)
    if resolved.is_symlink() or not resolved.is_dir():
        raise SecurityError(f"Validator working directory is missing or unsafe: {rules[0]}")
    return resolved, rules[0]


def _environment(
    declared_names: tuple[str, ...],
    temporary_directory: Path,
) -> dict[str, str]:
    names = (*_SAFE_INHERITED_ENVIRONMENT_NAMES, *declared_names)
    environment = {
        name: value
        for name in names
        if (value := os.environ.get(name)) is not None
    }
    temporary = str(temporary_directory)
    if os.name == "nt":
        environment["TEMP"] = temporary
        environment["TMP"] = temporary
    else:
        environment["TMPDIR"] = temporary
    return environment


def _capture_reader(
    source: BinaryIO,
    destination: BinaryIO,
    stream_name: str,
    budget: _CaptureBudget,
) -> None:
    try:
        while chunk := source.read(_CAPTURE_CHUNK_BYTES):
            retained = budget.retain(stream_name, chunk)
            if retained:
                destination.write(retained)
                destination.flush()
    except OSError:
        budget.failed.set()
    finally:
        with suppress(OSError):
            source.close()


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    with suppress(OSError):
        process.terminate()
    try:
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        with suppress(OSError):
            process.kill()
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)


def _capture_digest(path: Path) -> tuple[str, int]:
    try:
        content = path.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read validator output capture {path}: {error}") from error
    return sha256_digest(content), len(content)


def _supervise_process(
    *,
    executable: str,
    arguments: tuple[str, ...],
    working_directory: Path,
    environment: dict[str, str],
    timeout_seconds: int,
    stdout_path: Path,
    stderr_path: Path,
) -> _ProcessObservation:
    started_at = utc_now()
    status = CheckExecutionStatus.START_ERROR
    exit_status: int | None = None
    detail = "Validator process could not be started"
    process: subprocess.Popen[bytes] | None = None
    budget = _CaptureBudget(MAX_VALIDATOR_CAPTURE_BYTES)
    threads: tuple[threading.Thread, ...] = ()
    with stdout_path.open("xb") as stdout_stream, stderr_path.open("xb") as stderr_stream:
        try:
            process = subprocess.Popen(
                (executable, *arguments),
                cwd=working_directory,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except OSError:
            pass
        else:
            assert process.stdout is not None
            assert process.stderr is not None
            threads = (
                threading.Thread(
                    target=_capture_reader,
                    args=(process.stdout, stdout_stream, "stdout", budget),
                    daemon=True,
                ),
                threading.Thread(
                    target=_capture_reader,
                    args=(process.stderr, stderr_stream, "stderr", budget),
                    daemon=True,
                ),
            )
            for thread in threads:
                thread.start()
            deadline = time.monotonic() + timeout_seconds
            while process.poll() is None:
                if budget.overflow.is_set():
                    status = CheckExecutionStatus.OUTPUT_LIMIT_EXCEEDED
                    detail = (
                        f"Validator exceeded the {MAX_VALIDATOR_CAPTURE_BYTES}-byte "
                        "combined output limit"
                    )
                    _terminate(process)
                    break
                if budget.failed.is_set():
                    status = CheckExecutionStatus.SUPERVISION_ERROR
                    detail = "Validator output capture failed"
                    _terminate(process)
                    break
                if time.monotonic() >= deadline:
                    status = CheckExecutionStatus.TIMED_OUT
                    detail = f"Validator exceeded its {timeout_seconds}-second timeout"
                    _terminate(process)
                    break
                time.sleep(0.02)
            if process.poll() is not None and status is CheckExecutionStatus.START_ERROR:
                status = CheckExecutionStatus.COMPLETED
                exit_status = process.returncode
                detail = f"Validator exited with status {exit_status}"
            else:
                exit_status = process.returncode
            for thread in threads:
                thread.join(timeout=_TERMINATION_GRACE_SECONDS)
            if any(thread.is_alive() for thread in threads) or budget.failed.is_set():
                status = CheckExecutionStatus.SUPERVISION_ERROR
                detail = "Validator output capture did not finish safely"
            elif (
                budget.overflow.is_set()
                and status is CheckExecutionStatus.COMPLETED
            ):
                status = CheckExecutionStatus.OUTPUT_LIMIT_EXCEEDED
                detail = (
                    f"Validator exceeded the {MAX_VALIDATOR_CAPTURE_BYTES}-byte "
                    "combined output limit"
                )
    stdout_digest, stdout_byte_count = _capture_digest(stdout_path)
    stderr_digest, stderr_byte_count = _capture_digest(stderr_path)
    return _ProcessObservation(
        status=status,
        exit_status=exit_status,
        started_at=started_at,
        ended_at=utc_now(),
        stdout_digest=stdout_digest,
        stderr_digest=stderr_digest,
        stdout_byte_count=stdout_byte_count,
        stderr_byte_count=stderr_byte_count,
        detail=detail,
    )


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def _append_run_start(
    active: ActiveInitiative,
    run: RunRecord,
    event: AuditEvent,
) -> None:
    created_directory = _ensure_directory(active.layout.validator_run_directory)
    path = active.layout.validator_run_directory / f"{run.id}.json"
    try:
        write_record(path, run)
        append_event_and_update_snapshot(
            active.layout.event_journal_file,
            active.layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(active.layout, event.id):
            path.unlink(missing_ok=True)
            if created_directory:
                with suppress(OSError):
                    path.parent.rmdir()
        raise


def _append_check(
    active: ActiveInitiative,
    check: CheckResult,
    event: AuditEvent,
) -> None:
    created_directory = _ensure_directory(active.layout.check_directory)
    path = active.layout.check_directory / f"{check.id}.json"
    try:
        write_record(path, check)
        append_event_and_update_snapshot(
            active.layout.event_journal_file,
            active.layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(active.layout, event.id):
            path.unlink(missing_ok=True)
            if created_directory:
                with suppress(OSError):
                    path.parent.rmdir()
        raise


def execute_validator_check(
    layout: RepositoryLayout,
    *,
    step_id: str,
    check_id: str,
    check_version: str,
    capability_id: str,
) -> ValidatorExecutionResult:
    """Execute one approved validator without advancing workflow lifecycle state."""

    active = load_active_initiative(layout)
    step = _step(active, step_id)
    if active.state.step_states.get(step_id) is not StepState.AWAITING_VERIFICATION:
        raise ConflictError(f"Step {step_id} is not awaiting verification")
    if check_id not in step.check_requirements:
        raise ConflictError(
            f"Check {check_id!r} is not declared for step {step_id}; required checks are "
            f"{list(step.check_requirements)}"
        )
    check_version = _require_text("Check version", check_version)
    inspection, approval = require_validator_capability_approval(layout, capability_id)
    definition = inspection.definition
    if definition.executable is None or definition.timeout_seconds is None:
        raise IntegrityError("Approved local validator has an incomplete invocation profile")
    revisions = current_revisions_for_roles(active, step.required_outputs)
    target_ids = tuple(revision.id for revision in revisions)
    target_digests = tuple(revision.content_digest for revision in revisions)
    working_directory, working_directory_reference = _working_directory(layout, inspection)
    actor = _validator_actor(layout, inspection)
    run_id = uuid4()
    result_id = uuid4()
    run_directory, temporary_directory = _prepare_capture_directory(layout, run_id)
    stdout_path = run_directory / "stdout.log"
    stderr_path = run_directory / "stderr.log"
    stdout_reference = stdout_path.relative_to(layout.root).as_posix()
    stderr_reference = stderr_path.relative_to(layout.root).as_posix()
    environment = _environment(inspection.environment_access, temporary_directory)
    environment_names = tuple(sorted(environment))
    invocation_metadata = {
        "arguments": json.dumps(list(definition.arguments), ensure_ascii=False),
        "capability-definition-digest": inspection.definition_digest,
        "capability-version": definition.version,
        "environment-access": json.dumps(list(inspection.environment_access)),
        "environment-effective-names": json.dumps(list(environment_names)),
        "executable": definition.executable,
        "expected-outputs": json.dumps(list(inspection.output_locations)),
        "mode": "trusted-local-validator",
        "output-limit-bytes": str(MAX_VALIDATOR_CAPTURE_BYTES),
        "timeout-seconds": str(definition.timeout_seconds),
        "working-directory": working_directory_reference,
    }
    invocation_digest = canonical_json_digest(
        {
            "approval_id": str(approval.id),
            "arguments": list(definition.arguments),
            "capability_digest": inspection.definition_digest,
            "capability_id": definition.id,
            "capability_version": definition.version,
            "check_id": check_id,
            "check_result_id": str(result_id),
            "check_version": check_version,
            "environment_names": list(environment_names),
            "executable": definition.executable,
            "expected_outputs": list(inspection.output_locations),
            "output_limit_bytes": MAX_VALIDATOR_CAPTURE_BYTES,
            "run_id": str(run_id),
            "step_id": step_id,
            "target_artifact_digests": list(target_digests),
            "target_artifact_revision_ids": [str(item) for item in target_ids],
            "timeout_seconds": definition.timeout_seconds,
            "working_directory": working_directory_reference,
        }
    )
    started_at = utc_now()
    start_sequence = active.state.journal_head_sequence + 1
    run = RunRecord(
        id=run_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=started_at,
        event_sequence=start_sequence,
        run_id=run_id,
        authorization_basis=(
            "exact-profile owner capability approval authorized one local validator attempt"
        ),
        tool_version=__version__,
        affected_record_ids=(run_id, approval.id, result_id, *target_ids),
        affected_digests=(
            invocation_digest,
            approval.capability_digest,
            *target_digests,
        ),
        step_id=step_id,
        worker=actor,
        adapter_reference=f"validator:{definition.id}",
        capability_ids=(definition.id,),
        capability_approval_ids=(approval.id,),
        side_effect_class=definition.side_effect_class,
        status=RunState.RUNNING,
        started_at=started_at,
        input_context_digest=invocation_digest,
        exit_metadata={
            "check_id": check_id,
            "check_result_id": str(result_id),
            "check_version": check_version,
            "kind": "validator-check",
        },
    )
    start_event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=start_sequence,
        timestamp=started_at,
        event_type=VALIDATOR_RUN_STARTED,
        actor=actor,
        run_id=run_id,
        authorization_basis=run.authorization_basis,
        affected_record_ids=(run_id, approval.id, result_id, *target_ids),
        affected_digests=run.affected_digests,
        metadata={
            "capability_approval_id": str(approval.id),
            "capability_id": definition.id,
            "check_id": check_id,
            "check_result_id": str(result_id),
            "check_version": check_version,
            "invocation_digest": invocation_digest,
            "step_id": step_id,
            "target_artifact_revision_ids": [str(item) for item in target_ids],
        },
    )
    _append_run_start(active, run, start_event)

    try:
        observation = _supervise_process(
            executable=definition.executable,
            arguments=definition.arguments,
            working_directory=working_directory,
            environment=environment,
            timeout_seconds=definition.timeout_seconds,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
    except Exception as error:
        if not stdout_path.exists():
            stdout_path.touch()
        if not stderr_path.exists():
            stderr_path.touch()
        stdout_digest, stdout_byte_count = _capture_digest(stdout_path)
        stderr_digest, stderr_byte_count = _capture_digest(stderr_path)
        observation = _ProcessObservation(
            status=CheckExecutionStatus.SUPERVISION_ERROR,
            exit_status=None,
            started_at=started_at,
            ended_at=utc_now(),
            stdout_digest=stdout_digest,
            stderr_digest=stderr_digest,
            stdout_byte_count=stdout_byte_count,
            stderr_byte_count=stderr_byte_count,
            detail=f"Validator supervision failed with {type(error).__name__}",
        )

    outcome = (
        CheckOutcome.PASSED
        if (
            observation.status is CheckExecutionStatus.COMPLETED
            and observation.exit_status == 0
        )
        else (
            CheckOutcome.FAILED
            if observation.status is CheckExecutionStatus.COMPLETED
            else CheckOutcome.ERROR
        )
    )
    limitations = (
        _PROCESS_OUTCOME_LIMITATION,
        _OUTPUT_INTERPRETATION_LIMITATION,
        observation.detail,
    )
    result_digest = canonical_json_digest(
        check_digest_payload(
            check_id=check_id,
            check_version=check_version,
            target_ids=target_ids,
            invocation_metadata=invocation_metadata,
            started_at=observation.started_at,
            ended_at=observation.ended_at,
            exit_status=observation.exit_status,
            outcome=outcome,
            limitations=limitations,
            actor=actor,
            capability_id=definition.id,
            capability_approval_id=approval.id,
            run_id=run_id,
            invocation_digest=invocation_digest,
            execution_status=observation.status.value,
            stdout_capture_path=stdout_reference,
            stderr_capture_path=stderr_reference,
            stdout_digest=observation.stdout_digest,
            stderr_digest=observation.stderr_digest,
            stdout_byte_count=observation.stdout_byte_count,
            stderr_byte_count=observation.stderr_byte_count,
        )
    )
    refreshed = load_active_initiative(layout)
    check_sequence = refreshed.state.journal_head_sequence + 1
    recorded_at = utc_now()
    basis = (
        "approved local validator produced a bounded process result for one declared check"
    )
    check = CheckResult(
        id=result_id,
        initiative_id=refreshed.initiative.id,
        actor_id=actor.id,
        recorded_at=recorded_at,
        event_sequence=check_sequence,
        run_id=run_id,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=(run_id, approval.id, *target_ids),
        affected_digests=(
            result_digest,
            invocation_digest,
            observation.stdout_digest,
            observation.stderr_digest,
            *target_digests,
        ),
        check_id=check_id,
        check_version=check_version,
        target_artifact_revision_ids=target_ids,
        capability_id=definition.id,
        capability_approval_id=approval.id,
        invocation_digest=invocation_digest,
        execution_status=observation.status,
        stdout_capture_path=stdout_reference,
        stderr_capture_path=stderr_reference,
        stdout_digest=observation.stdout_digest,
        stderr_digest=observation.stderr_digest,
        stdout_byte_count=observation.stdout_byte_count,
        stderr_byte_count=observation.stderr_byte_count,
        invocation_metadata=invocation_metadata,
        started_at=observation.started_at,
        ended_at=observation.ended_at,
        exit_status=observation.exit_status,
        outcome=outcome,
        limitations=limitations,
        result_digest=result_digest,
        actor=actor,
    )
    check_event = AuditEvent(
        id=uuid4(),
        initiative_id=refreshed.initiative.id,
        sequence=check_sequence,
        timestamp=recorded_at,
        event_type=CHECK_RECORDED,
        actor=actor,
        run_id=run_id,
        authorization_basis=basis,
        affected_record_ids=(result_id, run_id, approval.id, *target_ids),
        affected_digests=check.affected_digests,
        metadata={
            "capability_approval_id": str(approval.id),
            "capability_id": definition.id,
            "check_id": check_id,
            "check_result_id": str(result_id),
            "execution_status": observation.status.value,
            "outcome": outcome.value,
            "step_id": step_id,
            "target_artifact_revision_ids": [str(item) for item in target_ids],
            "validator_run_id": str(run_id),
        },
    )
    _append_check(refreshed, check, check_event)
    return ValidatorExecutionResult(run, check, start_event, check_event)


def load_validator_run(layout: RepositoryLayout, run_id: UUID) -> RunRecord:
    """Load one immutable validator attempt record for inspection."""
    load_active_initiative(layout, allow_paused=True, allow_untrusted_pack=True)
    path = layout.validator_run_directory / f"{run_id}.json"
    if not path.exists():
        raise ConflictError(f"Unknown validator run {run_id}")
    return load_record(path, RunRecord)
