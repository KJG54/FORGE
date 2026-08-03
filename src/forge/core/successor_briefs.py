"""Read-only milestone transition briefs derived from validated terminal archives."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from forge import __version__
from forge.contracts.archives import ArchiveManifest
from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.contracts.verification import AcceptanceRecord, CheckResult, EvidencePacket
from forge.core.archival import ArchiveView, load_archive
from forge.core.decisions import DecisionView, list_decision_views
from forge.core.lifecycle import load_active_initiative
from forge.core.risk_acceptances import list_risk_acceptances
from forge.core.scope_amendments import effective_scope_summary
from forge.core.successors import predecessor_artifact_source_reference
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout

GIT_OBSERVATION_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class ReusableRevision:
    """One manifest-bound terminal revision that a successor may explicitly reuse."""

    artifact: ArtifactRecord
    revision: ArtifactRevision
    accepted: bool
    predecessor_reference: str


@dataclass(frozen=True)
class RepositoryObservations:
    """Fresh, non-governed observations kept separate from archived facts."""

    observed_at: datetime
    forge_version: str
    active_initiative_id: UUID | None
    selected_archive_is_predecessor: bool
    git_available: bool
    git_branch: str | None
    git_commit: str | None
    git_worktree_state: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SuccessorBrief:
    """Validated inputs for one disposable human-readable successor brief."""

    archive: ArchiveView
    effective_scope: str
    revisions: tuple[ReusableRevision, ...]
    current_decisions: tuple[DecisionView, ...]
    accepted_checks: tuple[CheckResult, ...]
    accepted_evidence: tuple[EvidencePacket, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    lessons: tuple[ReusableRevision, ...]
    observations: RepositoryObservations
    markdown: str


def _single_line(value: str) -> str:
    return " ".join(value.split())


def _unique(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item for item in items if item))


def _run_git(layout: RepositoryLayout, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=layout.root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=GIT_OBSERVATION_TIMEOUT_SECONDS,
    )


def _git_observations(
    layout: RepositoryLayout,
) -> tuple[bool, str | None, str | None, str, tuple[str, ...]]:
    warnings: list[str] = []
    try:
        worktree = _run_git(layout, "rev-parse", "--is-inside-work-tree")
    except FileNotFoundError:
        return False, None, None, "unavailable", ("Git executable is unavailable",)
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, None, None, "unavailable", (f"Git observation failed: {error}",)
    if worktree.returncode != 0 or worktree.stdout.strip() != "true":
        return True, None, None, "not-a-worktree", (
            "Repository is not inside a Git worktree",
        )

    try:
        branch_result = _run_git(layout, "branch", "--show-current")
        commit_result = _run_git(layout, "rev-parse", "HEAD")
        status_result = _run_git(
            layout,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return True, None, None, "unknown", (f"Git observation failed: {error}",)

    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    if not branch:
        branch = "detached"
    commit = commit_result.stdout.strip() if commit_result.returncode == 0 else None
    if commit is None:
        warnings.append("Git could not identify the current commit")
    if status_result.returncode == 0:
        entry_count = len(tuple(item for item in status_result.stdout.split("\0") if item))
        state = "clean" if entry_count == 0 else f"dirty ({entry_count} entries)"
    else:
        state = "unknown"
        warnings.append("Git could not inspect the current worktree state")
    return True, branch, commit, state, tuple(warnings)


def _repository_observations(
    layout: RepositoryLayout,
    archive_id: UUID,
) -> RepositoryObservations:
    active_id: UUID | None = None
    selected_archive_is_predecessor = False
    if layout.initiative_file.exists():
        active = load_active_initiative(
            layout,
            allow_paused=True,
            allow_untrusted_pack=True,
        )
        active_id = active.initiative.id
        selected_archive_is_predecessor = any(
            reference.initiative_id == archive_id
            for reference in active.initiative.predecessor_references
        )
    git_available, branch, commit, worktree_state, warnings = _git_observations(layout)
    from forge.contracts.base import utc_now

    return RepositoryObservations(
        observed_at=utc_now(),
        forge_version=__version__,
        active_initiative_id=active_id,
        selected_archive_is_predecessor=selected_archive_is_predecessor,
        git_available=git_available,
        git_branch=branch,
        git_commit=commit,
        git_worktree_state=worktree_state,
        warnings=warnings,
    )


def _revisions(archive: ArchiveView) -> tuple[ReusableRevision, ...]:
    result: list[ReusableRevision] = []
    for reference in archive.manifest.object_references:
        revision = load_record(
            archive.layout.artifact_revision_directory
            / f"{reference.artifact_revision_id}.json",
            ArtifactRevision,
        )
        artifact = load_record(
            archive.layout.artifact_record_directory
            / f"{revision.artifact_id}.{revision.revision_number}.json",
            ArtifactRecord,
        )
        result.append(
            ReusableRevision(
                artifact=artifact,
                revision=revision,
                accepted=reference.accepted,
                predecessor_reference=predecessor_artifact_source_reference(
                    archive.active.initiative.id,
                    revision.id,
                ),
            )
        )
    return tuple(sorted(result, key=lambda item: (item.artifact.role, str(item.revision.id))))


def _final_acceptances(archive: ArchiveView) -> tuple[AcceptanceRecord, ...]:
    if archive.closure is None:
        return ()
    return tuple(
        load_record(
            archive.layout.acceptance_directory / f"{acceptance_id}.json",
            AcceptanceRecord,
        )
        for acceptance_id in archive.closure.final_acceptance_ids
    )


def _accepted_support(
    archive: ArchiveView,
    acceptances: tuple[AcceptanceRecord, ...],
) -> tuple[tuple[CheckResult, ...], tuple[EvidencePacket, ...]]:
    check_ids = sorted(
        {
            check_id
            for acceptance in acceptances
            for check_id in acceptance.accepted_check_result_ids
        },
        key=str,
    )
    evidence_ids = sorted(
        {
            evidence_id
            for acceptance in acceptances
            for evidence_id in acceptance.accepted_evidence_ids
        },
        key=str,
    )
    checks = tuple(
        load_record(archive.layout.check_directory / f"{check_id}.json", CheckResult)
        for check_id in check_ids
    )
    evidence = tuple(
        load_record(
            archive.layout.evidence_directory / f"{evidence_id}.json",
            EvidencePacket,
        )
        for evidence_id in evidence_ids
    )
    return checks, evidence


def _limitations(
    manifest: ArchiveManifest,
    acceptances: tuple[AcceptanceRecord, ...],
    checks: tuple[CheckResult, ...],
    evidence: tuple[EvidencePacket, ...],
) -> tuple[str, ...]:
    return _unique(
        (
            *manifest.limitations,
            *(item for acceptance in acceptances for item in acceptance.known_limitations),
            *(item for check in checks for item in check.limitations),
            *(item for packet in evidence for item in packet.limitations),
        )
    )


def _risks(
    archive: ArchiveView,
    acceptances: tuple[AcceptanceRecord, ...],
) -> tuple[str, ...]:
    terminal_risks = (
        archive.abandonment.unresolved_risks if archive.abandonment is not None else ()
    )
    accepted_risks = tuple(
        f"{view.acceptance.risk} (residual impact: {view.acceptance.residual_impact})"
        for view in list_risk_acceptances(archive.layout)
        if view.revocation is None and not view.stale
    )
    return _unique(
        (
            *terminal_risks,
            *(item for acceptance in acceptances for item in acceptance.residual_risks),
            *accepted_risks,
        )
    )


def _bullet_lines(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {_single_line(item)}" for item in items) if items else "- none"


def _artifact_lines(revisions: tuple[ReusableRevision, ...]) -> str:
    if not revisions:
        return "- none"
    return "\n".join(
        f"- `{item.artifact.role}` - {_single_line(item.artifact.title)}: "
        f"`{item.revision.path}` (artifact `{item.artifact.id}`, revision "
        f"`{item.revision.id}`, digest `{item.revision.content_digest}`, "
        f"{item.revision.byte_size} bytes)"
        for item in revisions
    )


def _decision_lines(decisions: tuple[DecisionView, ...]) -> str:
    if not decisions:
        return "- none"
    return "\n".join(
        f"- `{view.decision.id}` [{view.decision.decision_type}]: "
        f"{_single_line(view.decision.question)} -> "
        f"{_single_line(view.decision.chosen_outcome)}"
        for view in decisions
    )


def _check_lines(checks: tuple[CheckResult, ...]) -> str:
    if not checks:
        return "- none"
    return "\n".join(
        f"- `{check.id}` `{check.check_id}` {check.outcome.value}; "
        f"result `{check.result_digest}`"
        for check in checks
    )


def _evidence_lines(evidence: tuple[EvidencePacket, ...]) -> str:
    if not evidence:
        return "- none"
    return "\n".join(
        f"- `{packet.id}`: {_single_line(packet.purpose)}; packet "
        f"`{packet.packet_digest}`"
        for packet in evidence
    )


def _reusable_lines(revisions: tuple[ReusableRevision, ...]) -> str:
    if not revisions:
        return "- none"
    return "\n".join(
        f"- `{item.revision.id}` [{('accepted' if item.accepted else 'not accepted')}]: "
        f"`{item.predecessor_reference}`; object "
        f"`{item.revision.preserved_object_path}`; digest "
        f"`{item.revision.content_digest}`; {item.revision.byte_size} bytes; reuse option "
        f"`--predecessor-revision {item.revision.id}`"
        for item in revisions
    )


def _lineage_lines(archive: ArchiveView) -> str:
    references = archive.active.initiative.predecessor_references
    if not references:
        return "- none"
    return "\n".join(
        f"- `{reference.initiative_id}` via `{reference.archive_reference}`"
        for reference in references
    )


def _terminal_lines(archive: ArchiveView) -> str:
    if archive.closure is not None:
        return (
            f"- Closing summary: {_single_line(archive.closure.closing_summary)}\n"
            f"- Final acceptance records: {len(archive.closure.final_acceptance_ids)}"
        )
    assert archive.abandonment is not None
    return (
        f"- Abandonment reason: {_single_line(archive.abandonment.reason)}\n"
        f"- Unfinished work: {_single_line(archive.abandonment.unfinished_work_summary)}"
    )


def _observation_lines(
    layout: RepositoryLayout,
    archive_id: UUID,
    observations: RepositoryObservations,
) -> str:
    if observations.active_initiative_id is None:
        active = "none (archive-only repository state)"
    else:
        relationship = (
            "declares the selected archive as a predecessor"
            if observations.selected_archive_is_predecessor
            else "does not declare the selected archive as a predecessor"
        )
        active = f"{observations.active_initiative_id} ({relationship})"
    lines = (
        f"- Observed at: `{observations.observed_at.isoformat()}`",
        f"- Repository root: `{layout.root}`",
        f"- Installed FORGE version: `{observations.forge_version}`",
        f"- Active initiative: {active}",
        f"- Git available: {'yes' if observations.git_available else 'no'}",
        f"- Git branch: `{observations.git_branch or 'unavailable'}`",
        f"- Git commit: `{observations.git_commit or 'unavailable'}`",
        f"- Git worktree: {observations.git_worktree_state}",
        *(
            f"- Observation warning: {_single_line(warning)}"
            for warning in observations.warnings
        ),
        f"- Selected archive at observation time: `{archive_id}`",
    )
    return "\n".join(lines)


def _render_markdown(
    layout: RepositoryLayout,
    archive: ArchiveView,
    effective_scope: str,
    revisions: tuple[ReusableRevision, ...],
    current_decisions: tuple[DecisionView, ...],
    accepted_checks: tuple[CheckResult, ...],
    accepted_evidence: tuple[EvidencePacket, ...],
    limitations: tuple[str, ...],
    risks: tuple[str, ...],
    lessons: tuple[ReusableRevision, ...],
    observations: RepositoryObservations,
) -> str:
    initiative = archive.active.initiative
    accepted_artifacts = tuple(item for item in revisions if item.accepted)
    archive_id = initiative.id
    journal_hash = archive.active.state.journal_head_hash or "legacy-unhashed"
    create_command = (
        'forge create "<new objective>" --scope "<new bounded scope>" '
        f"--predecessor {archive_id} --trust-pack-data -C ."
    )
    return f"""# FORGE Successor Brief

> Disposable read-only view. The validated archive remains authoritative. This brief imports no
> progress, checks, evidence, decisions, acceptance, authority, or local scratchpad content.

## Governed predecessor facts

- Archive validation: healthy
- Initiative ID: `{archive_id}`
- Objective: {_single_line(initiative.objective)}
- Effective scope: {_single_line(effective_scope)}
- Terminal outcome: `{archive.manifest.terminal_state.value}`
- Archive reference: `.forge/archive/{archive_id}`
- Archive digest: `{archive.manifest.archive_digest}`
- Journal head: sequence {archive.active.state.journal_head_sequence}, hash `{journal_hash}`
{_terminal_lines(archive)}

### Predecessor lineage

{_lineage_lines(archive)}

## Durable governed carryover

### Accepted artifacts

{_artifact_lines(accepted_artifacts)}

### Current decisions

{_decision_lines(current_decisions)}

### Accepted checks

{_check_lines(accepted_checks)}

### Accepted evidence

{_evidence_lines(accepted_evidence)}

### Limitations

{_bullet_lines(limitations)}

### Residual risks

{_bullet_lines(risks)}

### Lessons

{_artifact_lines(lessons)}

## Exact reusable predecessor revisions

{_reusable_lines(revisions)}

Reuse is a distinct successor registration. Exact bytes and provenance may be copied; predecessor
progress and acceptance do not transfer.

## Fresh repository observations (not governed history)

{_observation_lines(layout, archive_id, observations)}

## Receiving-agent startup validation

1. `forge status --archive {archive_id} -C .`
2. `forge history --archive {archive_id} -C .`
3. `forge successor brief --archive {archive_id} -C .`
4. Inspect fresh Git state independently with `git status --short --branch` and
   `git rev-parse HEAD`.
5. If no initiative is active, review and then perform the distinct owner action using
   `{create_command}`.
6. Reuse only an exact terminal revision listed above. First place its exact bytes at the intended
   successor path, then review the resulting
   `forge artifact add ... --predecessor-revision <revision-id>` command.

The receiving agent must rerun validation rather than trusting this prose or prior-chat memory.
"""


def build_successor_brief(layout: RepositoryLayout, archive_id: UUID) -> SuccessorBrief:
    """Validate one terminal archive and derive a non-persisted milestone brief."""

    archive = load_archive(layout, archive_id)
    revisions = _revisions(archive)
    acceptances = _final_acceptances(archive)
    checks, evidence = _accepted_support(archive, acceptances)
    decisions = tuple(
        view for view in list_decision_views(archive.layout) if view.status == "current"
    )
    limitations = _limitations(archive.manifest, acceptances, checks, evidence)
    risks = _risks(archive, acceptances)
    lessons = tuple(
        item for item in revisions if item.accepted and item.artifact.role == "lessons"
    )
    observations = _repository_observations(layout, archive_id)
    scope = effective_scope_summary(archive.active)
    markdown = _render_markdown(
        layout,
        archive,
        scope,
        revisions,
        decisions,
        checks,
        evidence,
        limitations,
        risks,
        lessons,
        observations,
    )
    return SuccessorBrief(
        archive=archive,
        effective_scope=scope,
        revisions=revisions,
        current_decisions=decisions,
        accepted_checks=checks,
        accepted_evidence=evidence,
        limitations=limitations,
        risks=risks,
        lessons=lessons,
        observations=observations,
        markdown=markdown,
    )
