"""Validated read-only event history for active and archived initiatives."""

from dataclasses import dataclass
from uuid import UUID

from forge.contracts.archives import ArchiveManifest
from forge.contracts.events import AuditEvent
from forge.contracts.state import InitiativeLifecycleState
from forge.core.archival import load_archive
from forge.core.lifecycle import load_active_initiative
from forge.errors import ConflictError
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout


@dataclass(frozen=True)
class HistoryReport:
    """Integrity-validated history with source and chain presentation metadata."""

    initiative_id: UUID
    lifecycle_state: InitiativeLifecycleState
    events: tuple[AuditEvent, ...]
    total_event_count: int
    journal_head_sequence: int
    journal_head_hash: str | None
    archive_manifest: ArchiveManifest | None = None


def inspect_history_report(
    layout: RepositoryLayout,
    *,
    archive_id: UUID | None = None,
    event_type: str | None = None,
    step_id: str | None = None,
    actor: str | None = None,
    run_id: UUID | None = None,
) -> HistoryReport:
    """Load validated history and apply presentation-only filters."""
    if archive_id is not None:
        archive = load_archive(layout, archive_id)
        active = archive.active
        events = archive.events
        manifest: ArchiveManifest | None = archive.manifest
    else:
        if not layout.initiative_file.exists():
            raise ConflictError(
                "No active initiative exists; select archived history with --archive"
            )
        active = load_active_initiative(
            layout,
            allow_paused=True,
            allow_untrusted_pack=True,
        )
        events = read_journal(layout.event_journal_file)
        manifest = None
    result = events
    if event_type is not None:
        result = tuple(item for item in result if item.event_type == event_type)
    if step_id is not None:
        result = tuple(item for item in result if item.metadata.get("step_id") == step_id)
    if actor is not None:
        normalized = actor.casefold()
        result = tuple(
            item
            for item in result
            if normalized
            in {
                str(item.actor.id).casefold(),
                item.actor.actor_type.value.casefold(),
                item.actor.display_label.casefold(),
            }
        )
    if run_id is not None:
        result = tuple(item for item in result if item.run_id == run_id)
    lifecycle_state = active.state.lifecycle_state
    if lifecycle_state is None:
        raise ConflictError("Selected initiative has no lifecycle state")
    return HistoryReport(
        initiative_id=active.initiative.id,
        lifecycle_state=lifecycle_state,
        events=result,
        total_event_count=len(events),
        journal_head_sequence=active.state.journal_head_sequence,
        journal_head_hash=active.state.journal_head_hash,
        archive_manifest=manifest,
    )


def inspect_history(
    layout: RepositoryLayout,
    *,
    archive_id: UUID | None = None,
    event_type: str | None = None,
    step_id: str | None = None,
    actor: str | None = None,
    run_id: UUID | None = None,
) -> tuple[AuditEvent, ...]:
    """Return only selected events for callers that do not need source metadata."""
    return inspect_history_report(
        layout,
        archive_id=archive_id,
        event_type=event_type,
        step_id=step_id,
        actor=actor,
        run_id=run_id,
    ).events
