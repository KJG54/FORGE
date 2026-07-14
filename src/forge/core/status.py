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
    if not layout.initiative_file.exists():
        unexpected = tuple(path.name for path in layout.active_directory.iterdir())
        if unexpected:
            return StatusReport(
                repository_state=RepositoryState.INITIALIZED,
                integrity_state=IntegrityState.INTEGRITY_ERROR,
                initiative=None,
                state=None,
                next_actions=(),
                blockers=(f"Active directory contains incomplete records: {unexpected}",),
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
        active = load_active_initiative(layout, allow_terminal=True)
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
                "Terminal state remains under .forge/active; preliminary archival did not "
                "finish and M2 recovery is required",
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
    if drifted:
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
