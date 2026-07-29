"""Rehearse both bundled workflows in fresh copies of the static examples."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = PROJECT_ROOT / "examples"


class ExampleSmokeError(RuntimeError):
    """An example precondition or governed CLI command failed."""


@dataclass(frozen=True)
class StepScenario:
    """One fixed example workflow step."""

    step_id: str
    outputs: tuple[str, ...]
    checks: tuple[str, ...]


@dataclass(frozen=True)
class ExampleScenario:
    """One static example repository and its expected workflow."""

    example_id: str
    pack_id: str
    objective: str
    scope: str
    steps: tuple[StepScenario, ...]


SOFTWARE_SCENARIO = ExampleScenario(
    example_id="software",
    pack_id="software-basic",
    objective="Define a deterministic release-note formatter",
    scope="Document and review a bounded formatter design",
    steps=(
        StepScenario(
            "discover",
            ("objective-and-constraints", "requirements"),
            ("outputs-present",),
        ),
        StepScenario("plan", ("implementation-plan",), ("outputs-present",)),
        StepScenario("execute", ("project-artifacts",), ("declared-checks",)),
        StepScenario("verify", ("verification-report",), ("declared-checks",)),
        StepScenario("review", ("review-report",), ("review-complete",)),
        StepScenario(
            "close",
            ("lessons", "closure-record"),
            ("closure-readiness",),
        ),
    ),
)
RESEARCH_SCENARIO = ExampleScenario(
    example_id="research",
    pack_id="research-basic",
    objective="Compare two structures for a monthly volunteer update",
    scope="Use synthetic local evidence to demonstrate traceable research governance",
    steps=(
        StepScenario(
            "frame",
            ("research-question", "research-boundaries"),
            ("framing-structure-reviewed",),
        ),
        StepScenario(
            "plan",
            ("research-plan", "evidence-criteria"),
            ("plan-structure-reviewed",),
        ),
        StepScenario(
            "collect",
            ("source-register", "research-notes"),
            ("evidence-register-structure", "citation-record-structure"),
        ),
        StepScenario(
            "synthesize",
            ("synthesis-draft", "claims-evidence-map", "limitations"),
            ("synthesis-traceability-reviewed",),
        ),
        StepScenario(
            "verify",
            ("research-verification-report",),
            ("verification-structure-reviewed",),
        ),
        StepScenario("review", ("research-review",), ("review-complete",)),
        StepScenario(
            "close",
            ("lessons", "closure-record"),
            ("closure-readiness",),
        ),
    ),
)
SCENARIOS: Mapping[str, ExampleScenario] = {
    SOFTWARE_SCENARIO.example_id: SOFTWARE_SCENARIO,
    RESEARCH_SCENARIO.example_id: RESEARCH_SCENARIO,
}


def _fail(message: str) -> NoReturn:
    raise ExampleSmokeError(message)


def _value(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            value = line.removeprefix(prefix).strip()
            if value:
                return value
    _fail(f"Command output did not contain a value after {prefix!r}")


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


def _run_cli(
    executable: Path,
    repository: Path,
    arguments: Sequence[str | Path],
    *,
    initialize: bool = False,
) -> str:
    command = [str(executable), *(str(argument) for argument in arguments)]
    if not initialize:
        command.extend(("-C", str(repository)))
    result = subprocess.run(
        command,
        cwd=repository,
        env=_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        shell=False,
    )
    if result.returncode != 0:
        _fail(
            f"Command exited with status {result.returncode}: "
            f"{subprocess.list2cmdline(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


def _register_artifact(
    executable: Path,
    repository: Path,
    role: str,
) -> str:
    relative_path = Path("artifacts") / f"{role}.md"
    if not (repository / relative_path).is_file():
        _fail(f"Example output is missing: {relative_path.as_posix()}")
    output = _run_cli(
        executable,
        repository,
        (
            "artifact",
            "add",
            relative_path,
            "--role",
            role,
            "--title",
            role.replace("-", " ").title(),
            "--media-type",
            "text/markdown",
        ),
    )
    return _value(output, "Revision ID: ")


def _record_check(
    executable: Path,
    repository: Path,
    *,
    scenario: ExampleScenario,
    step: StepScenario,
    check_id: str,
) -> str:
    output = _run_cli(
        executable,
        repository,
        (
            "check",
            "record",
            step.step_id,
            check_id,
            "--invocation",
            f"synthetic {scenario.example_id} example review",
            "--outcome",
            "passed",
            "--exit-status",
            "0",
            "--limitation",
            "Example structure and presence do not establish production or factual correctness",
        ),
    )
    return _value(output, "Recorded check result ").split(":", 1)[0]


def _advance_step(
    executable: Path,
    repository: Path,
    scenario: ExampleScenario,
    step: StepScenario,
) -> None:
    print(f"[{scenario.example_id}] {step.step_id}", flush=True)
    _run_cli(executable, repository, ("begin", step.step_id))
    revision_ids = tuple(
        _register_artifact(executable, repository, role) for role in step.outputs
    )
    claim_output = _run_cli(
        executable,
        repository,
        (
            "complete",
            step.step_id,
            "--assertion",
            f"Declared {scenario.example_id} example outputs for {step.step_id} were produced",
            "--limitation",
            "The synthetic rehearsal claim does not establish production or factual correctness",
        ),
    )
    claim_id = _value(claim_output, "Recorded claim ")
    check_result_ids = tuple(
        _record_check(
            executable,
            repository,
            scenario=scenario,
            step=step,
            check_id=check_id,
        )
        for check_id in step.checks
    )
    evidence_arguments: list[str] = [
        "evidence",
        "add",
        step.step_id,
        "--purpose",
        f"Bind the synthetic {scenario.example_id} example support for {step.step_id}",
        "--claim",
        claim_id,
        "--limitation",
        "This packet supports only the temporary example rehearsal",
    ]
    for check_result_id in check_result_ids:
        evidence_arguments.extend(("--check-result", check_result_id))
    for revision_id in revision_ids:
        evidence_arguments.extend(("--artifact-revision", revision_id))
    _run_cli(executable, repository, evidence_arguments)
    _run_cli(executable, repository, ("verify", step.step_id))
    _run_cli(
        executable,
        repository,
        (
            "acceptance",
            "record",
            step.step_id,
            "--scope",
            f"Exact temporary {scenario.example_id} example outputs for {step.step_id}",
            "--known-limitation",
            "Synthetic example acceptance does not apply to real work",
            "--residual-risk",
            "The example omits production and factual validation",
        ),
    )


def run_example(
    executable: Path,
    scenario: ExampleScenario,
    scratch_root: Path,
) -> dict[str, object]:
    """Copy, complete, close, and validate one example in an isolated scratch root."""
    source = EXAMPLES_ROOT / f"{scenario.example_id}-project"
    if not source.is_dir():
        _fail(f"Example source directory is missing: {source}")
    repository = scratch_root / f"{scenario.example_id}-project"
    shutil.copytree(source, repository)
    _run_cli(
        executable,
        repository,
        ("init", repository, "--owner-name", f"Example {scenario.example_id.title()} Owner"),
        initialize=True,
    )
    _run_cli(
        executable,
        repository,
        (
            "pack",
            "validate",
            scenario.pack_id,
        ),
    )
    _run_cli(
        executable,
        repository,
        (
            "create",
            scenario.objective,
            "--scope",
            scenario.scope,
            "--pack",
            scenario.pack_id,
            "--trust-pack-data",
        ),
    )
    for step in scenario.steps:
        _advance_step(executable, repository, scenario, step)
    status = _run_cli(executable, repository, ("status",))
    if "Integrity: healthy" not in status:
        _fail(f"{scenario.example_id} active status was not healthy")
    close_output = _run_cli(
        executable,
        repository,
        (
            "close",
            "--summary",
            f"Completed the temporary {scenario.example_id} example rehearsal",
        ),
    )
    initiative_id = _value(close_output, "Closed initiative ")
    archive_status = _run_cli(
        executable,
        repository,
        ("status", "--archive", initiative_id),
    )
    if "Lifecycle: closed" not in archive_status or "Integrity: healthy" not in archive_status:
        _fail(f"{scenario.example_id} archive status was not closed and healthy")
    doctor = _run_cli(executable, repository, ("doctor",))
    if "FORGE repository health: healthy" not in doctor:
        _fail(f"{scenario.example_id} doctor result was not healthy")
    return {
        "archive_status": "healthy",
        "example": scenario.example_id,
        "pack": scenario.pack_id,
        "status": "passed",
        "steps": len(scenario.steps),
    }


def run_rehearsal(executable: Path, example_ids: Sequence[str]) -> tuple[dict[str, object], ...]:
    """Run selected examples only inside a new temporary directory."""
    resolved_executable = executable.resolve(strict=True)
    if not resolved_executable.is_file():
        _fail(f"FORGE executable is not a file: {resolved_executable}")
    with tempfile.TemporaryDirectory(prefix="forge-example-smoke-") as temporary:
        root = Path(temporary)
        return tuple(
            run_example(resolved_executable, SCENARIOS[example_id], root)
            for example_id in example_ids
        )


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Complete FORGE's static examples in temporary governed repositories.",
    )
    parser.add_argument(
        "--forge",
        type=Path,
        default=Path(shutil.which("forge") or "forge"),
        help="Exact installed forge console executable to exercise.",
    )
    parser.add_argument(
        "--example",
        choices=(*sorted(SCENARIOS), "all"),
        default="all",
        help="Example to rehearse; defaults to both.",
    )
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = parse_args(arguments)
    example_ids = tuple(sorted(SCENARIOS)) if args.example == "all" else (args.example,)
    try:
        results = run_rehearsal(args.forge, example_ids)
    except (ExampleSmokeError, OSError) as error:
        print(f"example workflow smoke failed: {error}", file=sys.stderr)
        return 1
    print(
        "FORGE_EXAMPLE_SMOKE="
        + json.dumps(results, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
