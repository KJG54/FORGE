"""Read-only repository status and legal-next-action reporting."""

from __future__ import annotations

from dataclasses import dataclass

from forge.contracts.initiatives import Initiative
from forge.contracts.state import IntegrityState, MaterializedState, RepositoryState
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


def inspect_status(layout: RepositoryLayout) -> StatusReport:
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
            next_actions=("create",),
        )
    try:
        active = load_active_initiative(layout)
    except IntegrityError as error:
        return StatusReport(
            repository_state=RepositoryState.INITIALIZED,
            integrity_state=IntegrityState.INTEGRITY_ERROR,
            initiative=None,
            state=None,
            next_actions=(),
            blockers=(str(error),),
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
    )
