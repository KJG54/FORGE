from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.artifacts import ArtifactRevision
from forge.contracts.verification import CheckOutcome
from forge.core import context_discovery
from forge.core.acceptance import record_acceptance
from forge.core.artifacts import ArtifactMutationResult, add_artifact
from forge.core.authorization import owner_actor
from forge.core.context_discovery import (
    CONTEXT_DISCOVERY_PROFILE,
    ContextSufficiencyStatus,
    discover_context,
    measure_discovery_sufficiency,
)
from forge.core.lifecycle import begin_manual_run, create_initiative
from forge.core.verification import (
    complete_step,
    record_check,
    record_evidence,
    verify_step,
)
from forge.storage.repository import (
    InitializationResult,
    RepositoryLayout,
    initialize_repository,
)

runner = CliRunner()


def _initialize_git(root: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("Git is unavailable")
    completed = subprocess.run(
        ["git", "init", "--quiet"],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0:
        pytest.skip("Git worktree initialization is unavailable")


def _initiative(
    root: Path,
    *,
    objective: str,
    scope: str,
    pack_id: str = "software-basic",
    workflow_id: str | None = None,
    with_git: bool = True,
) -> InitializationResult:
    if with_git:
        _initialize_git(root)
    initialized = initialize_repository(root, owner_display_name="Discovery Owner")
    create_initiative(
        initialized.layout,
        objective=objective,
        declared_scope_summary=scope,
        actor=owner_actor(initialized.configuration.owner),
        pack_id=pack_id,
        workflow_id=workflow_id,
        trust_pack_data=True,
    )
    return initialized


def _advance_software_to_plan(initialized: InitializationResult) -> None:
    actor = owner_actor(initialized.configuration.owner)
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    artifacts: list[ArtifactMutationResult] = []
    for filename, role in (
        ("objective.md", "objective-and-constraints"),
        ("requirements.md", "requirements"),
    ):
        (initialized.layout.root / filename).write_text(
            f"# {role}\n\nBounded checkout implementation.\n",
            encoding="utf-8",
        )
        artifacts.append(
            add_artifact(
                initialized.layout,
                path=filename,
                role=role,
                title=role,
                actor=actor,
                media_type="text/markdown",
            )
        )
    claim = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Discovery outputs are registered",
        actor=actor,
    )
    check = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"method": "manual inspection"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
    )
    record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Bind the exact discovery outputs",
        actor=actor,
        artifact_revision_ids=tuple(item.revision.id for item in artifacts),
        check_result_ids=(check.check.id,),
        claim_ids=(claim.claim.id,),
    )
    verify_step(initialized.layout, step_id="discover")
    record_acceptance(
        initialized.layout,
        step_id="discover",
        accepted_scope="Exact discovery outputs",
        actor=actor,
    )


def test_software_discovery_is_bounded_safe_and_measurably_sufficient(
    tmp_path: Path,
) -> None:
    initialized = _initiative(
        tmp_path,
        objective="Build a payment checkout implementation",
        scope="Payment architecture and checkout requirements only",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "private").mkdir()
    (tmp_path / "docs" / "checkout-requirements.md").write_text(
        "RELEVANT_REQUIREMENTS_CONTENT_SENTINEL",
        encoding="utf-8",
    )
    (tmp_path / "src" / "payment-checkout.py").write_text(
        "RELEVANT_IMPLEMENTATION_CONTENT_SENTINEL",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "gardening-notes.md").write_text(
        "UNRELATED_CONTENT_SENTINEL",
        encoding="utf-8",
    )
    (tmp_path / "private" / "payment-secrets.md").write_text(
        "IGNORED_CONTENT_SENTINEL",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("SECRET_CONTENT_SENTINEL", encoding="utf-8")
    with (tmp_path / ".gitignore").open("a", encoding="utf-8") as stream:
        stream.write("/private/\n")
    journal_before = initialized.layout.event_journal_file.read_bytes()

    report = discover_context(initialized.layout)
    measurement = measure_discovery_sufficiency(
        report,
        expected_relevant_paths=(
            "docs/checkout-requirements.md",
            "src/payment-checkout.py",
        ),
    )

    assert report.profile == CONTEXT_DISCOVERY_PROFILE
    assert report.step_id == "discover"
    assert report.sufficiency_status is ContextSufficiencyStatus.SUFFICIENT
    assert report.ignore_policy_enforced
    assert not report.inventory_truncated
    assert report.ignored_file_count == 1
    assert report.policy_excluded_count >= 3
    assert measurement.sufficient
    assert measurement.precision == 1.0
    assert measurement.recall == 1.0
    assert measurement.missed_paths == ()
    assert tuple(item.path for item in report.candidates) == (
        "docs/checkout-requirements.md",
        "src/payment-checkout.py",
    )
    rendered = repr(report)
    for sentinel in (
        "RELEVANT_REQUIREMENTS_CONTENT_SENTINEL",
        "RELEVANT_IMPLEMENTATION_CONTENT_SENTINEL",
        "UNRELATED_CONTENT_SENTINEL",
        "IGNORED_CONTENT_SENTINEL",
        "SECRET_CONTENT_SENTINEL",
    ):
        assert sentinel not in rendered
    assert initialized.layout.event_journal_file.read_bytes() == journal_before


def test_research_discovery_uses_the_same_core_and_measured_boundary(
    tmp_path: Path,
) -> None:
    initialized = _initiative(
        tmp_path,
        objective="Research regional climate adaptation evidence",
        scope="Climate evidence and adaptation boundaries",
        pack_id="research-basic",
        workflow_id="research-basic",
    )
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "climate-evidence.md").write_text(
        "Evidence notes",
        encoding="utf-8",
    )
    (tmp_path / "research" / "adaptation-boundaries.md").write_text(
        "Research boundaries",
        encoding="utf-8",
    )
    (tmp_path / "research" / "cooking-log.md").write_text(
        "Unrelated notes",
        encoding="utf-8",
    )

    report = discover_context(initialized.layout)
    measurement = measure_discovery_sufficiency(
        report,
        expected_relevant_paths=(
            "research/adaptation-boundaries.md",
            "research/climate-evidence.md",
        ),
    )

    assert report.step_id == "frame"
    assert report.sufficiency_status is ContextSufficiencyStatus.SUFFICIENT
    assert measurement.sufficient
    assert measurement.precision == 1.0
    assert measurement.recall == 1.0
    assert tuple(item.path for item in report.candidates) == (
        "research/adaptation-boundaries.md",
        "research/climate-evidence.md",
    )
    assert all("cooking" not in item.path for item in report.candidates)


def test_required_input_coverage_and_drift_control_structural_sufficiency(
    tmp_path: Path,
) -> None:
    initialized = _initiative(
        tmp_path,
        objective="Plan a checkout implementation",
        scope="Accepted checkout requirements",
    )
    _advance_software_to_plan(initialized)

    current = discover_context(initialized.layout)

    assert current.step_id == "plan"
    assert current.required_input_roles == ("requirements",)
    assert current.covered_required_input_roles == ("requirements",)
    assert current.current_required_input_roles == ("requirements",)
    assert current.required_input_coverage == 1.0
    assert current.sufficiency_status is ContextSufficiencyStatus.SUFFICIENT
    requirements = next(item for item in current.candidates if item.path == "requirements.md")
    assert requirements.current_required_input
    assert requirements.registered_roles == ("requirements",)

    (tmp_path / "requirements.md").write_text(
        "Changed without registering a revision",
        encoding="utf-8",
    )
    changed = discover_context(initialized.layout)

    assert changed.covered_required_input_roles == ("requirements",)
    assert changed.current_required_input_roles == ()
    assert changed.required_input_coverage == 0.0
    assert changed.sufficiency_status is ContextSufficiencyStatus.INSUFFICIENT
    assert any("no longer matches" in warning for warning in changed.warnings)


def test_discovery_hashes_only_active_required_governed_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(
        tmp_path,
        objective="Plan a checkout implementation",
        scope="Accepted checkout requirements",
    )
    _advance_software_to_plan(initialized)
    inspected_paths: list[str] = []

    def record_currentness_check(
        layout: RepositoryLayout,
        revision: ArtifactRevision,
    ) -> None:
        inspected_paths.append(revision.path)

    monkeypatch.setattr(
        context_discovery,
        "assert_working_revision_current",
        record_currentness_check,
    )

    report = discover_context(initialized.layout)

    assert report.sufficiency_status is ContextSufficiencyStatus.SUFFICIENT
    assert inspected_paths == ["requirements.md"]
    assert "objective.md" not in inspected_paths


def test_discovery_withholds_unregistered_paths_without_git_ignore_enforcement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(
        tmp_path,
        objective="Discover payment requirements",
        scope="Payment requirements only",
        with_git=False,
    )
    (tmp_path / "payment-requirements.md").write_text(
        "Unregistered candidate",
        encoding="utf-8",
    )

    def unavailable_git(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError

    monkeypatch.setattr(context_discovery.subprocess, "run", unavailable_git)
    report = discover_context(initialized.layout)

    assert not report.ignore_policy_enforced
    assert report.sufficiency_status is ContextSufficiencyStatus.INDETERMINATE
    assert report.candidates == ()
    assert any("unregistered path suggestions are withheld" in item for item in report.warnings)


def test_candidate_limit_is_fail_closed_and_cli_is_read_only(tmp_path: Path) -> None:
    initialized = _initiative(
        tmp_path,
        objective="Implement payment checkout requirements",
        scope="Payment checkout requirements",
    )
    for name in ("payment-a.md", "payment-b.md", "payment-c.md"):
        (tmp_path / name).write_text(name, encoding="utf-8")
    journal_before = initialized.layout.event_journal_file.read_bytes()

    report = discover_context(initialized.layout, max_candidates=1)
    result = runner.invoke(
        app,
        ["agent", "discover", "-C", str(tmp_path), "--max-candidates", "1"],
    )

    assert report.candidate_budget_exhausted
    assert report.sufficiency_status is ContextSufficiencyStatus.INSUFFICIENT
    assert len(report.candidates) == 1
    assert result.exit_code == 0, result.stderr
    assert "Context discovery profile: bounded-path-v1" in result.stdout
    assert "Structural sufficiency: insufficient" in result.stdout
    assert "Candidate paths:" in result.stdout
    assert "SQLite FTS" in result.stdout
    assert initialized.layout.event_journal_file.read_bytes() == journal_before


def test_repository_file_inspection_limit_is_a_hard_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialized = _initiative(
        tmp_path,
        objective="Discover payment requirements",
        scope="Payment requirements only",
    )
    (tmp_path / "payment-a.md").write_text("First candidate", encoding="utf-8")
    (tmp_path / "payment-b.md").write_text("Second candidate", encoding="utf-8")
    monkeypatch.setattr(context_discovery, "MAX_INSPECTED_FILES", 1)

    report = discover_context(initialized.layout)

    assert report.inspected_file_count == 1
    assert report.inventory_truncated
    assert report.sufficiency_status is ContextSufficiencyStatus.INSUFFICIENT
    assert any("file inspection limit" in warning for warning in report.warnings)


def test_discovery_never_follows_symbolic_links_when_supported(tmp_path: Path) -> None:
    initialized = _initiative(
        tmp_path,
        objective="Discover payment requirements",
        scope="Payment requirements only",
    )
    target = tmp_path / "payment-requirements.md"
    target.write_text("Ordinary candidate", encoding="utf-8")
    linked = tmp_path / "payment-linked.md"
    try:
        os.symlink(target, linked)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")

    report = discover_context(initialized.layout)

    assert report.symlink_excluded_count == 1
    assert "payment-linked.md" not in {item.path for item in report.candidates}
