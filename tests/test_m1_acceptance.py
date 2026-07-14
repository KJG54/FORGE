from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from forge.contracts.actors import Actor, ActorType
from forge.contracts.agents import AgentResult, ReturnedFile
from forge.contracts.configuration import PackConfiguration
from forge.contracts.state import ExplanationProfile, StepState
from forge.core.artifacts import list_artifacts
from forge.core.lifecycle import load_active_initiative
from forge.core.runs import cancel_run
from forge.errors import AuthorizationError
from forge.storage.configuration import load_configuration, render_configuration
from forge.storage.records import render_record
from forge.storage.repository import RepositoryLayout

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_PACK = PROJECT_ROOT / "tests" / "fixtures" / "packs" / "community-research"


def _run(repository: Path, *arguments: str, expected: int = 0) -> str:
    environment = os.environ.copy()
    source = str(PROJECT_ROOT / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        item for item in (source, environment.get("PYTHONPATH", "")) if item
    )
    environment["PYTHONUTF8"] = "1"
    command = [sys.executable, "-m", "forge", *arguments]
    if not arguments or arguments[0] != "init":
        command.extend(("-C", str(repository)))
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert completed.returncode == expected, (
        f"command failed: forge {' '.join(arguments)}\n"
        f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
    return completed.stdout


def _value(output: str, prefix: str) -> str:
    return next(
        line.removeprefix(prefix)
        for line in output.splitlines()
        if line.startswith(prefix)
    )


def _init(repository: Path) -> None:
    repository.mkdir()
    _run(repository, "init", str(repository), "--owner-name", "Acceptance Owner")


def _revision_ids(repository: Path, roles: tuple[str, ...]) -> tuple[str, ...]:
    layout = RepositoryLayout.at(repository)
    by_role = {view.artifact.role: view.current_revision.id for view in list_artifacts(layout)}
    return tuple(str(by_role[role]) for role in roles)


def _advance(
    repository: Path,
    *,
    step_id: str,
    outputs: tuple[str, ...],
    check_id: str,
) -> None:
    _run(repository, "begin", step_id)
    existing = {view.artifact.role for view in list_artifacts(RepositoryLayout.at(repository))}
    for role in outputs:
        if role in existing:
            continue
        target = repository / f"{role}.md"
        target.write_text(f"# {role}\n\nAcceptance fixture content.\n", encoding="utf-8")
        _run(
            repository,
            "artifact",
            "add",
            target.name,
            "--role",
            role,
            "--title",
            role.replace("-", " ").title(),
            "--media-type",
            "text/markdown",
        )
    claim_output = _run(
        repository,
        "complete",
        step_id,
        "--assertion",
        f"Declared outputs for {step_id} are present",
    )
    claim_id = _value(claim_output, "Recorded claim ")
    check_output = _run(
        repository,
        "check",
        "record",
        step_id,
        check_id,
        "--invocation",
        f"manual acceptance review of {step_id}",
        "--outcome",
        "passed",
        "--exit-status",
        "0",
    )
    check_result_id = _value(check_output, "Recorded check result ").split(":", 1)[0]
    evidence_arguments = [
        "evidence",
        "add",
        step_id,
        "--purpose",
        f"Current governed support for {step_id}",
        "--check-result",
        check_result_id,
        "--claim",
        claim_id,
    ]
    for revision_id in _revision_ids(repository, outputs):
        evidence_arguments.extend(("--artifact-revision", revision_id))
    _run(repository, *evidence_arguments)
    _run(repository, "verify", step_id)
    _run(
        repository,
        "acceptance",
        "record",
        step_id,
        "--scope",
        f"Exact current {step_id} outputs",
        "--known-limitation",
        "Synthetic acceptance evidence",
    )


def _configure_synthetic_pack(repository: Path) -> None:
    target = repository / "test-packs" / "community-research"
    shutil.copytree(SYNTHETIC_PACK, target)
    layout = RepositoryLayout.at(repository)
    configuration = load_configuration(layout.configuration_file)
    configured = configuration.model_copy(
        update={"packs": PackConfiguration(local_paths=("test-packs/community-research",))}
    )
    layout.configuration_file.write_bytes(render_configuration(configured))


def test_restarted_process_software_walkthrough_with_import_revision_and_closure(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "software"
    _init(repository)
    _run(repository, "doctor")
    _run(
        repository,
        "create",
        "Deliver the bounded M1 acceptance fixture",
        "--scope",
        "Software-basic workflow acceptance only",
        "--trust-pack-data",
        "--explanation",
        "guided",
    )
    assert "Integrity: healthy" in _run(repository, "status")

    handoff_output = _run(
        repository,
        "handoff",
        "discover",
        "--constraint",
        "Return only declared discovery files",
    )
    handoff_id = UUID(_value(handoff_output, "Created handoff "))
    bundle = tmp_path / "software-result"
    bundle.mkdir()
    (bundle / "objective.md").write_text("# Objective\nBounded M1 acceptance.\n", encoding="utf-8")
    (bundle / "requirements.md").write_text("# Requirements\nNo M2 work.\n", encoding="utf-8")
    result = AgentResult(
        id=uuid4(),
        source_run_or_handoff_id=handoff_id,
        worker_claims=("Returned declared discovery files",),
        returned_files=(
            ReturnedFile(
                source_path="objective.md",
                proposed_target_path="objective.md",
                media_type="text/markdown",
            ),
            ReturnedFile(
                source_path="requirements.md",
                proposed_target_path="requirements.md",
                media_type="text/markdown",
            ),
        ),
        declared_limitations=("Untrusted fixture output",),
        tool_metadata={"fixture": "restarted-process"},
    )
    manifest = bundle / "result.json"
    manifest.write_bytes(render_record(result))
    import_arguments = (
        "import-result",
        str(manifest),
        "--role",
        "objective.md=objective-and-constraints",
        "--role",
        "requirements.md=requirements",
    )
    assert "Preview only" in _run(repository, *import_arguments)
    assert "remains subject to claims" in _run(repository, *import_arguments, "--apply")

    software_steps = (
        ("discover", ("objective-and-constraints", "requirements"), "outputs-present"),
        ("plan", ("implementation-plan",), "outputs-present"),
        ("execute", ("project-artifacts",), "declared-checks"),
        ("verify", ("verification-report",), "declared-checks"),
        ("review", ("review-report",), "review-complete"),
        ("close", ("lessons", "closure-record"), "closure-readiness"),
    )
    _advance(
        repository,
        step_id="discover",
        outputs=("objective-and-constraints", "requirements"),
        check_id="outputs-present",
    )
    requirements = next(
        view for view in list_artifacts(RepositoryLayout.at(repository))
        if view.artifact.role == "requirements"
    )
    (repository / "requirements.md").write_text(
        "# Requirements\nNo M2 work; restarted-process evidence required.\n",
        encoding="utf-8",
    )
    revised = _run(
        repository,
        "artifact",
        "revise",
        str(requirements.artifact.id),
        "requirements.md",
    )
    assert "Stale dependency effects:" in revised
    assert "Step discover: invalidated" in _run(repository, "status")
    _advance(
        repository,
        step_id="discover",
        outputs=("objective-and-constraints", "requirements"),
        check_id="outputs-present",
    )
    for step_id, outputs, check_id in software_steps[1:]:
        _advance(repository, step_id=step_id, outputs=outputs, check_id=check_id)
    assert "status=succeeded" in _run(repository, "run", "list")
    close_output = _run(repository, "close", "--summary", "M1 acceptance fixture complete")
    initiative_id = UUID(_value(close_output, "Closed initiative "))
    archive_status = _run(repository, "status", "--archive", str(initiative_id))
    assert "Lifecycle: closed" in archive_status
    assert "Archive guarantee: preliminary M1" in archive_status
    assert "initiative-closed" in _run(
        repository, "history", "--archive", str(initiative_id), "--event-type", "initiative-closed"
    )
    _run(repository, "doctor")


def test_synthetic_nonsoftware_pack_uses_unchanged_core_services(tmp_path: Path) -> None:
    repository = tmp_path / "research"
    _init(repository)
    _configure_synthetic_pack(repository)
    assert "community-research-test" in _run(repository, "pack", "list")
    _run(repository, "pack", "validate", "community-research-test")
    _run(
        repository,
        "create",
        "Understand a bounded community question",
        "--scope",
        "Synthetic non-identifying observations only",
        "--pack",
        "community-research-test",
        "--trust-pack-data",
    )
    steps = (
        ("frame", ("question-brief", "participation-boundaries"), "framing-reviewed"),
        ("gather", ("observation-log",), "observations-reviewed"),
        ("synthesize", ("findings-summary", "limitations-note"), "synthesis-reviewed"),
    )
    for step_id, outputs, check_id in steps:
        _advance(repository, step_id=step_id, outputs=outputs, check_id=check_id)
    active = load_active_initiative(RepositoryLayout.at(repository))
    assert active.workflow.pack_id == "community-research-test"
    assert all(state is StepState.COMPLETED for state in active.state.step_states.values())
    assert not any("software" in role for role in active.workflow.required_artifact_classes)
    _run(repository, "close", "--summary", "Synthetic community research fixture complete")


def test_diagnostics_profiles_and_cancellation_are_bounded_m1_behaviors(
    tmp_path: Path,
) -> None:
    standard = tmp_path / "standard"
    guided = tmp_path / "guided"
    for repository, profile in (
        (standard, ExplanationProfile.STANDARD),
        (guided, ExplanationProfile.GUIDED),
    ):
        _init(repository)
        output = _run(
            repository,
            "create",
            "Profile equivalence",
            "--scope",
            "Presentation-only comparison",
            "--trust-pack-data",
            "--explanation",
            profile.value,
        )
        assert f"Guidance ({profile.value})" in output
        _run(repository, "doctor")
    standard_active = load_active_initiative(RepositoryLayout.at(standard))
    guided_active = load_active_initiative(RepositoryLayout.at(guided))
    assert standard_active.state.step_states == guided_active.state.step_states
    assert (
        standard_active.state.permitted_next_actions
        == guided_active.state.permitted_next_actions
    )
    assert standard_active.workflow.transitions == guided_active.workflow.transitions

    begun = _run(standard, "begin", "discover", "--side-effect", "read_only")
    run_id = UUID(_value(begun, "Started manual run ").split(" ", 1)[0])
    assert "status=running" in _run(standard, "run", "list")
    assert "Status: running" in _run(standard, "run", "show", str(run_id))
    with pytest.raises(AuthorizationError, match="run worker or repository owner"):
        cancel_run(
            RepositoryLayout.at(standard),
            run_id=run_id,
            reason="Unauthorized cancellation",
            actor=Actor(
                id=uuid4(),
                actor_type=ActorType.AGENT_ADAPTER,
                display_label="Other agent",
            ),
        )
    cancelled = _run(
        standard,
        "run",
        "cancel",
        str(run_id),
        "--reason",
        "Fixture cancellation",
    )
    assert "Step discover: ready" in cancelled
    assert "Status: cancelled" in _run(standard, "run", "show", str(run_id))
    assert "Step discover: ready" in _run(standard, "status")

    risky = _run(guided, "begin", "discover", "--side-effect", "external_reversible")
    risky_id = UUID(_value(risky, "Started manual run ").split(" ", 1)[0])
    blocked = _run(
        guided,
        "run",
        "cancel",
        str(risky_id),
        "--reason",
        "External state may require review",
    )
    assert "Step discover: blocked" in blocked
    assert "Step discover: blocked" in _run(guided, "status")
