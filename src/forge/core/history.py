"""Validated read-only event history for active and archived initiatives."""

from uuid import UUID

from forge.contracts.events import AuditEvent
from forge.core.archival import load_archive
from forge.core.lifecycle import load_active_initiative
from forge.errors import ConflictError
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout


def inspect_history(
    layout: RepositoryLayout,
    *,
    archive_id: UUID | None = None,
    event_type: str | None = None,
    step_id: str | None = None,
    actor: str | None = None,
    run_id: UUID | None = None,
) -> tuple[AuditEvent, ...]:
    """Load validated history and apply presentation-only filters."""
    if archive_id is not None:
        events = load_archive(layout, archive_id).events
    else:
        if not layout.initiative_file.exists():
            raise ConflictError(
                "No active initiative exists; select archived history with --archive"
            )
        load_active_initiative(layout)
        events = read_journal(layout.event_journal_file)
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
    return result
