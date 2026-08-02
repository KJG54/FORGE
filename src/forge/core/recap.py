"""Read-only warm recap with explicit governed and local boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from forge.core.lifecycle import ExplanationGuidance, load_active_initiative
from forge.core.scratchpad import ScratchpadDocument, read_scratchpad
from forge.core.status import StatusReport, inspect_status
from forge.storage.journal import read_journal
from forge.storage.repository import RepositoryLayout


class ScratchpadReconciliation(StrEnum):
    MISSING = "missing"
    EMPTY = "empty"
    CURRENT = "current"
    STALE = "stale"
    AHEAD = "ahead-of-journal"
    CROSS_INITIATIVE = "initiative-mismatch"
    NO_ACTIVE_INITIATIVE = "no-active-initiative"


@dataclass(frozen=True)
class RecapReport:
    """Validated governed position plus separately labeled advisory notes."""

    project_label: str
    project_label_source: str
    status: StatusReport
    last_governed_event_at: datetime | None
    current_step_id: str | None
    current_step_state: str | None
    guidance: ExplanationGuidance | None
    scratchpad: ScratchpadDocument
    scratchpad_reconciliation: ScratchpadReconciliation
    scratchpad_reconciliation_detail: str


def _last_governed_event_at(
    layout: RepositoryLayout,
    status: StatusReport,
) -> datetime | None:
    if status.state is not None and layout.event_journal_file.is_file():
        events = read_journal(layout.event_journal_file)
        if events:
            return events[-1].timestamp
    if status.archive_summaries:
        return max(item.last_event_at for item in status.archive_summaries)
    return None


def _reconcile(
    scratchpad: ScratchpadDocument,
    status: StatusReport,
) -> tuple[ScratchpadReconciliation, str]:
    if not scratchpad.exists:
        return (
            ScratchpadReconciliation.MISSING,
            "no local scratchpad exists",
        )
    if scratchpad.empty:
        return (
            ScratchpadReconciliation.EMPTY,
            "the local scratchpad contains no working notes",
        )
    if status.initiative is None or status.state is None:
        return (
            ScratchpadReconciliation.NO_ACTIVE_INITIATIVE,
            "local notes cannot be bound to a current initiative because none is active",
        )
    assert scratchpad.initiative_id is not None
    assert scratchpad.journal_sequence is not None
    if scratchpad.initiative_id != status.initiative.id:
        return (
            ScratchpadReconciliation.CROSS_INITIATIVE,
            "local notes name initiative "
            f"{scratchpad.initiative_id}, not active initiative {status.initiative.id}",
        )
    current_sequence = status.state.journal_head_sequence
    if scratchpad.journal_sequence < current_sequence:
        return (
            ScratchpadReconciliation.STALE,
            "local notes were based on journal sequence "
            f"{scratchpad.journal_sequence}; the validated head is {current_sequence}",
        )
    if scratchpad.journal_sequence > current_sequence:
        return (
            ScratchpadReconciliation.AHEAD,
            "local notes name journal sequence "
            f"{scratchpad.journal_sequence}; the validated head is only {current_sequence}",
        )
    return (
        ScratchpadReconciliation.CURRENT,
        f"initiative and journal sequence {current_sequence} match validated governed state",
    )


def build_recap(layout: RepositoryLayout) -> RecapReport:
    """Build a warm resume view without mutating governed or local state."""
    status = inspect_status(layout)
    scratchpad = read_scratchpad(layout)
    reconciliation, detail = _reconcile(scratchpad, status)
    current_step_id = status.state.current_step_id if status.state is not None else None
    current_step_state = None
    if status.state is not None and current_step_id is not None:
        current_step_state = status.state.step_states[current_step_id].value
    guidance = None
    if status.initiative is not None and status.state is not None:
        active = load_active_initiative(
            layout,
            allow_terminal=True,
            allow_paused=True,
            allow_untrusted_pack=True,
        )
        guidance = active.explanation_guidance
    return RecapReport(
        project_label=layout.root.name,
        project_label_source="repository directory; friendly and non-canonical",
        status=status,
        last_governed_event_at=_last_governed_event_at(layout, status),
        current_step_id=current_step_id,
        current_step_state=current_step_state,
        guidance=guidance,
        scratchpad=scratchpad,
        scratchpad_reconciliation=reconciliation,
        scratchpad_reconciliation_detail=detail,
    )
