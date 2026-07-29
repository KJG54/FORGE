"""M6 performance budgets and deterministic release-review scenarios."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter_ns
from typing import NoReturn, cast
from uuid import UUID

from forge import __version__
from forge.contracts.actors import Actor, ActorType
from forge.contracts.events import AuditEvent
from forge.core.archival import abandon_initiative
from forge.core.authorization import owner_actor
from forge.core.decisions import record_decision
from forge.core.lifecycle import create_initiative
from forge.storage.journal import read_journal, render_event, seal_event
from forge.storage.repository import RepositoryLayout, initialize_repository

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "release" / "performance-budgets.json"
INSTALLATION_MATRIX = ROOT / "release" / "installation-matrix.json"
CASE_IDS = {
    "startup",
    "status",
    "journal_replay",
    "context_generation",
    "archive_access",
}
OS_IDS = {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}


class PerformanceReviewError(RuntimeError):
    """A performance policy, fixture, measurement, or budget failed."""


@dataclass(frozen=True)
class MeasurementPolicy:
    warmups: int
    samples: int
    percentile: int
    timeout_seconds: int


@dataclass(frozen=True)
class WorkloadPolicy:
    archive_count: int
    decision_count: int
    journal_event_count: int


@dataclass(frozen=True)
class CasePolicy:
    case_id: str
    description: str
    iterations_per_sample: int
    budgets_ms: dict[str, float]


@dataclass(frozen=True)
class PerformancePolicy:
    python_implementation: str
    python_versions: tuple[str, ...]
    operating_systems: tuple[str, ...]
    measurement: MeasurementPolicy
    workload: WorkloadPolicy
    cases: dict[str, CasePolicy]


@dataclass(frozen=True)
class PerformanceFixture:
    layout: RepositoryLayout
    archive_ids: tuple[UUID, ...]
    journal_path: Path


def _fail(message: str) -> NoReturn:
    raise PerformanceReviewError(message)


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail(f"{label} must be a JSON object")
    untyped = cast("dict[object, object]", value)
    if any(not isinstance(key, str) for key in untyped):
        _fail(f"{label} keys must be strings")
    return cast("dict[str, object]", value)


def _exact_keys(value: dict[str, object], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        _fail(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def _positive_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        _fail(f"{label} must be a positive integer")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{label} must be non-empty text")
    return value


def _text_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        _fail(f"{label} must be a non-empty JSON array")
    result = tuple(_text(item, f"{label} item") for item in cast("list[object]", value))
    if len(result) != len(set(result)):
        _fail(f"{label} entries must be unique")
    return result


def _budget_map(value: object, systems: tuple[str, ...], label: str) -> dict[str, float]:
    document = _object(value, label)
    if set(document) != set(systems):
        _fail(f"{label} must define exactly {sorted(systems)}")
    budgets: dict[str, float] = {}
    for system in systems:
        budget = document[system]
        if (
            not isinstance(budget, (int, float))
            or isinstance(budget, bool)
            or budget <= 0
        ):
            _fail(f"{label}.{system} must be a positive number")
        budgets[system] = float(budget)
    return budgets


def load_policy(path: Path = DEFAULT_POLICY) -> PerformancePolicy:
    """Load a strict performance policy without interpreting executable data."""

    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PerformanceReviewError(f"Cannot load performance policy {path}: {error}") from error
    document = _object(value, "performance policy")
    _exact_keys(
        document,
        {
            "schema_version",
            "python_implementation",
            "python_versions",
            "operating_systems",
            "measurement",
            "workload",
            "cases",
        },
        "performance policy",
    )
    if document["schema_version"] != 1:
        _fail("Performance policy schema_version must equal 1")
    python_versions = _text_tuple(document["python_versions"], "python_versions")
    operating_systems = _text_tuple(
        document["operating_systems"],
        "operating_systems",
    )
    if set(operating_systems) != {"linux", "macos", "windows"}:
        _fail("operating_systems must be exactly linux, macos, and windows")

    measurement_document = _object(document["measurement"], "measurement")
    _exact_keys(
        measurement_document,
        {"clock", "warmups", "samples", "percentile", "timeout_seconds"},
        "measurement",
    )
    if measurement_document["clock"] != "perf_counter_ns":
        _fail("The measurement clock must be perf_counter_ns")
    measurement = MeasurementPolicy(
        warmups=_positive_int(measurement_document["warmups"], "measurement.warmups"),
        samples=_positive_int(measurement_document["samples"], "measurement.samples"),
        percentile=_positive_int(
            measurement_document["percentile"],
            "measurement.percentile",
        ),
        timeout_seconds=_positive_int(
            measurement_document["timeout_seconds"],
            "measurement.timeout_seconds",
        ),
    )
    if measurement.samples < 20:
        _fail("Performance measurement requires at least 20 samples")
    if measurement.percentile != 95:
        _fail("Performance budgets must use the p95 statistic")

    workload_document = _object(document["workload"], "workload")
    _exact_keys(
        workload_document,
        {"archive_count", "decision_count", "journal_event_count"},
        "workload",
    )
    workload = WorkloadPolicy(
        archive_count=_positive_int(
            workload_document["archive_count"],
            "workload.archive_count",
        ),
        decision_count=_positive_int(
            workload_document["decision_count"],
            "workload.decision_count",
        ),
        journal_event_count=_positive_int(
            workload_document["journal_event_count"],
            "workload.journal_event_count",
        ),
    )

    cases_document = _object(document["cases"], "cases")
    if set(cases_document) != CASE_IDS:
        _fail(f"Performance cases must be exactly {sorted(CASE_IDS)}")
    cases: dict[str, CasePolicy] = {}
    for case_id in sorted(CASE_IDS):
        case_document = _object(cases_document[case_id], f"cases.{case_id}")
        _exact_keys(
            case_document,
            {"description", "iterations_per_sample", "budget_ms"},
            f"cases.{case_id}",
        )
        cases[case_id] = CasePolicy(
            case_id=case_id,
            description=_text(
                case_document["description"],
                f"cases.{case_id}.description",
            ),
            iterations_per_sample=_positive_int(
                case_document["iterations_per_sample"],
                f"cases.{case_id}.iterations_per_sample",
            ),
            budgets_ms=_budget_map(
                case_document["budget_ms"],
                operating_systems,
                f"cases.{case_id}.budget_ms",
            ),
        )
    return PerformancePolicy(
        python_implementation=_text(
            document["python_implementation"],
            "python_implementation",
        ),
        python_versions=python_versions,
        operating_systems=operating_systems,
        measurement=measurement,
        workload=workload,
        cases=cases,
    )


def validate_policy_against_installation_matrix(
    policy: PerformancePolicy,
    path: Path = INSTALLATION_MATRIX,
) -> None:
    """Require performance environments to equal the installation support matrix."""

    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
        matrix = _object(value, "installation matrix")
        systems_value = matrix["operating_systems"]
        if not isinstance(systems_value, list):
            _fail("installation matrix operating_systems must be a list")
        systems = tuple(
            _text(
                _object(item, "installation matrix operating system")["id"],
                "installation matrix operating system id",
            )
            for item in cast("list[object]", systems_value)
        )
        python_versions = tuple(
            _text(item, "installation matrix Python version")
            for item in cast("list[object]", matrix["python_versions"])
        )
        implementation = _text(
            matrix["python_implementation"],
            "installation matrix Python implementation",
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise PerformanceReviewError(
            f"Cannot compare the installation matrix: {error}"
        ) from error
    if (
        policy.python_implementation != implementation
        or policy.python_versions != python_versions
        or policy.operating_systems != systems
    ):
        _fail("Performance environments do not match the installation matrix")


def platform_id(system: str | None = None) -> str:
    detected = platform.system() if system is None else system
    try:
        return OS_IDS[detected]
    except KeyError as error:
        raise PerformanceReviewError(
            f"Unsupported performance operating system: {detected}"
        ) from error


def validate_current_environment(policy: PerformancePolicy) -> tuple[str, str]:
    implementation = platform.python_implementation()
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    system = platform_id()
    if implementation != policy.python_implementation:
        _fail(
            f"Performance review requires {policy.python_implementation}, found {implementation}"
        )
    if version not in policy.python_versions:
        _fail(f"Python {version} is outside the performance support matrix")
    if system not in policy.operating_systems:
        _fail(f"Operating system {system} is outside the performance support matrix")
    return system, version


def _synthetic_actor() -> Actor:
    return Actor(
        id=UUID("00000000-0000-4000-8000-000000000001"),
        actor_type=ActorType.FORGE_CLI,
        display_label="Synthetic performance fixture",
    )


def create_synthetic_journal(path: Path, event_count: int) -> None:
    """Create a deterministic valid hash chain used only for replay measurement."""

    initiative_id = UUID("00000000-0000-4000-8000-000000000002")
    actor = _synthetic_actor()
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    previous_hash: str | None = None
    rendered: list[bytes] = []
    for sequence in range(1, event_count + 1):
        event = AuditEvent(
            id=UUID(int=sequence),
            initiative_id=initiative_id,
            sequence=sequence,
            timestamp=timestamp,
            event_type="performance-probe",
            actor=actor,
            authorization_basis="synthetic M6 replay measurement only",
            metadata={"sequence": sequence},
        )
        sealed = seal_event(event, previous_hash)
        assert sealed.event_hash is not None
        previous_hash = sealed.event_hash
        rendered.append(render_event(sealed))
    path.write_bytes(b"".join(rendered))
    if len(read_journal(path)) != event_count:
        _fail("Synthetic performance journal did not validate")


def create_repository_fixture(
    root: Path,
    *,
    archive_count: int,
    decision_count: int,
    journal_event_count: int,
) -> PerformanceFixture:
    """Create real validated archives and active records for maintained measurements."""

    initialized = initialize_repository(root, owner_display_name="Performance Review Owner")
    actor = owner_actor(initialized.configuration.owner)
    predecessor_ids: tuple[UUID, ...] = ()
    archives: list[UUID] = []
    for index in range(archive_count):
        created = create_initiative(
            initialized.layout,
            objective=f"Synthetic archived performance initiative {index + 1}",
            declared_scope_summary="Synthetic performance review scope only",
            actor=actor,
            trust_pack_data=True,
            predecessor_ids=predecessor_ids,
        )
        initiative_id = created.active.initiative.id
        abandon_initiative(
            initialized.layout,
            reason="Create a bounded archive-access performance fixture",
            unfinished_work_summary="All synthetic workflow steps remain unfinished",
            unresolved_risks=("Synthetic work has no accepted outcome",),
            actor=actor,
        )
        archives.append(initiative_id)
        predecessor_ids = (initiative_id,)

    create_initiative(
        initialized.layout,
        objective="Synthetic active performance initiative",
        declared_scope_summary="Measure maintained read and derived-context paths only",
        actor=actor,
        trust_pack_data=True,
        predecessor_ids=predecessor_ids,
    )
    for index in range(decision_count):
        record_decision(
            initialized.layout,
            decision_type="performance-choice",
            question=f"Synthetic performance decision {index + 1}?",
            considered_options=("retain", "replace"),
            chosen_outcome="retain",
            rationale="Create a maintained open-decision context workload",
            actor=actor,
        )

    journal_path = root / "synthetic-performance-journal.jsonl"
    create_synthetic_journal(journal_path, journal_event_count)
    return PerformanceFixture(
        layout=initialized.layout,
        archive_ids=tuple(archives),
        journal_path=journal_path,
    )


def nearest_rank_percentile(values: Sequence[float], percentile: int) -> float:
    """Return the nearest-rank percentile for a non-empty measurement sample."""

    if not values:
        _fail("Cannot calculate a percentile from no values")
    if percentile < 1 or percentile > 100:
        _fail("Percentile must be between 1 and 100")
    ordered = sorted(values)
    rank = math.ceil((percentile / 100) * len(ordered))
    return ordered[rank - 1]


def measure_operation(
    operation: Callable[[], None],
    *,
    warmups: int,
    samples: int,
    iterations_per_sample: int,
) -> tuple[float, ...]:
    """Measure average milliseconds per operation using a monotonic high-resolution clock."""

    for _ in range(warmups):
        operation()
    results: list[float] = []
    for _ in range(samples):
        started = perf_counter_ns()
        for _ in range(iterations_per_sample):
            operation()
        elapsed = perf_counter_ns() - started
        results.append(elapsed / 1_000_000 / iterations_per_sample)
    return tuple(results)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "NO_COLOR": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def _cli_operation(
    executable: Path,
    arguments: Sequence[str | Path],
    *,
    cwd: Path,
    expected_output: str,
    timeout_seconds: int,
) -> Callable[[], None]:
    command = [str(executable), *(str(item) for item in arguments)]
    environment = _environment()

    def operation() -> None:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            shell=False,
            timeout=timeout_seconds,
        )
        if result.returncode != 0:
            _fail(
                f"Performance command exited with {result.returncode}: "
                f"{subprocess.list2cmdline(command)}"
            )
        if expected_output not in result.stdout:
            _fail(
                f"Performance command omitted {expected_output!r}: "
                f"{subprocess.list2cmdline(command)}"
            )

    return operation


def _case_result(
    case: CasePolicy,
    measurements: tuple[float, ...],
    *,
    system: str,
    percentile: int,
) -> dict[str, object]:
    p95 = nearest_rank_percentile(measurements, percentile)
    budget = case.budgets_ms[system]
    return {
        "description": case.description,
        "iterations_per_sample": case.iterations_per_sample,
        "samples_ms": [round(item, 3) for item in measurements],
        "minimum_ms": round(min(measurements), 3),
        "median_ms": round(nearest_rank_percentile(measurements, 50), 3),
        "p95_ms": round(p95, 3),
        "maximum_ms": round(max(measurements), 3),
        "budget_ms": budget,
        "status": "passed" if p95 <= budget else "failed",
    }


def run_review(
    policy: PerformancePolicy,
    *,
    forge_executable: Path,
) -> dict[str, object]:
    """Build fresh fixtures, measure every maintained path, and enforce p95 budgets."""

    validate_policy_against_installation_matrix(policy)
    system, python_version = validate_current_environment(policy)
    executable = forge_executable.resolve(strict=True)
    if not executable.is_file():
        _fail(f"FORGE executable is not a regular file: {executable}")
    version_check = _cli_operation(
        executable,
        ("--version",),
        cwd=ROOT,
        expected_output=__version__,
        timeout_seconds=policy.measurement.timeout_seconds,
    )
    version_check()

    with tempfile.TemporaryDirectory(prefix="forge-performance-review-") as temporary:
        fixture = create_repository_fixture(
            Path(temporary),
            archive_count=policy.workload.archive_count,
            decision_count=policy.workload.decision_count,
            journal_event_count=policy.workload.journal_event_count,
        )
        selected_archive = fixture.archive_ids[-1]
        operations: dict[str, Callable[[], None]] = {
            "startup": version_check,
            "status": _cli_operation(
                executable,
                ("status", "-C", fixture.layout.root),
                cwd=fixture.layout.root,
                expected_output="Integrity: healthy",
                timeout_seconds=policy.measurement.timeout_seconds,
            ),
            "journal_replay": lambda: _require_journal_count(
                fixture.journal_path,
                policy.workload.journal_event_count,
            ),
            "context_generation": _cli_operation(
                executable,
                ("agent", "context", "-C", fixture.layout.root),
                cwd=fixture.layout.root,
                expected_output="Generated neutral canonical agent context",
                timeout_seconds=policy.measurement.timeout_seconds,
            ),
            "archive_access": _cli_operation(
                executable,
                (
                    "status",
                    "--archive",
                    str(selected_archive),
                    "-C",
                    fixture.layout.root,
                ),
                cwd=fixture.layout.root,
                expected_output=f"Archive: .forge/archive/{selected_archive}",
                timeout_seconds=policy.measurement.timeout_seconds,
            ),
        }
        cases: dict[str, dict[str, object]] = {}
        for case_id in (
            "startup",
            "status",
            "journal_replay",
            "context_generation",
            "archive_access",
        ):
            case = policy.cases[case_id]
            measured = measure_operation(
                operations[case_id],
                warmups=policy.measurement.warmups,
                samples=policy.measurement.samples,
                iterations_per_sample=case.iterations_per_sample,
            )
            cases[case_id] = _case_result(
                case,
                measured,
                system=system,
                percentile=policy.measurement.percentile,
            )

    failed = tuple(case_id for case_id, result in cases.items() if result["status"] == "failed")
    return {
        "schema_version": 1,
        "status": "passed" if not failed else "failed",
        "environment": {
            "operating_system": system,
            "python_implementation": policy.python_implementation,
            "python_version": python_version,
            "forge_version": __version__,
        },
        "measurement": {
            "clock": "perf_counter_ns",
            "warmups": policy.measurement.warmups,
            "samples": policy.measurement.samples,
            "percentile": policy.measurement.percentile,
        },
        "workload": {
            "archive_count": policy.workload.archive_count,
            "decision_count": policy.workload.decision_count,
            "journal_event_count": policy.workload.journal_event_count,
        },
        "cases": cases,
        "failed_cases": failed,
        "limitations": [
            "Elapsed time includes ordinary host scheduling and filesystem behavior.",
            "A local pass establishes only this exact environment and executable.",
            "Budgets detect release-blocking regressions; they are not real-time guarantees.",
            "Every supported platform and Python version must repeat the review at M6 closeout.",
        ],
    }


def _require_journal_count(path: Path, expected: int) -> None:
    if len(read_journal(path)) != expected:
        _fail(f"Journal replay did not return {expected} events")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure maintained FORGE release-candidate performance budgets."
    )
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument(
        "--forge",
        type=Path,
        default=Path(shutil.which("forge") or "forge"),
        help="Exact FORGE console executable to measure.",
    )
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        policy = load_policy(arguments.policy.resolve(strict=True))
        report = run_review(policy, forge_executable=arguments.forge)
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if arguments.output is None:
            sys.stdout.write(rendered)
        else:
            output = arguments.output.resolve()
            if output.exists():
                _fail(f"Refusing to overwrite performance report: {output}")
            output.write_text(rendered, encoding="utf-8")
        if report["status"] != "passed":
            print(
                f"performance review exceeded budgets: {report['failed_cases']}",
                file=sys.stderr,
            )
            return 1
    except (OSError, PerformanceReviewError, subprocess.TimeoutExpired) as error:
        print(f"performance review failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
