from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from forge.contracts.actors import ActorType
from forge.contracts.state import StepState
from forge.core.artifacts import list_artifacts
from forge.core.lifecycle import load_active_initiative
from forge.packs.loader import load_pack
from forge.storage.repository import RepositoryLayout

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = PROJECT_ROOT / "src" / "forge" / "packs" / "bundled" / "research-basic"

RESEARCH_STEPS = (
    (
        "frame",
        ("research-question", "research-boundaries"),
        "framing-structure-reviewed",
    ),
    (
        "plan",
        ("research-plan", "evidence-criteria"),
        "plan-structure-reviewed",
    ),
    (
        "collect",
        ("source-register", "research-notes"),
        "evidence-register-structure-reviewed",
    ),
    (
        "synthesize",
        ("synthesis-draft", "claims-evidence-map", "limitations"),
        "synthesis-traceability-reviewed",
    ),
    (
        "verify",
        ("research-verification-report",),
        "verification-structure-reviewed",
    ),
    ("review", ("research-review",), "review-complete"),
    ("close", ("lessons", "closure-record"), "closure-readiness"),
)


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


def _current_revision_ids(
    repository: Path,
    roles: tuple[str, ...],
) -> tuple[str, ...]:
    by_role = {
        view.artifact.role: view.current_revision.id
        for view in list_artifacts(RepositoryLayout.at(repository))
    }
    return tuple(str(by_role[role]) for role in roles)


def _advance_research_step(
    repository: Path,
    *,
    step_id: str,
    outputs: tuple[str, ...],
    check_id: str,
) -> None:
    _run(repository, "begin", step_id)
    for role in outputs:
        path = repository / f"{role}.md"
        path.write_text(
            f"# {role}\n\nStructural M5 research acceptance content.\n",
            encoding="utf-8",
        )
        _run(
            repository,
            "artifact",
            "add",
            path.name,
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
        f"Declared research outputs for {step_id} were produced",
        "--limitation",
        "The worker claim does not establish factual truth",
    )
    claim_id = _value(claim_output, "Recorded claim ")
    check_output = _run(
        repository,
        "check",
        "record",
        step_id,
        check_id,
        "--invocation",
        f"manual structural review of {step_id}",
        "--outcome",
        "passed",
        "--exit-status",
        "0",
        "--limitation",
        "Structure and presence do not establish factual correctness",
    )
    check_id_value = _value(check_output, "Recorded check result ").split(":", 1)[0]
    evidence_arguments = [
        "evidence",
        "add",
        step_id,
        "--purpose",
        f"Bind current structural support for {step_id}",
        "--check-result",
        check_id_value,
        "--claim",
        claim_id,
        "--limitation",
        "Governed support does not establish source quality or factual truth",
    ]
    for revision_id in _current_revision_ids(repository, outputs):
        evidence_arguments.extend(("--artifact-revision", revision_id))
    _run(repository, *evidence_arguments)
    _run(repository, "verify", step_id)
    _run(
        repository,
        "acceptance",
        "record",
        step_id,
        "--scope",
        f"Exact current {step_id} research outputs",
        "--known-limitation",
        "Structural acceptance is not automated factual validation",
        "--residual-risk",
        "Sources or conclusions may still be incomplete or incorrect",
    )


def test_bundled_research_pack_is_complete_data_only_and_digest_valid() -> None:
    pack = load_pack(PACK_ROOT, bundled=True)
    workflow = pack.workflow()

    assert pack.manifest.id == "research-basic"
    assert pack.manifest.version == "0.2.0"
    assert pack.manifest.template_paths == (
        "templates/research-evidence-register.md",
        "templates/research-citation-record.md",
    )
    assert pack.manifest.explanation_paths == ()
    assert pack.manifest.data_resource_paths == ()
    assert pack.manifest.declared_capability_ids == ()
    assert workflow.id == "research-basic"
    assert [step.id for step in workflow.steps] == [
        "frame",
        "plan",
        "collect",
        "synthesize",
        "verify",
        "review",
        "close",
    ]
    assert all(
        ActorType.AGENT_ADAPTER in step.allowed_actors for step in workflow.steps
    )
    assert all("software" not in role for role in workflow.required_artifact_classes)
    assert {"standard", "guided"} <= set(workflow.explanation_content)
    assert all(
        "review" in check_id or check_id == "closure-readiness"
        for step in workflow.steps
        for check_id in step.check_requirements
    )


def test_research_pack_completes_through_restarted_unchanged_core(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "research"
    repository.mkdir()
    _run(repository, "init", str(repository), "--owner-name", "Research Owner")
    assert "research-basic 0.2.0" in _run(repository, "pack", "list")
    assert "Valid data pack research-basic 0.2.0" in _run(
        repository,
        "pack",
        "validate",
        "research-basic",
    )
    _run(
        repository,
        "create",
        "Answer one bounded research question",
        "--scope",
        "Structural research workflow acceptance only",
        "--pack",
        "research-basic",
        "--trust-pack-data",
    )

    for step_id, outputs, check_id in RESEARCH_STEPS:
        _advance_research_step(
            repository,
            step_id=step_id,
            outputs=outputs,
            check_id=check_id,
        )

    active = load_active_initiative(RepositoryLayout.at(repository))
    assert active.pack_manifest.id == "research-basic"
    assert active.workflow.id == "research-basic"
    assert all(state is StepState.COMPLETED for state in active.state.step_states.values())
    assert "Integrity: healthy" in _run(repository, "status")

    close_output = _run(
        repository,
        "close",
        "--summary",
        "M5 Increment 1 research workflow acceptance complete",
    )
    initiative_id = _value(close_output, "Closed initiative ")
    archive_status = _run(repository, "status", "--archive", initiative_id)
    assert "Lifecycle: closed" in archive_status
    assert "Archive guarantee: atomic M2" in archive_status
    _run(repository, "doctor")
