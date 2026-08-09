"""Read-only repository status and legal-next-action reporting."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from forge.contracts.archives import AbandonmentRecord, ArchiveManifest, ClosureRecord
from forge.contracts.initiatives import Initiative
from forge.contracts.packs import PackTrustState
from forge.contracts.state import (
    InitiativeLifecycleState,
    IntegrityState,
    MaterializedState,
    RepositoryState,
    StepState,
)
from forge.core.archival import ArchiveSummary
from forge.core.lifecycle import load_active_initiative
from forge.errors import ConflictError, IntegrityError
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout


@dataclass(frozen=True)
class StatusReport:
    repository_state: RepositoryState
    integrity_state: IntegrityState
    initiative: Initiative | None
    state: MaterializedState | None
    next_actions: tuple[str, ...]
    blockers: tuple[str, ...] = ()
    ready_actions: tuple[str, ...] | None = None
    archived_initiative_ids: tuple[UUID, ...] = ()
    selected_archive_id: UUID | None = None
    archive_manifest: ArchiveManifest | None = None
    closure: ClosureRecord | None = None
    abandonment: AbandonmentRecord | None = None
    archive_summaries: tuple[ArchiveSummary, ...] = ()
    pack_trust_state: PackTrustState | None = None
    effective_scope_summary: str | None = None
    open_workflow_deviation_ids: tuple[UUID, ...] = ()
    emergency_override_ids: tuple[UUID, ...] = ()
    risk_acceptance_ids: tuple[UUID, ...] = ()
    resumption_summary: str | None = None

    @property
    def executable_actions(self) -> tuple[str, ...]:
        """Actions executable now; absent overrides mean every legal action is ready."""

        return self.next_actions if self.ready_actions is None else self.ready_actions


def inspect_status(
    layout: RepositoryLayout,
    *,
    archive_id: UUID | None = None,
) -> StatusReport:
    from forge.core.archival import list_validated_archives, summarize_archive

    try:
        archives = list_validated_archives(layout)
        archive_summaries = tuple(summarize_archive(archive) for archive in archives)
        archived_ids = tuple(summary.initiative_id for summary in archive_summaries)
        if archive_id is not None:
            archived = next(
                (archive for archive in archives if archive.active.initiative.id == archive_id),
                None,
            )
            if archived is None:
                raise ConflictError(f"Unknown archived initiative {archive_id}")
            from forge.core.scope_amendments import effective_scope_summary

            return StatusReport(
                repository_state=RepositoryState.INITIALIZED,
                integrity_state=IntegrityState.HEALTHY,
                initiative=archived.active.initiative,
                state=archived.active.state,
                next_actions=(),
                archived_initiative_ids=archived_ids,
                selected_archive_id=archive_id,
                archive_manifest=archived.manifest,
                closure=archived.closure,
                abandonment=archived.abandonment,
                archive_summaries=archive_summaries,
                pack_trust_state=archived.active.pack_trust.trust_state,
                effective_scope_summary=effective_scope_summary(archived.active),
            )
    except IntegrityError as error:
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=None,
            state=None,
            next_actions=(),
            blockers=(str(error),),
        )
    staging = tuple(
        path.name
        for path in layout.archive_directory.iterdir()
        if path.name.startswith(".") and path.name.endswith(".staging")
    )
    if layout.local_directory.is_symlink() or (
        layout.local_directory.exists() and not layout.local_directory.is_dir()
    ):
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=None,
            state=None,
            next_actions=(),
            blockers=(f"Local FORGE path is irregular or symbolic: {layout.local_directory}",),
            archived_initiative_ids=archived_ids,
            archive_summaries=archive_summaries,
        )
    retired = (
        tuple(
            path.name
            for path in layout.local_directory.iterdir()
            if path.name.startswith(("closed-active-", "abandoned-active-"))
        )
        if layout.local_directory.is_dir()
        else ()
    )
    active_exists = layout.active_directory.exists()
    if layout.active_directory.is_symlink() or (
        active_exists and not layout.active_directory.is_dir()
    ):
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=None,
            state=None,
            next_actions=(),
            blockers=(f"Active FORGE path is irregular or symbolic: {layout.active_directory}",),
            archived_initiative_ids=archived_ids,
            archive_summaries=archive_summaries,
        )
    if not active_exists:
        if staging or retired:
            return StatusReport(
                repository_state=RepositoryState.INITIALIZED,
                integrity_state=IntegrityState.INTEGRITY_ERROR,
                initiative=None,
                state=None,
                next_actions=(),
                blockers=(
                    "Terminal retirement is incomplete; retry the terminal command with the same "
                    f"idempotency key (staging={staging}, retired={retired})",
                ),
                archived_initiative_ids=archived_ids,
                archive_summaries=archive_summaries,
            )
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.HEALTHY,
            initiative=None,
            state=None,
            next_actions=("create",) if not archived_ids else ("create-successor",),
            archived_initiative_ids=archived_ids,
            archive_summaries=archive_summaries,
        )
    if not layout.initiative_file.exists():
        unexpected = tuple(path.name for path in layout.active_directory.iterdir())
        if unexpected or staging or retired:
            return StatusReport(
                repository_state=RepositoryState.INITIALIZED,
                integrity_state=IntegrityState.INTEGRITY_ERROR,
                initiative=None,
                state=None,
                next_actions=(),
                blockers=(
                    "Terminal transaction is incomplete; retry the terminal command with the same "
                    f"idempotency key (active={unexpected}, staging={staging}, retired={retired})",
                ),
                archived_initiative_ids=archived_ids,
                archive_summaries=archive_summaries,
            )
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.HEALTHY,
            initiative=None,
            state=None,
            next_actions=("create",) if not archived_ids else ("create-successor",),
            archived_initiative_ids=archived_ids,
            archive_summaries=archive_summaries,
        )
    try:
        active = load_active_initiative(
            layout,
            allow_terminal=True,
            allow_paused=True,
            allow_untrusted_pack=True,
        )
    except IntegrityError as error:
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=None,
            state=None,
            next_actions=(),
            blockers=(str(error),),
            archived_initiative_ids=archived_ids,
            archive_summaries=archive_summaries,
        )
    if active.state.lifecycle_state in {
        InitiativeLifecycleState.CLOSED,
        InitiativeLifecycleState.ABANDONED,
    }:
        terminal_command = (
            "close"
            if active.state.lifecycle_state is InitiativeLifecycleState.CLOSED
            else "abandon"
        )
        from forge.core.scope_amendments import effective_scope_summary

        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=active.initiative,
            state=active.state,
            next_actions=(),
            blockers=(
                "Terminal state remains under .forge/active; retry "
                f"'forge {terminal_command}' "
                "with the same idempotency key to finish atomic archival",
            ),
            archived_initiative_ids=archived_ids,
            archive_summaries=archive_summaries,
            pack_trust_state=active.pack_trust.trust_state,
            effective_scope_summary=effective_scope_summary(active),
        )
    if active.pack_trust.trust_state is PackTrustState.UNTRUSTED:
        from forge.core.scope_amendments import effective_scope_summary

        run_actions = tuple(f"run-cancel:{run_id}" for run_id in active.state.active_run_ids)
        terminal_actions = () if run_actions else ("abandon",)
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=active.state.integrity_state,
            initiative=active.initiative,
            state=active.state,
            next_actions=(
                f"pack-trust:{active.pack_manifest.id}",
                *run_actions,
                *terminal_actions,
            ),
            blockers=(
                f"Locked pack {active.pack_manifest.id}@{active.pack_manifest.version} is "
                "untrusted as data; workflow-dependent mutation is disabled",
            ),
            archived_initiative_ids=archived_ids,
            archive_summaries=archive_summaries,
            pack_trust_state=active.pack_trust.trust_state,
            effective_scope_summary=effective_scope_summary(active),
        )
    if active.state.current_artifact_revisions:
        from forge.core.artifacts import list_artifacts

        artifact_views = list_artifacts(layout)
    else:
        artifact_views = ()
    drifted = tuple(view for view in artifact_views if not view.working_copy_matches)
    if layout.workflow_deviation_directory.exists():
        from forge.core.deviations import open_workflow_deviations

        open_deviations = open_workflow_deviations(layout)
    else:
        open_deviations = ()
    if layout.emergency_override_directory.exists():
        from forge.core.overrides import list_emergency_overrides

        emergency_overrides = list_emergency_overrides(layout)
    else:
        emergency_overrides = ()
    if layout.risk_acceptance_directory.exists():
        from forge.core.risk_acceptances import list_risk_acceptances

        risk_acceptances = list_risk_acceptances(layout)
    else:
        risk_acceptances = ()
    effective_overrides = tuple(
        override
        for override in emergency_overrides
        if override.id not in active.state.stale_record_ids
    )
    accepted_override_ids: set[UUID] = set()
    for view in risk_acceptances:
        if (
            view.stale
            or view.revocation is not None
            or view.override.id in active.state.stale_record_ids
        ):
            continue
        if view.override.id in accepted_override_ids:
            raise IntegrityError(
                f"Emergency override {view.override.id} has multiple current risk acceptances"
            )
        accepted_override_ids.add(view.override.id)
    unresolved_overrides = tuple(
        override for override in effective_overrides if override.id not in accepted_override_ids
    )
    blockers = (
        *(
            "Workflow deviation "
            f"{view.deviation.id} requires review: {view.deviation.review_requirement}"
            for view in open_deviations
        ),
        *(
            "Emergency override "
            f"{override.id} retains unresolved residual risk: {override.residual_risk}"
            for override in unresolved_overrides
        ),
        *(
            f"Working copy changed for artifact {view.artifact.id}; register an explicit revision"
            for view in drifted
        ),
    )
    next_actions = (
        *active.state.permitted_next_actions,
        *(f"deviation-review:{view.deviation.id}" for view in open_deviations),
        *(f"risk-accept:{override.id}" for override in unresolved_overrides),
    )
    ready_actions = next_actions
    current_step_id = active.state.current_step_id
    current_step_state = (
        active.state.step_states.get(current_step_id) if current_step_id is not None else None
    )
    if current_step_id is not None and current_step_state is StepState.IN_PROGRESS:
        current_step = next(step for step in active.workflow.steps if step.id == current_step_id)
        registered_roles = {view.artifact.role for view in artifact_views}
        missing_roles = tuple(
            role for role in current_step.required_outputs if role not in registered_roles
        )
        if missing_roles:
            blockers = (
                *blockers,
                f"Step {current_step_id} cannot complete until required artifact roles are "
                f"registered: {list(missing_roles)}",
            )
            blocked_completion = f"complete:{current_step_id}"
            ready_actions = (
                *(action for action in next_actions if action != blocked_completion),
                *(f"artifact-add:{role}" for role in missing_roles),
            )
    elif current_step_id is not None and current_step_state is StepState.AWAITING_VERIFICATION:
        from forge.core.verification import inspect_verification_prerequisites

        current_step = next(step for step in active.workflow.steps if step.id == current_step_id)
        prerequisites = inspect_verification_prerequisites(
            layout,
            active=active,
            step=current_step,
        )
        blocked_verification = f"verify:{current_step_id}"
        other_ready_actions = tuple(
            action for action in next_actions if action != blocked_verification
        )
        if not prerequisites.claims:
            blockers = (
                *blockers,
                f"Step {current_step_id} cannot verify until a current worker claim covers "
                "the required artifact revisions",
            )
            ready_actions = other_ready_actions
        elif prerequisites.missing_check_ids:
            blockers = (
                *blockers,
                f"Step {current_step_id} cannot verify until required checks pass for current "
                f"artifact revisions: {list(prerequisites.missing_check_ids)}",
            )
            ready_actions = (
                *other_ready_actions,
                *(
                    f"check-record:{current_step_id}:{check_id}"
                    for check_id in prerequisites.missing_check_ids
                ),
            )
        elif prerequisites.evidence is None:
            blockers = (
                *blockers,
                f"Step {current_step_id} cannot verify until evidence binds current "
                "artifacts, passing checks, and claim",
            )
            ready_actions = (*other_ready_actions, f"evidence-add:{current_step_id}")
    resumption_summary = None
    if active.state.lifecycle_state is InitiativeLifecycleState.PAUSED:
        from forge.core.continuity import build_resumption_summary

        pause_id = active.state.active_pause_event_id
        pause_event = next(
            (event for event in read_journal(layout.event_journal_file) if event.id == pause_id),
            None,
        )
        reason = pause_event.metadata.get("reason") if pause_event is not None else None
        if not isinstance(reason, str) or not reason:
            raise IntegrityError("Paused initiative lacks a valid governing pause reason")
        blockers = (f"Initiative paused: {reason}", *blockers)
        next_actions = ("resume",)
        ready_actions = next_actions
        resumption_summary = build_resumption_summary(layout)
    elif drifted:
        next_actions = tuple(f"artifact-revise:{view.artifact.id}" for view in drifted)
        ready_actions = next_actions
    if active.state.journal_head_hash is None:
        blockers = (
            "Legacy M1 journal is read-only; preview and apply its registered migration",
            *blockers,
        )
        next_actions = ("migrate",)
        ready_actions = next_actions
    from forge.core.scope_amendments import effective_scope_summary

    return StatusReport(
        repository_state=RepositoryState.INITIALIZED,
        integrity_state=active.state.integrity_state,
        initiative=active.initiative,
        state=active.state,
        next_actions=next_actions,
        blockers=blockers,
        ready_actions=ready_actions,
        archived_initiative_ids=archived_ids,
        archive_summaries=archive_summaries,
        pack_trust_state=active.pack_trust.trust_state,
        effective_scope_summary=effective_scope_summary(active),
        open_workflow_deviation_ids=tuple(item.deviation.id for item in open_deviations),
        emergency_override_ids=tuple(item.id for item in emergency_overrides),
        risk_acceptance_ids=tuple(item.acceptance.id for item in risk_acceptances),
        resumption_summary=resumption_summary,
    )
