"""Owner-governed emergency override declarations."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge import __version__
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.decisions import EmergencyOverride
from forge.contracts.events import AuditEvent
from forge.core.authorization import require_owner
from forge.core.lifecycle import load_active_initiative
from forge.core.scope_amendments import known_workflow_requirement_ids
from forge.core.transitions import EMERGENCY_OVERRIDE_RECORDED
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot

OVERRIDE_PERMANENCE_VALUES = ("temporary", "permanent")


@dataclass(frozen=True)
class EmergencyOverrideResult:
    override: EmergencyOverride
    event: AuditEvent


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _override_path(layout: RepositoryLayout, override_id: UUID) -> Path:
    return layout.emergency_override_directory / f"{override_id}.json"


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


def list_emergency_overrides(layout: RepositoryLayout) -> tuple[EmergencyOverride, ...]:
    load_active_initiative(
        layout,
        allow_terminal=True,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    if not layout.emergency_override_directory.exists():
        return ()
    return tuple(
        sorted(
            (
                load_record(path, EmergencyOverride)
                for path in layout.emergency_override_directory.glob("*.json")
            ),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def show_emergency_override(
    layout: RepositoryLayout,
    override_id: UUID,
) -> EmergencyOverride:
    match = next(
        (item for item in list_emergency_overrides(layout) if item.id == override_id),
        None,
    )
    if match is None:
        raise ConflictError(f"Unknown emergency override {override_id}")
    return match


def record_emergency_override(
    layout: RepositoryLayout,
    *,
    requirement_id: str | None,
    gate_id: str | None,
    rationale: str,
    residual_risk: str,
    permanence: str,
    review_requirement: str,
    actor: Actor,
) -> EmergencyOverrideResult:
    active = load_active_initiative(layout)
    require_owner(actor, active.initiative.owner_identity_id, "record an emergency override")
    if (requirement_id is None) == (gate_id is None):
        raise ConfigurationError(
            "Emergency override requires exactly one affected requirement or gate"
        )
    known_gates = {gate.id for gate in active.workflow.required_gates}
    if gate_id is not None:
        target_id = _require_text("Gate ID", gate_id)
        if target_id not in known_gates:
            raise ConflictError(f"Unknown locked-workflow gate {target_id!r}")
        target = f"gate:{target_id}"
    else:
        assert requirement_id is not None
        target_id = _require_text("Requirement ID", requirement_id)
        if target_id not in known_workflow_requirement_ids(active.workflow):
            raise ConflictError(f"Unknown locked-workflow requirement {target_id!r}")
        target = f"requirement:{target_id}"
    permanence = _require_text("Override permanence", permanence)
    if permanence not in OVERRIDE_PERMANENCE_VALUES:
        raise ConfigurationError(
            "Override permanence must be 'temporary' or 'permanent'"
        )
    rationale = _require_text("Override rationale", rationale)
    residual_risk = _require_text("Residual risk", residual_risk)
    review_requirement = _require_text("Review requirement", review_requirement)

    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    override_id = uuid4()
    workflow_digest = canonical_json_digest(active.workflow.model_dump(mode="json"))
    basis = (
        "configured owner recorded an emergency exception without bypassing governed "
        "verification or acceptance"
    )
    override = EmergencyOverride(
        id=override_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_digests=(workflow_digest,),
        affected_requirement_or_gate=target,
        rationale=rationale,
        residual_risk=residual_risk,
        permanence=permanence,
        review_requirement=review_requirement,
        actor=actor,
    )
    record_digest = canonical_json_digest(override.model_dump(mode="json"))
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=EMERGENCY_OVERRIDE_RECORDED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(override_id,),
        affected_digests=(workflow_digest, record_digest),
        metadata={
            "emergency_override_id": str(override_id),
            "affected_requirement_or_gate": target,
            "permanence": permanence,
            "workflow_id": active.workflow.id,
            "workflow_version": active.workflow.version,
            "workflow_digest": workflow_digest,
        },
    )
    path = _override_path(layout, override_id)
    created_directory = _ensure_directory(path.parent)
    try:
        write_record(path, override)
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
    return EmergencyOverrideResult(override, event)
