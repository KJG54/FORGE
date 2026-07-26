"""Owner risk acceptance bound to exact emergency override records."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.decisions import EmergencyOverride, RiskAcceptance
from forge.contracts.events import AuditEvent
from forge.core.authorization import require_owner
from forge.core.lifecycle import load_active_initiative
from forge.core.overrides import list_emergency_overrides, show_emergency_override
from forge.core.transitions import RISK_ACCEPTED
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot


@dataclass(frozen=True)
class RiskAcceptanceResult:
    acceptance: RiskAcceptance
    override: EmergencyOverride
    event: AuditEvent


@dataclass(frozen=True)
class RiskAcceptanceView:
    acceptance: RiskAcceptance
    override: EmergencyOverride
    stale: bool


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _acceptance_path(layout: RepositoryLayout, acceptance_id: UUID) -> Path:
    return layout.risk_acceptance_directory / f"{acceptance_id}.json"


def _ensure_directory(path: Path) -> bool:
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


def list_risk_acceptances(layout: RepositoryLayout) -> tuple[RiskAcceptanceView, ...]:
    active = load_active_initiative(
        layout,
        allow_terminal=True,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    if not layout.risk_acceptance_directory.exists():
        return ()
    overrides = {item.id: item for item in list_emergency_overrides(layout)}
    views: list[RiskAcceptanceView] = []
    for path in layout.risk_acceptance_directory.glob("*.json"):
        acceptance = load_record(path, RiskAcceptance)
        if (
            len(acceptance.affected_record_ids) != 1
            or acceptance.affected_record_ids[0] not in overrides
        ):
            raise IntegrityError(
                f"Risk acceptance {acceptance.id} lacks one governed emergency override"
            )
        views.append(
            RiskAcceptanceView(
                acceptance,
                overrides[acceptance.affected_record_ids[0]],
                acceptance.id in active.state.stale_record_ids,
            )
        )
    return tuple(
        sorted(
            views,
            key=lambda item: (item.acceptance.event_sequence, str(item.acceptance.id)),
        )
    )


def show_risk_acceptance(
    layout: RepositoryLayout,
    acceptance_id: UUID,
) -> RiskAcceptanceView:
    match = next(
        (
            item
            for item in list_risk_acceptances(layout)
            if item.acceptance.id == acceptance_id
        ),
        None,
    )
    if match is None:
        raise ConflictError(f"Unknown risk acceptance {acceptance_id}")
    return match


def current_risk_acceptance_for_override(
    layout: RepositoryLayout,
    override_id: UUID,
) -> RiskAcceptanceView | None:
    matches = [
        item
        for item in list_risk_acceptances(layout)
        if item.override.id == override_id and not item.stale
    ]
    if len(matches) > 1:
        raise IntegrityError(
            f"Emergency override {override_id} has multiple current risk acceptances"
        )
    return matches[0] if matches else None


def record_risk_acceptance(
    layout: RepositoryLayout,
    *,
    override_id: UUID,
    rationale: str,
    residual_impact: str,
    review_condition: str | None,
    actor: Actor,
) -> RiskAcceptanceResult:
    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "accept residual risk")
    override = show_emergency_override(layout, override_id)
    if override.id in active.state.stale_record_ids:
        raise ConflictError(f"Emergency override {override_id} is stale")
    if current_risk_acceptance_for_override(layout, override_id) is not None:
        raise ConflictError(
            f"Emergency override {override_id} already has a current risk acceptance"
        )
    rationale = _require_text("Risk-acceptance rationale", rationale)
    residual_impact = _require_text("Residual impact", residual_impact)
    if review_condition is not None:
        review_condition = _require_text("Review condition", review_condition)

    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    acceptance_id = uuid4()
    override_digest = canonical_json_digest(override.model_dump(mode="json"))
    affected_digests = (override_digest, *override.affected_digests)
    basis = (
        "configured owner accepted the residual risk of one exact emergency override "
        "without waiving workflow progression"
    )
    acceptance = RiskAcceptance(
        id=acceptance_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=(override_id,),
        affected_digests=affected_digests,
        risk=override.residual_risk,
        rationale=rationale,
        residual_impact=residual_impact,
        review_condition=review_condition,
        actor=actor,
    )
    record_digest = canonical_json_digest(acceptance.model_dump(mode="json"))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=RISK_ACCEPTED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(acceptance_id, override_id),
        affected_digests=(*affected_digests, record_digest),
        metadata={
            "risk_acceptance_id": str(acceptance_id),
            "emergency_override_id": str(override_id),
            "emergency_override_digest": override_digest,
        },
    )
    path = _acceptance_path(layout, acceptance_id)
    created_directory = _ensure_directory(path.parent)
    try:
        write_record(path, acceptance)
        append_event_and_update_snapshot(
            layout.event_journal_file,
            layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(layout, event.id):
            path.unlink(missing_ok=True)
            if created_directory:
                with suppress(OSError):
                    path.parent.rmdir()
        raise
    return RiskAcceptanceResult(acceptance, override, event)
