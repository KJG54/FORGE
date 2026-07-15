"""Read-only repository status and legal-next-action reporting."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from forge.contracts.archives import ArchiveManifest, ClosureRecord
from forge.contracts.initiatives import Initiative
from forge.contracts.state import (
    InitiativeLifecycleState,
    IntegrityState,
    MaterializedState,
    RepositoryState,
)
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


def inspect_status(
    layout: RepositoryLayout,
    *,
    archive_id: UUID | None = None,
) -> StatusReport:
    from forge.core.archival import list_archive_ids, load_archive

    try:
        archived_ids = list_archive_ids(layout)
        if archive_id is not None:
            archived = load_archive(layout, archive_id)
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
            )
        for identifier in archived_ids:
            load_archive(layout, identifier)
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
        if path.name.startswith("closed-active-")
    )
    if not layout.active_directory.exists():
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=None,
            state=None,
            next_actions=(),
            blockers=(
                "Closure retirement is incomplete; retry 'forge close' with the same "
                "idempotency key",
            ),
            archived_initiative_ids=archived_ids,
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
                    "Closure transaction is incomplete; retry 'forge close' with the same "
                    f"idempotency key (active={unexpected}, staging={staging}, retired={retired})",
                ),
            )
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.HEALTHY,
            initiative=None,
            state=None,
            next_actions=("create",) if not archived_ids else (),
            archived_initiative_ids=archived_ids,
        )
    try:
        active = load_active_initiative(
            layout,
            allow_terminal=True,
            allow_paused=True,
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
        )
    if active.state.lifecycle_state in {
        InitiativeLifecycleState.CLOSED,
        InitiativeLifecycleState.ABANDONED,
    }:
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=active.initiative,
            state=active.state,
            next_actions=(),
            blockers=(
                "Terminal state remains under .forge/active; retry 'forge close' with the same "
                "idempotency key to finish atomic archival",
            ),
            archived_initiative_ids=archived_ids,
        )
    from forge.core.artifacts import list_artifacts

    drifted = tuple(view for view in list_artifacts(layout) if not view.working_copy_matches)
    blockers = tuple(
        f"Working copy changed for artifact {view.artifact.id}; register an explicit revision"
        for view in drifted
    )
    next_actions = active.state.permitted_next_actions
    if active.state.lifecycle_state is InitiativeLifecycleState.PAUSED:
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
    elif drifted:
        next_actions = tuple(f"artifact-revise:{view.artifact.id}" for view in drifted)
    return StatusReport(
        repository_state=RepositoryState.INITIALIZED,
        integrity_state=active.state.integrity_state,
        initiative=active.initiative,
        state=active.state,
        next_actions=next_actions,
        blockers=blockers,
        archived_initiative_ids=archived_ids,
    )
