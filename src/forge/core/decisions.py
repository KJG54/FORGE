"""Append-only owner decisions and explicit supersession history."""

from __future__ import annotations

import re
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.decisions import DecisionRecord, DecisionSupersession
from forge.contracts.events import AuditEvent
from forge.core.authorization import require_owner
from forge.core.lifecycle import load_active_initiative
from forge.core.transitions import DECISION_RECORDED, DECISION_SUPERSEDED
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot

_SYMBOLIC_ID = re.compile(r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$")
_SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class DecisionResult:
    decision: DecisionRecord
    event: AuditEvent
    supersession: DecisionSupersession | None = None


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _decision_path(layout: RepositoryLayout, record_id: UUID) -> Path:
    return layout.decision_directory / f"{record_id}.json"


def _supersession_path(layout: RepositoryLayout, record_id: UUID) -> Path:
    return layout.decision_supersession_directory / f"{record_id}.json"


def _ensure_directory(path: Path, created: list[Path]) -> None:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Expected a governed directory at {path}")
        return
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create governed directory {path}: {error}") from error
    created.append(path)


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def list_decisions(layout: RepositoryLayout) -> tuple[DecisionRecord, ...]:
    load_active_initiative(layout)
    if not layout.decision_directory.exists():
        return ()
    return tuple(
        sorted(
            (
                load_record(path, DecisionRecord)
                for path in layout.decision_directory.glob("*.json")
            ),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def record_decision(
    layout: RepositoryLayout,
    *,
    decision_type: str,
    question: str,
    considered_options: tuple[str, ...],
    chosen_outcome: str,
    rationale: str,
    actor: Actor,
    affected_record_ids: tuple[UUID, ...] = (),
    bound_digests: tuple[str, ...] = (),
    supersedes: UUID | None = None,
) -> DecisionResult:
    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "record a governance decision")
    decision_type = _require_text("Decision type", decision_type)
    if not _SYMBOLIC_ID.fullmatch(decision_type):
        raise ConfigurationError(f"Invalid decision type: {decision_type!r}")
    question = _require_text("Decision question", question)
    considered_options = tuple(
        _require_text("Considered option", item) for item in considered_options
    )
    if not considered_options:
        raise ConfigurationError("At least one considered option is required")
    chosen_outcome = _require_text("Chosen outcome", chosen_outcome)
    rationale = _require_text("Decision rationale", rationale)
    if any(not _SHA256_DIGEST.fullmatch(item) for item in bound_digests):
        raise ConfigurationError("Every bound digest must be a lowercase sha256 digest")
    prior = None
    if supersedes is not None:
        if supersedes not in active.state.open_decision_ids:
            raise ConflictError(f"Decision {supersedes} is not active for supersession")
        prior = load_record(_decision_path(layout, supersedes), DecisionRecord)
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    decision_id = uuid4()
    supersession_id = uuid4() if prior is not None else None
    basis = (
        "configured owner explicitly superseded an active governance decision"
        if prior is not None
        else "configured owner recorded an explicit governance decision"
    )
    decision = DecisionRecord(
        id=decision_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=affected_record_ids,
        affected_digests=bound_digests,
        decision_type=decision_type,
        question=question,
        considered_options=considered_options,
        chosen_outcome=chosen_outcome,
        rationale=rationale,
        actor=actor,
        bound_digests=bound_digests,
    )
    supersession = None
    event_record_ids: tuple[UUID, ...]
    if prior is not None and supersession_id is not None:
        supersession = DecisionSupersession(
            id=supersession_id,
            initiative_id=active.initiative.id,
            actor_id=actor.id,
            recorded_at=now,
            event_sequence=sequence,
            authorization_basis=basis,
            tool_version=__version__,
            affected_record_ids=(prior.id, decision_id),
            affected_digests=bound_digests,
            prior_decision_id=prior.id,
            replacement_decision_id=decision_id,
            rationale=rationale,
            actor=actor,
        )
        event_record_ids = (
            decision_id,
            supersession_id,
            prior.id,
            *affected_record_ids,
        )
        event_type = DECISION_SUPERSEDED
    else:
        event_record_ids = (decision_id, *affected_record_ids)
        event_type = DECISION_RECORDED
    record_digests = [canonical_json_digest(decision.model_dump(mode="json"))]
    if supersession is not None:
        record_digests.append(canonical_json_digest(supersession.model_dump(mode="json")))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=event_type,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=tuple(dict.fromkeys(event_record_ids)),
        affected_digests=(*bound_digests, *record_digests),
        metadata={
            "decision_id": str(decision_id),
            **({"prior_decision_id": str(prior.id)} if prior is not None else {}),
            **(
                {"supersession_id": str(supersession_id)}
                if supersession_id is not None
                else {}
            ),
        },
    )
    created_directories: list[Path] = []
    paths = [_decision_path(layout, decision_id)]
    try:
        _ensure_directory(layout.decision_directory, created_directories)
        write_record(paths[0], decision)
        if supersession is not None and supersession_id is not None:
            _ensure_directory(layout.decision_supersession_directory, created_directories)
            paths.append(_supersession_path(layout, supersession_id))
            write_record(paths[-1], supersession)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event.id):
            for path in reversed(paths):
                path.unlink(missing_ok=True)
            for path in reversed(created_directories):
                with suppress(OSError):
                    path.rmdir()
        raise
    return DecisionResult(decision, event, supersession)
