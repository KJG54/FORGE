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
)
from forge.core.archival import ArchiveSummary
from forge.core.lifecycle import load_active_initiative
from forge.errors import IntegrityError
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


def inspect_status(
    layout: RepositoryLayout,
    *,
    archive_id: UUID | None = None,
) -> StatusReport:
    from forge.core.archival import list_archive_summaries, load_archive

    try:
        archive_summaries = list_archive_summaries(layout)
        archived_ids = tuple(summary.initiative_id for summary in archive_summaries)
        if archive_id is not None:
            archived = load_archive(layout, archive_id)
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
    retired = tuple(
        path.name
        for path in layout.local_directory.iterdir()
        if path.name.startswith(("closed-active-", "abandoned-active-"))
    )
    if not layout.active_directory.exists():
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=None,
            state=None,
            next_actions=(),
            blockers=(
                "Terminal retirement is incomplete; retry the terminal command with the same "
                "idempotency key",
            ),
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

        run_actions = tuple(
            f"run-cancel:{run_id}" for run_id in active.state.active_run_ids
        )
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
    from forge.core.artifacts import list_artifacts
    from forge.core.deviations import open_workflow_deviations
    from forge.core.overrides import list_emergency_overrides
    from forge.core.risk_acceptances import list_risk_acceptances

    drifted = tuple(view for view in list_artifacts(layout) if not view.working_copy_matches)
    open_deviations = open_workflow_deviations(layout)
    emergency_overrides = list_emergency_overrides(layout)
    risk_acceptances = list_risk_acceptances(layout)
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
        override
        for override in effective_overrides
        if override.id not in accepted_override_ids
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
        *(
            "deviation-review:"
            f"{view.deviation.id}"
            for view in open_deviations
        ),
        *(
            f"risk-accept:{override.id}"
            for override in unresolved_overrides
        ),
    )
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
        resumption_summary = build_resumption_summary(layout)
    elif drifted:
        next_actions = tuple(f"artifact-revise:{view.artifact.id}" for view in drifted)
    if active.state.journal_head_hash is None:
        blockers = (
            "Legacy M1 journal is read-only; preview and apply its registered migration",
            *blockers,
        )
        next_actions = ("migrate",)
    from forge.core.scope_amendments import effective_scope_summary

    return StatusReport(
        repository_state=RepositoryState.INITIALIZED,
        integrity_state=active.state.integrity_state,
        initiative=active.initiative,
        state=active.state,
        next_actions=next_actions,
        blockers=blockers,
        archived_initiative_ids=archived_ids,
        archive_summaries=archive_summaries,
        pack_trust_state=active.pack_trust.trust_state,
        effective_scope_summary=effective_scope_summary(active),
        open_workflow_deviation_ids=tuple(
            item.deviation.id for item in open_deviations
        ),
        emergency_override_ids=tuple(item.id for item in emergency_overrides),
        risk_acceptance_ids=tuple(
            item.acceptance.id for item in risk_acceptances
        ),
        resumption_summary=resumption_summary,
    )
