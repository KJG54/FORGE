"""Append-only owner trust lifecycle for one initiative's exact locked data pack."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.packs import PackTrustDecision, PackTrustState
from forge.core.authorization import require_owner
from forge.core.transitions import PACK_TRUST_CHANGED
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class PackTrustChangeResult:
    decision: PackTrustDecision
    event: AuditEvent


def _decision_path(layout: RepositoryLayout, decision_id: UUID) -> Path:
    return layout.pack_trust_decision_directory / f"{decision_id}.json"


def _ensure_record_directory(path: Path) -> bool:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Expected a governed directory at {path}")
        return False
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create governed directory {path}: {error}") from error
    return True


def _event_committed(layout: RepositoryLayout, event_id: UUID) -> bool:
    try:
        return any(event.id == event_id for event in read_journal(layout.event_journal_file))
    except IntegrityError:
        return True


def pack_trust_history(
    layout: RepositoryLayout,
    initial: PackTrustDecision,
    events: tuple[AuditEvent, ...],
) -> tuple[PackTrustDecision, ...]:
    """Resolve immutable trust history in authoritative journal order."""

    history = [initial]
    current = initial
    for event in events:
        if event.event_type != PACK_TRUST_CHANGED:
            continue
        raw_decision_id = event.metadata.get("pack_trust_decision_id")
        raw_prior_id = event.metadata.get("prior_pack_trust_decision_id")
        if not isinstance(raw_decision_id, str) or not isinstance(raw_prior_id, str):
            raise IntegrityError(f"Pack trust event {event.id} has invalid decision metadata")
        try:
            decision_id = UUID(raw_decision_id)
            prior_id = UUID(raw_prior_id)
        except ValueError as error:
            raise IntegrityError(f"Pack trust event {event.id} has invalid decision IDs") from error
        decision = load_record(_decision_path(layout, decision_id), PackTrustDecision)
        if prior_id != current.id:
            raise IntegrityError(f"Pack trust event {event.id} does not extend current history")
        history.append(decision)
        current = decision
    return tuple(history)


def current_pack_trust(
    layout: RepositoryLayout,
    initial: PackTrustDecision,
    events: tuple[AuditEvent, ...],
) -> PackTrustDecision:
    return pack_trust_history(layout, initial, events)[-1]


def require_pack_trusted(decision: PackTrustDecision) -> None:
    if decision.trust_state is PackTrustState.UNTRUSTED:
        raise ConflictError(
            f"Locked pack {decision.pack_id}@{decision.pack_version} is untrusted; "
            "inspect and restore data trust before workflow-dependent mutation"
        )


def change_pack_trust(
    layout: RepositoryLayout,
    *,
    pack_id: str,
    trust_state: PackTrustState,
    rationale: str,
    actor: Actor,
) -> PackTrustChangeResult:
    from forge.core.lifecycle import load_active_initiative

    active = load_active_initiative(
        layout,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    require_owner(actor, active.initiative.owner_identity_id, "change pack data trust")
    if pack_id.strip() != active.pack_manifest.id:
        raise ConflictError(
            f"Active initiative locks {active.pack_manifest.id!r}, not {pack_id.strip()!r}"
        )
    rationale = rationale.strip()
    if not rationale:
        raise ConfigurationError("Pack trust rationale must not be empty")
    prior = active.pack_trust
    if prior.trust_state is trust_state:
        raise ConflictError(
            f"Pack {prior.pack_id}@{prior.pack_version} is already {trust_state.value}"
        )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    decision_id = uuid4()
    event_id = uuid4()
    basis = (
        "configured owner explicitly trusted the exact locked pack as data"
        if trust_state is PackTrustState.TRUSTED_DATA
        else "configured owner withdrew data trust from the exact locked pack"
    )
    decision = PackTrustDecision(
        id=decision_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=(prior.id,),
        affected_digests=(active.pack_manifest.integrity_digest,),
        pack_id=active.pack_manifest.id,
        pack_version=active.pack_manifest.version,
        trust_state=trust_state,
        rationale=rationale,
        actor=actor,
    )
    record_digest = canonical_json_digest(decision.model_dump(mode="json"))
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=PACK_TRUST_CHANGED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(decision_id, prior.id),
        affected_digests=(active.pack_manifest.integrity_digest, record_digest),
        metadata={
            "pack_id": active.pack_manifest.id,
            "pack_version": active.pack_manifest.version,
            "pack_trust_decision_id": str(decision_id),
            "prior_pack_trust_decision_id": str(prior.id),
            "trust_state": trust_state.value,
        },
    )
    path = _decision_path(layout, decision_id)
    created = _ensure_record_directory(path.parent)
    try:
        write_record(path, decision)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event.id):
            path.unlink(missing_ok=True)
            if created:
                with suppress(OSError):
                    path.parent.rmdir()
        raise
    return PackTrustChangeResult(decision, event)
