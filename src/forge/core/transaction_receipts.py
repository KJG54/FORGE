"""Canonical concise receipts derived from validated journal transactions and state."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, cast
from uuid import UUID

from pydantic import ValidationError

from forge.contracts.events import AuditEvent
from forge.contracts.initiatives import InitiativeReference
from forge.contracts.state import IntegrityState
from forge.core.owner_ceremony import owner_action_presentation
from forge.core.status import StatusReport, inspect_status
from forge.errors import ForgeError, IntegrityError
from forge.storage.idempotency import load_completed_idempotent_transaction
from forge.storage.repository import RepositoryLayout


class TransactionDisposition(StrEnum):
    COMMITTED = "committed"
    REPLAYED = "replayed"
    REFUSED = "refused"


@dataclass(frozen=True)
class GovernedPosition:
    """Comparable validated governed position used only for honest refusal reporting."""

    active_initiative_id: UUID | None
    active_lifecycle: str | None
    active_step_id: str | None
    active_step_state: str | None
    journal_head_sequence: int | None
    journal_head_hash: str | None
    archives: tuple[tuple[UUID, str, int, str | None], ...]


@dataclass(frozen=True)
class TransactionReceiptResult:
    disposition: TransactionDisposition
    command: str
    idempotency_key: str | None
    facts: tuple[str, ...]
    event_ids: tuple[UUID, ...]
    sequence_start: int | None
    sequence_end: int | None
    meaning: str


_EVENT_FIELDS: Final[dict[str, tuple[str, ...]]] = {
    "acceptance-recorded": ("step_id", "acceptance_id"),
    "acceptance-revoked": ("acceptance_id", "revocation_id"),
    "artifact-registered": ("artifact_role", "artifact_id", "revision_id"),
    "artifact-revised": ("artifact_role", "artifact_id", "revision_id"),
    "check-recorded": ("step_id", "check_id", "check_result_id", "outcome"),
    "claim-recorded": ("step_id", "claim_id"),
    "decision-recorded": ("decision_type", "decision_id"),
    "decision-superseded": ("decision_id", "prior_decision_id", "supersession_id"),
    "evidence-registered": ("step_id", "evidence_id"),
    "initiative-created": ("pack_id", "workflow_id"),
    "initiative-paused": ("pause_event_id",),
    "initiative-resumed": ("pause_event_id",),
    "scope-amended": ("scope_amendment_id", "workflow_return_step_id"),
    "step-transitioned": ("step_id", "transition_id", "destination_state"),
}


def _healthy_report(layout: RepositoryLayout) -> StatusReport | None:
    try:
        report = inspect_status(layout)
    except ForgeError:
        return None
    if report.integrity_state is not IntegrityState.HEALTHY:
        return None
    return report


def capture_governed_position(layout: RepositoryLayout) -> GovernedPosition | None:
    """Capture only a fully validated position; return none when safety is uncertain."""

    report = _healthy_report(layout)
    if report is None:
        return None
    state = report.state
    step_id = state.current_step_id if state is not None else None
    active_step_state = (
        state.step_states.get(step_id)
        if state is not None and step_id is not None
        else None
    )
    step_state = active_step_state.value if active_step_state is not None else None
    return GovernedPosition(
        active_initiative_id=report.initiative.id if report.initiative is not None else None,
        active_lifecycle=(
            state.lifecycle_state.value
            if state is not None and state.lifecycle_state is not None
            else None
        ),
        active_step_id=step_id,
        active_step_state=step_state,
        journal_head_sequence=(state.journal_head_sequence if state is not None else None),
        journal_head_hash=(state.journal_head_hash if state is not None else None),
        archives=tuple(
            (
                summary.initiative_id,
                summary.archive_digest,
                summary.journal_head_sequence,
                summary.journal_head_hash,
            )
            for summary in report.archive_summaries
        ),
    )


def _safe_value(value: object) -> str | None:
    if isinstance(value, str | int | bool):
        return str(value).lower() if isinstance(value, bool) else _compact_text(str(value))
    if isinstance(value, UUID):
        return str(value)
    return None


def _compact_text(value: str) -> str:
    return " ".join(value.split())


def _predecessor_ids(event: AuditEvent) -> tuple[UUID, ...]:
    raw = event.metadata.get("predecessor_references")
    if not isinstance(raw, list):
        return ()
    try:
        references = tuple(
            InitiativeReference.model_validate(item) for item in cast(list[object], raw)
        )
    except ValidationError:
        return ()
    return tuple(reference.initiative_id for reference in references)


def _event_fact(event: AuditEvent) -> str:
    details = [f"initiative={event.initiative_id}"]
    if event.run_id is not None:
        details.append(f"run_id={event.run_id}")
    if event.event_type == "claim-recorded":
        details.append(f"actor_type={event.actor.actor_type.value}")
        details.append(
            "actor=" + json.dumps(_compact_text(event.actor.display_label), ensure_ascii=True)
        )
        operator_type = _safe_value(event.metadata.get("operator_type"))
        if operator_type is not None:
            details.append(f"operator_type={operator_type}")
            details.append("operator_attribution=caller-declared-not-authentication")
        operator_session = _safe_value(event.metadata.get("operator_session_reference"))
        if operator_session is not None:
            details.append(
                "operator_session_reference="
                + json.dumps(operator_session, ensure_ascii=True)
            )
    predecessors = _predecessor_ids(event)
    if predecessors:
        details.append("predecessors=" + ",".join(str(item) for item in predecessors))
    for field in _EVENT_FIELDS.get(event.event_type, ()):
        rendered = _safe_value(event.metadata.get(field))
        if rendered is not None:
            details.append(f"{field}={rendered}")
    if len(details) == 1 and event.affected_record_ids:
        details.append(
            "records=" + ",".join(str(record_id) for record_id in event.affected_record_ids)
        )
    return f"{event.event_type} ({'; '.join(details)})"


def _meaning(report: StatusReport) -> str:
    parts = [
        f"repository={report.repository_state.value}",
        f"integrity={report.integrity_state.value}",
    ]
    if report.initiative is not None:
        parts.append(f"initiative={report.initiative.id}")
    if report.state is not None and report.state.lifecycle_state is not None:
        parts.append(f"lifecycle={report.state.lifecycle_state.value}")
        step_id = report.state.current_step_id
        if step_id is not None:
            step_state = report.state.step_states.get(step_id)
            if step_state is not None:
                parts.append(f"step={step_id}:{step_state.value}")
    blockers = (
        " | ".join(_compact_text(item) for item in report.blockers)
        if report.blockers
        else "none"
    )
    actions = (
        ", ".join(_compact_text(item) for item in report.next_actions)
        if report.next_actions
        else "none"
    )
    ready_actions = (
        ", ".join(_compact_text(item) for item in report.executable_actions)
        if report.executable_actions
        else "none"
    )
    parts.append(f"blockers={blockers}")
    parts.append(f"legal_actions={actions}")
    parts.append(f"ready_actions={ready_actions}")
    owner_actions = tuple(
        presentation
        for action in report.next_actions
        if (presentation := owner_action_presentation(action)) is not None
    )
    for presentation in owner_actions:
        parts.append(
            "owner_command=" + json.dumps(presentation.command, ensure_ascii=True)
        )
        parts.append(
            "owner_consequence="
            + json.dumps(_compact_text(presentation.consequence), ensure_ascii=True)
        )
    if owner_actions:
        parts.append("owner_ceremony=caller-attribution-is-not-authentication")
    return "; ".join(parts)


def build_transaction_receipt(
    layout: RepositoryLayout,
    *,
    key: str,
    replayed: bool,
) -> TransactionReceiptResult:
    """Derive one receipt from an exact completion record and replay-validated state."""

    transaction = load_completed_idempotent_transaction(layout, key)
    report = _healthy_report(layout)
    if report is None:
        raise IntegrityError("Cannot render a transaction receipt from unhealthy governed state")
    sequences = tuple(event.sequence for event in transaction.events)
    if not sequences:
        raise IntegrityError("Completed transaction has no committed events")
    return TransactionReceiptResult(
        disposition=(
            TransactionDisposition.REPLAYED if replayed else TransactionDisposition.COMMITTED
        ),
        command=transaction.receipt.command.replace("_", " "),
        idempotency_key=transaction.receipt.key,
        facts=tuple(_event_fact(event) for event in transaction.events),
        event_ids=tuple(event.id for event in transaction.events),
        sequence_start=min(sequences),
        sequence_end=max(sequences),
        meaning=_meaning(report),
    )


def build_refusal_receipt(
    layout: RepositoryLayout,
    *,
    command: str,
    error: ForgeError,
    position_before: GovernedPosition | None,
) -> TransactionReceiptResult:
    """Report a refusal without asserting unchanged state unless validation proves it."""

    report = _healthy_report(layout)
    position_after = capture_governed_position(layout) if report is not None else None
    unchanged = position_before is not None and position_after == position_before
    if unchanged and report is not None:
        meaning = (
            f"Refused {command.replace('_', ' ')}: {_compact_text(str(error))}; "
            "validated no new governed events; "
        )
        meaning += _meaning(report)
    else:
        meaning = (
            f"Refused {command.replace('_', ' ')}: {_compact_text(str(error))}; "
            "governed commit state is not "
            "asserted; run forge doctor and inspect history before retrying"
        )
    return TransactionReceiptResult(
        disposition=TransactionDisposition.REFUSED,
        command=command.replace("_", " "),
        idempotency_key=None,
        facts=(),
        event_ids=(),
        sequence_start=None,
        sequence_end=None,
        meaning=meaning,
    )


def render_transaction_receipt(result: TransactionReceiptResult) -> str:
    """Render the one canonical concise receipt dialect."""

    if result.disposition is TransactionDisposition.REFUSED:
        return f"Means    -> {result.meaning}"
    if (
        result.idempotency_key is None
        or result.sequence_start is None
        or result.sequence_end is None
        or not result.event_ids
    ):
        raise IntegrityError("Committed transaction receipt lacks exact event identity")
    facts = "; ".join(result.facts)
    if result.disposition is TransactionDisposition.REPLAYED:
        facts = (
            f"Idempotent replay of {result.command} transaction {result.idempotency_key}; "
            f"zero new events; original facts: {facts}"
        )
    else:
        facts = f"{facts}; transaction={result.command}:{result.idempotency_key}"
    event_ids = ",".join(str(event_id) for event_id in result.event_ids)
    return (
        f"Recorded -> {facts} [sequence {result.sequence_start}-{result.sequence_end}; "
        f"events {event_ids}]\nMeans    -> {result.meaning}"
    )
