"""Cross-check governed records against journal events and preserved bytes."""

from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID

from forge.contracts.actors import ActorType
from forge.contracts.agents import AgentResult
from forge.contracts.archives import AbandonmentRecord, ClosureRecord
from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.contracts.capabilities import (
    CapabilityApproval,
    CapabilityRevocation,
    CapabilityTrustState,
    SideEffectClass,
)
from forge.contracts.decisions import (
    ApprovalRevocation,
    DecisionRecord,
    DecisionSupersession,
    ScopeAmendment,
)
from forge.contracts.events import AuditEvent
from forge.contracts.idempotency import (
    CommandRecoveryRecord,
    IdempotencyEventReference,
    IdempotencyReceipt,
)
from forge.contracts.initiatives import Initiative
from forge.contracts.migrations import MigrationRecord
from forge.contracts.packs import PackManifest, PackTrustDecision
from forge.contracts.recovery import (
    JournalDamageCondition,
    JournalRecoveryRecord,
    JournalRecoverySnapshotCondition,
    RecoveryRecord,
    SnapshotCondition,
)
from forge.contracts.runs import RunRecord
from forge.contracts.state import (
    InitiativeLifecycleState,
    IntegrityState,
    MaterializedState,
    RunState,
    StepState,
)
from forge.contracts.verification import (
    AcceptanceRecord,
    CheckExecutionStatus,
    CheckOutcome,
    CheckResult,
    Claim,
    EvidencePacket,
)
from forge.contracts.workflows import CancellationBehavior, WorkflowDefinition
from forge.core.authorization import migration_actor
from forge.core.successors import (
    load_predecessor_artifact_revision,
    predecessor_artifact_source_reference,
)
from forge.core.transitions import (
    ACCEPTANCE_RECORDED,
    ACCEPTANCE_REVOKED,
    ADAPTER_RUN_EXECUTED,
    ARTIFACT_REGISTERED,
    ARTIFACT_REVISED,
    CAPABILITY_APPROVED,
    CAPABILITY_REVOKED,
    CHECK_RECORDED,
    CLAIM_RECORDED,
    COMMAND_RECOVERED,
    DECISION_RECORDED,
    DECISION_SUPERSEDED,
    EVIDENCE_REGISTERED,
    INITIATIVE_ABANDONED,
    INITIATIVE_CLOSED,
    INTEGRITY_RECOVERED,
    JOURNAL_RECOVERED,
    PACK_TRUST_CHANGED,
    RESULT_IMPORTED,
    RUN_CANCELLED,
    SCHEMA_MIGRATED,
    SCOPE_AMENDED,
    STEP_TRANSITIONED,
    VALIDATOR_RUN_STARTED,
    WorkflowStateReducer,
)
from forge.errors import IntegrityError, SecurityError
from forge.storage.canonical import sha256_digest
from forge.storage.configuration import load_configuration
from forge.storage.journal import (
    MAX_JOURNAL_RECOVERY_BYTES,
    inspect_journal_recovery_candidate,
    read_journal,
)
from forge.storage.migrations import (
    LEGACY_JOURNAL_MIGRATION,
    LEGACY_JOURNAL_MIGRATION_ID,
    MAX_MIGRATION_SOURCE_BYTES,
)
from forge.storage.objects import canonical_json_digest, verify_preserved_object
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import MAX_SNAPSHOT_BYTES, replay_events


def _uuid_metadata(event: AuditEvent, key: str) -> UUID:
    value = event.metadata.get(key)
    if not isinstance(value, str):
        raise IntegrityError(f"Event {event.id} requires UUID metadata field {key!r}")
    try:
        return UUID(value)
    except ValueError as error:
        raise IntegrityError(f"Event {event.id} has invalid UUID metadata field {key!r}") from error


def _uuid_list_metadata(event: AuditEvent, key: str) -> tuple[UUID, ...]:
    value = event.metadata.get(key)
    if not isinstance(value, list):
        raise IntegrityError(f"Event {event.id} requires UUID-list metadata field {key!r}")
    items = cast("list[object]", value)
    if not all(isinstance(item, str) for item in items):
        raise IntegrityError(f"Event {event.id} requires UUID-list metadata field {key!r}")
    try:
        return tuple(UUID(item) for item in cast("list[str]", value))
    except ValueError as error:
        raise IntegrityError(f"Event {event.id} has invalid UUID metadata field {key!r}") from error


def _string_list_matches(value: object, expected: tuple[str, ...]) -> bool:
    if not isinstance(value, list):
        return False
    items = cast("list[object]", value)
    return all(isinstance(item, str) for item in items) and tuple(
        cast("list[str]", items)
    ) == expected


def _record_path(layout: RepositoryLayout, artifact_id: UUID, revision_number: int) -> Path:
    return layout.artifact_record_directory / f"{artifact_id}.{revision_number}.json"


def _revision_path(layout: RepositoryLayout, revision_id: UUID) -> Path:
    return layout.artifact_revision_directory / f"{revision_id}.json"


def _claim_path(layout: RepositoryLayout, claim_id: UUID) -> Path:
    return layout.claim_directory / f"{claim_id}.json"


def _check_path(layout: RepositoryLayout, check_id: UUID) -> Path:
    return layout.check_directory / f"{check_id}.json"


def _evidence_path(layout: RepositoryLayout, evidence_id: UUID) -> Path:
    return layout.evidence_directory / f"{evidence_id}.json"


def _acceptance_path(layout: RepositoryLayout, acceptance_id: UUID) -> Path:
    return layout.acceptance_directory / f"{acceptance_id}.json"


def _revocation_path(layout: RepositoryLayout, revocation_id: UUID) -> Path:
    return layout.revocation_directory / f"{revocation_id}.json"


def _capability_approval_path(layout: RepositoryLayout, approval_id: UUID) -> Path:
    return layout.capability_approval_directory / f"{approval_id}.json"


def _capability_revocation_path(layout: RepositoryLayout, revocation_id: UUID) -> Path:
    return layout.capability_revocation_directory / f"{revocation_id}.json"


def _pack_trust_decision_path(layout: RepositoryLayout, decision_id: UUID) -> Path:
    return layout.pack_trust_decision_directory / f"{decision_id}.json"


def _decision_path(layout: RepositoryLayout, decision_id: UUID) -> Path:
    return layout.decision_directory / f"{decision_id}.json"


def _supersession_path(layout: RepositoryLayout, supersession_id: UUID) -> Path:
    return layout.decision_supersession_directory / f"{supersession_id}.json"


def _scope_amendment_path(layout: RepositoryLayout, amendment_id: UUID) -> Path:
    return layout.scope_amendment_directory / f"{amendment_id}.json"


def _imported_result_path(layout: RepositoryLayout, result_id: UUID) -> Path:
    return layout.imported_result_directory / f"{result_id}.json"


def _closure_path(layout: RepositoryLayout, closure_id: UUID) -> Path:
    return layout.closure_directory / f"{closure_id}.json"


def _abandonment_path(layout: RepositoryLayout, abandonment_id: UUID) -> Path:
    return layout.abandonment_directory / f"{abandonment_id}.json"


def _recovery_path(layout: RepositoryLayout, recovery_id: UUID) -> Path:
    return layout.recovery_record_directory / f"{recovery_id}.json"


def _command_recovery_path(layout: RepositoryLayout, recovery_id: UUID) -> Path:
    return layout.command_recovery_record_directory / f"{recovery_id}.json"


def _recovery_journal_path(layout: RepositoryLayout, recovery_id: UUID) -> Path:
    return layout.recovery_journal_directory / f"{recovery_id}.events.jsonl"


def _migration_path(layout: RepositoryLayout, migration_id: UUID) -> Path:
    return layout.migration_record_directory / f"{migration_id}.json"


def _migration_source_path(layout: RepositoryLayout, migration_id: UUID) -> Path:
    return layout.migration_source_directory / f"{migration_id}.events.jsonl"


def _validate_common(record: object, event: AuditEvent, record_id: UUID) -> None:
    initiative_id = getattr(record, "initiative_id", None)
    actor_id = getattr(record, "actor_id", None)
    event_sequence = getattr(record, "event_sequence", None)
    if (
        initiative_id != event.initiative_id
        or actor_id != event.actor.id
        or event_sequence != event.sequence
        or record_id not in event.affected_record_ids
    ):
        raise IntegrityError(f"Governed record {record_id} does not match event {event.id}")


def _check_digest(check: CheckResult) -> str:
    payload: dict[str, object] = {
        "actor": check.actor.model_dump(mode="json"),
        "check_id": check.check_id,
        "check_version": check.check_version,
        "ended_at": check.ended_at.isoformat(),
        "exit_status": check.exit_status,
        "invocation_metadata": check.invocation_metadata,
        "limitations": list(check.limitations),
        "outcome": check.outcome.value,
        "started_at": check.started_at.isoformat(),
        "target_artifact_revision_ids": [
            str(item) for item in check.target_artifact_revision_ids
        ],
    }
    if check.capability_id is not None:
        payload.update(
            {
                "capability_approval_id": str(check.capability_approval_id),
                "capability_id": check.capability_id,
                "execution_status": (
                    check.execution_status.value
                    if check.execution_status is not None
                    else None
                ),
                "invocation_digest": check.invocation_digest,
                "run_id": str(check.run_id),
                "stderr_byte_count": check.stderr_byte_count,
                "stderr_capture_path": check.stderr_capture_path,
                "stderr_digest": check.stderr_digest,
                "stdout_byte_count": check.stdout_byte_count,
                "stdout_capture_path": check.stdout_capture_path,
                "stdout_digest": check.stdout_digest,
            }
        )
    return canonical_json_digest(payload)


def _evidence_digest(evidence: EvidencePacket) -> str:
    return canonical_json_digest(
        {
            "actor": evidence.actor.model_dump(mode="json"),
            "artifact_revision_ids": [str(item) for item in evidence.artifact_revision_ids],
            "check_result_ids": [str(item) for item in evidence.check_result_ids],
            "claim_ids": [str(item) for item in evidence.claim_ids],
            "limitations": list(evidence.limitations),
            "purpose": evidence.purpose,
        }
    )


def _validate_directory(path: Path, expected: set[Path]) -> None:
    if not expected and not path.exists():
        return
    if path.is_symlink():
        raise SecurityError(f"Governed record directory is a symbolic link: {path}")
    if not path.is_dir():
        raise IntegrityError(f"Governed record directory is missing: {path}")
    actual = set(path.iterdir())
    unexpected = actual - expected
    missing = expected - actual
    if unexpected or missing:
        raise IntegrityError(
            f"Governed record inventory mismatch at {path}: "
            f"missing={sorted(item.name for item in missing)}, "
            f"unexpected={sorted(item.name for item in unexpected)}"
        )
    if any(item.is_symlink() or not item.is_file() for item in actual):
        raise IntegrityError(f"Governed record inventory contains a non-regular file: {path}")


def _condition_record_ids(event: AuditEvent, condition: str) -> tuple[UUID, ...]:
    mapping = event.metadata.get("condition_record_ids")
    if not isinstance(mapping, dict):
        raise IntegrityError(f"Transition event {event.id} lacks condition record mapping")
    values = cast("dict[object, object]", mapping).get(condition)
    if not isinstance(values, list):
        raise IntegrityError(
            f"Transition event {event.id} lacks governed support for {condition!r}"
        )
    items = cast("list[object]", values)
    if not all(isinstance(item, str) for item in items):
        raise IntegrityError(
            f"Transition event {event.id} lacks governed support for {condition!r}"
        )
    try:
        record_ids = tuple(UUID(item) for item in cast("list[str]", values))
    except ValueError as error:
        raise IntegrityError(f"Transition event {event.id} has invalid condition UUIDs") from error
    if not record_ids or not set(record_ids).issubset(event.affected_record_ids):
        raise IntegrityError(f"Transition event {event.id} has unbound condition records")
    return record_ids


def validate_governed_records(
    layout: RepositoryLayout,
    events: tuple[AuditEvent, ...],
    state: MaterializedState,
    workflow: WorkflowDefinition,
) -> None:
    """Validate all implemented M1 record and event dependencies."""
    expected_artifact_records: set[Path] = set()
    expected_revisions: set[Path] = set()
    expected_claims: set[Path] = set()
    expected_checks: set[Path] = set()
    expected_evidence: set[Path] = set()
    expected_acceptances: set[Path] = set()
    expected_revocations: set[Path] = set()
    expected_capability_approvals: set[Path] = set()
    expected_capability_revocations: set[Path] = set()
    expected_pack_trust_decisions: set[Path] = set()
    expected_decisions: set[Path] = set()
    expected_supersessions: set[Path] = set()
    expected_scope_amendments: set[Path] = set()
    expected_imported_results: set[Path] = set()
    expected_closures: set[Path] = set()
    expected_abandonments: set[Path] = set()
    expected_runs: set[Path] = set()
    expected_validator_runs: set[Path] = set()
    expected_command_recoveries: set[Path] = set()
    expected_recoveries: set[Path] = set()
    expected_recovery_snapshots: set[Path] = set()
    expected_recovery_journals: set[Path] = set()
    expected_migrations: set[Path] = set()
    expected_migration_sources: set[Path] = set()
    revisions_by_id: dict[UUID, ArtifactRevision] = {}
    artifact_roles: dict[UUID, str] = {}
    current_revision_ids: dict[UUID, UUID] = {}
    claims_by_id: dict[UUID, Claim] = {}
    checks_by_id: dict[UUID, CheckResult] = {}
    evidence_by_id: dict[UUID, EvidencePacket] = {}
    acceptances_by_id: dict[UUID, AcceptanceRecord] = {}
    acceptance_steps: dict[UUID, str] = {}
    record_steps: dict[UUID, str] = {}
    decisions_by_id: dict[UUID, DecisionRecord] = {}
    runs_by_id: dict[UUID, RunRecord] = {}
    validator_runs_by_id: dict[UUID, RunRecord] = {}
    capability_approvals_by_id: dict[UUID, CapabilityApproval] = {}
    revoked_capability_approval_ids: set[UUID] = set()
    used_capability_approval_ids: set[UUID] = set()
    current_pack_trust = load_record(layout.pack_trust_file, PackTrustDecision)
    locked_pack = load_record(layout.pack_lock_file, PackManifest)
    adapter_execution_run_ids: set[UUID] = set()
    revoked_acceptance_ids: set[UUID] = set()
    stale_ids: set[UUID] = set()
    seen_event_record_ids: set[UUID] = set()
    owner_id = load_configuration(layout.configuration_file).owner.id
    initiative = load_record(layout.initiative_file, Initiative)
    states_before: dict[UUID, MaterializedState | None] = {}
    replayed_state: MaterializedState | None = None
    replay_reducer = WorkflowStateReducer(workflow, owner_id)
    for replay_event in events:
        states_before[replay_event.id] = replayed_state
        replayed_state = replay_reducer(replayed_state, replay_event)
        replayed_state = replayed_state.model_copy(
            update={
                "integrity_state": IntegrityState.HEALTHY,
                "journal_head_sequence": replay_event.sequence,
                "journal_head_hash": replay_event.event_hash,
            }
        )

    for event in events:
        if event.event_type == PACK_TRUST_CHANGED:
            decision_id = _uuid_metadata(event, "pack_trust_decision_id")
            prior_id = _uuid_metadata(event, "prior_pack_trust_decision_id")
            path = _pack_trust_decision_path(layout, decision_id)
            expected_pack_trust_decisions.add(path)
            decision = load_record(path, PackTrustDecision)
            _validate_common(decision, event, decision_id)
            record_digest = canonical_json_digest(decision.model_dump(mode="json"))
            if (
                prior_id != current_pack_trust.id
                or decision.id != decision_id
                or decision.actor != event.actor
                or decision.actor_id != owner_id
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or decision.pack_id != locked_pack.id
                or decision.pack_version != locked_pack.version
                or decision.trust_state.value != event.metadata.get("trust_state")
                or event.metadata.get("pack_id") != locked_pack.id
                or event.metadata.get("pack_version") != locked_pack.version
                or decision.trust_state is current_pack_trust.trust_state
                or decision.affected_record_ids != (prior_id,)
                or decision.affected_digests != (locked_pack.integrity_digest,)
                or event.affected_record_ids != (decision_id, prior_id)
                or locked_pack.integrity_digest not in event.affected_digests
                or record_digest not in event.affected_digests
            ):
                raise IntegrityError(f"Pack trust decision does not match event {event.id}")
            current_pack_trust = decision
        elif event.event_type == CAPABILITY_APPROVED:
            approval_id = _uuid_metadata(event, "approval_id")
            path = _capability_approval_path(layout, approval_id)
            expected_capability_approvals.add(path)
            approval = load_record(path, CapabilityApproval)
            _validate_common(approval, event, approval_id)
            record_digest = canonical_json_digest(approval.model_dump(mode="json"))
            if (
                approval.id != approval_id
                or approval.owner_actor != event.actor
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or approval.approval_event_id != event.id
                or approval.capability_id != event.metadata.get("capability_id")
                or approval.capability_version != event.metadata.get("capability_version")
                or approval.provider_version != event.metadata.get("provider_version")
                or approval.approval_scope.value != event.metadata.get("approval_scope")
                or approval.capability_digest not in event.affected_digests
                or record_digest not in event.affected_digests
                or approval_id in capability_approvals_by_id
                or approval.affected_record_ids != (approval_id,)
                or approval.affected_digests != (approval.capability_digest,)
            ):
                raise IntegrityError(f"Capability approval does not match event {event.id}")
            capability_approvals_by_id[approval_id] = approval
        elif event.event_type == CAPABILITY_REVOKED:
            approval_id = _uuid_metadata(event, "approval_id")
            revocation_id = _uuid_metadata(event, "revocation_id")
            path = _capability_revocation_path(layout, revocation_id)
            expected_capability_revocations.add(path)
            revocation = load_record(path, CapabilityRevocation)
            _validate_common(revocation, event, revocation_id)
            approval = capability_approvals_by_id.get(approval_id)
            record_digest = canonical_json_digest(revocation.model_dump(mode="json"))
            if (
                approval is None
                or approval_id in revoked_capability_approval_ids
                or revocation.id != revocation_id
                or revocation.approval_id != approval_id
                or revocation.owner_actor != event.actor
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or revocation.revocation_event_id != event.id
                or event.metadata.get("capability_id") != approval.capability_id
                or approval_id not in event.affected_record_ids
                or approval.capability_digest not in event.affected_digests
                or record_digest not in event.affected_digests
                or revocation.affected_record_ids != (approval_id,)
                or revocation.affected_digests != (approval.capability_digest,)
            ):
                raise IntegrityError(f"Capability revocation does not match event {event.id}")
            revoked_capability_approval_ids.add(approval_id)
        elif event.event_type in {ARTIFACT_REGISTERED, ARTIFACT_REVISED}:
            artifact_id = _uuid_metadata(event, "artifact_id")
            revision_id = _uuid_metadata(event, "revision_id")
            revision_number = event.metadata.get("revision_number")
            if not isinstance(revision_number, int) or isinstance(revision_number, bool):
                raise IntegrityError(f"Artifact event {event.id} has invalid revision number")
            record_path = _record_path(layout, artifact_id, revision_number)
            revision_path = _revision_path(layout, revision_id)
            expected_artifact_records.add(record_path)
            expected_revisions.add(revision_path)
            artifact = load_record(record_path, ArtifactRecord)
            revision = load_record(revision_path, ArtifactRevision)
            _validate_common(artifact, event, artifact_id)
            _validate_common(revision, event, revision_id)
            if (
                artifact.id != artifact_id
                or artifact.current_revision != revision_number
                or revision.id != revision_id
                or revision.artifact_id != artifact_id
                or revision.revision_number != revision_number
                or revision.registration_event_id != event.id
                or revision.preserved_object_path is None
                or revision.preservation_status != "preserved"
                or revision.content_digest not in event.affected_digests
            ):
                raise IntegrityError(f"Artifact records do not match event {event.id}")
            if event.event_type == ARTIFACT_REGISTERED:
                if revision_number != 1 or revision.superseded_revision_number is not None:
                    raise IntegrityError("First artifact revision has invalid predecessor data")
                raw_predecessor_revision_id = event.metadata.get(
                    "predecessor_revision_id"
                )
                if revision.provenance.source_type == "predecessor-artifact":
                    if not isinstance(raw_predecessor_revision_id, str):
                        raise IntegrityError(
                            "Predecessor artifact registration lacks its source revision"
                        )
                    try:
                        predecessor_revision_id = UUID(raw_predecessor_revision_id)
                    except ValueError as error:
                        raise IntegrityError(
                            "Predecessor artifact registration has an invalid source revision"
                        ) from error
                    predecessor_id, predecessor_revision = (
                        load_predecessor_artifact_revision(
                            layout,
                            initiative,
                            predecessor_revision_id,
                        )
                    )
                    expected_metadata = {
                        "predecessor_initiative_id": str(predecessor_id),
                        "predecessor_revision_id": str(predecessor_revision_id),
                        "predecessor_content_digest": predecessor_revision.content_digest,
                    }
                    if (
                        revision.provenance.source_reference
                        != predecessor_artifact_source_reference(
                            predecessor_id, predecessor_revision_id
                        )
                        or revision.provenance.metadata != expected_metadata
                        or revision.content_digest != predecessor_revision.content_digest
                        or revision.byte_size != predecessor_revision.byte_size
                        or predecessor_revision_id not in event.affected_record_ids
                    ):
                        raise IntegrityError(
                            "Predecessor artifact provenance does not match archived bytes"
                        )
                elif raw_predecessor_revision_id is not None:
                    raise IntegrityError(
                        "Ordinary artifact registration claims predecessor revision metadata"
                    )
            else:
                previous_id = _uuid_metadata(event, "superseded_revision_id")
                previous = revisions_by_id.get(previous_id)
                if (
                    previous is None
                    or previous.artifact_id != artifact_id
                    or revision.superseded_revision_number != previous.revision_number
                ):
                    raise IntegrityError("Artifact revision predecessor does not match history")
                effects = _uuid_list_metadata(event, "stale_record_ids")
                if (
                    revision.stale_dependency_effects != effects
                    or previous_id not in effects
                    or not set(effects).issubset(event.affected_record_ids)
                ):
                    raise IntegrityError("Artifact revision staleness does not match its event")
                stale_ids.update(effects)
            verify_preserved_object(
                layout,
                repository_path=revision.preserved_object_path,
                expected_digest=revision.content_digest,
                expected_size=revision.byte_size,
            )
            revisions_by_id[revision_id] = revision
            artifact_roles[artifact_id] = artifact.role
            current_revision_ids[artifact_id] = revision_id
        elif event.event_type == RESULT_IMPORTED:
            result_id = _uuid_metadata(event, "result_id")
            result_path = _imported_result_path(layout, result_id)
            expected_imported_results.add(result_path)
            result = load_record(result_path, AgentResult)
            result_digest = canonical_json_digest(result.model_dump(mode="json"))
            manifest_digest = event.metadata.get("manifest_digest")
            raw_updates = event.metadata.get("artifact_updates")
            import_step_id = event.metadata.get("step_id")
            source_kind = event.metadata.get("source_kind")
            import_step = next(
                (item for item in workflow.steps if item.id == import_step_id),
                None,
            )
            if not isinstance(raw_updates, list) or not raw_updates:
                raise IntegrityError(f"Import event {event.id} has no artifact updates")
            updates = cast("list[object]", raw_updates)
            if (
                result.id != result_id
                or str(result.source_run_or_handoff_id) != event.metadata.get("source_id")
                or event.metadata.get("result_digest") != result_digest
                or result_digest not in event.affected_digests
                or not isinstance(manifest_digest, str)
                or manifest_digest not in event.affected_digests
                or result_id not in event.affected_record_ids
                or result_id in seen_event_record_ids
                or len(updates) != len(result.returned_files)
                or import_step is None
                or event.actor.actor_type not in import_step.allowed_actors
                or source_kind not in {"run", "handoff"}
                or (source_kind == "run" and event.run_id != result.source_run_or_handoff_id)
                or (source_kind == "handoff" and event.run_id is not None)
            ):
                raise IntegrityError(f"Imported result does not match event {event.id}")
            if source_kind == "run":
                source_run = load_record(
                    layout.governed_run_directory
                    / f"{result.source_run_or_handoff_id}.json",
                    RunRecord,
                )
                if (
                    source_run.initiative_id != event.initiative_id
                    or source_run.step_id != import_step_id
                ):
                    raise IntegrityError(f"Imported result source run is invalid: {event.id}")
            returned_by_paths = {
                (item.source_path, item.proposed_target_path): item
                for item in result.returned_files
            }
            if len(returned_by_paths) != len(result.returned_files):
                raise IntegrityError(f"Imported result has duplicate file declarations: {event.id}")
            import_stale: set[UUID] = set()
            seen_artifacts: set[UUID] = set()
            for raw_update in updates:
                if not isinstance(raw_update, dict):
                    raise IntegrityError(f"Import event {event.id} has invalid artifact data")
                update = cast("dict[object, object]", raw_update)
                artifact_value = update.get("artifact_id")
                revision_value = update.get("revision_id")
                revision_number = update.get("revision_number")
                source_path = update.get("source_path")
                target_path = update.get("target_path")
                action = update.get("action")
                role = update.get("artifact_role")
                digest = update.get("content_digest")
                byte_size = update.get("byte_size")
                media_type = update.get("media_type")
                if (
                    not isinstance(artifact_value, str)
                    or not isinstance(revision_value, str)
                    or not isinstance(revision_number, int)
                    or isinstance(revision_number, bool)
                    or not isinstance(source_path, str)
                    or not isinstance(target_path, str)
                    or action not in {"create", "revise"}
                    or not isinstance(role, str)
                    or not isinstance(digest, str)
                    or not isinstance(byte_size, int)
                    or isinstance(byte_size, bool)
                    or not isinstance(media_type, str)
                ):
                    raise IntegrityError(f"Import event {event.id} has invalid artifact data")
                try:
                    artifact_id = UUID(artifact_value)
                    revision_id = UUID(revision_value)
                except ValueError as error:
                    raise IntegrityError(
                        f"Import event {event.id} has invalid artifact UUIDs"
                    ) from error
                if artifact_id in seen_artifacts:
                    raise IntegrityError(f"Import event {event.id} updates an artifact twice")
                seen_artifacts.add(artifact_id)
                declaration = returned_by_paths.get((source_path, target_path))
                record_path = _record_path(layout, artifact_id, revision_number)
                stored_revision_path = _revision_path(layout, revision_id)
                expected_artifact_records.add(record_path)
                expected_revisions.add(stored_revision_path)
                artifact = load_record(record_path, ArtifactRecord)
                revision = load_record(stored_revision_path, ArtifactRevision)
                _validate_common(artifact, event, artifact_id)
                _validate_common(revision, event, revision_id)
                if (
                    declaration is None
                    or artifact.id != artifact_id
                    or artifact.role != role
                    or artifact.current_revision != revision_number
                    or revision.id != revision_id
                    or revision.artifact_id != artifact_id
                    or revision.revision_number != revision_number
                    or revision.path != target_path
                    or revision.content_digest != digest
                    or revision.byte_size != byte_size
                    or revision.media_type != media_type
                    or revision.registration_event_id != event.id
                    or revision.preserved_object_path is None
                    or revision.preservation_status != "preserved"
                    or revision.provenance.source_type != "import-result"
                    or revision.provenance.source_reference
                    != f"result:{result_id}:{source_path}"
                    or revision.provenance.metadata.get("untrusted") is not True
                    or digest not in event.affected_digests
                    or (declaration.declared_digest is not None
                        and declaration.declared_digest != digest)
                ):
                    raise IntegrityError(
                        f"Imported artifact records do not match event {event.id}"
                    )
                if action == "create":
                    if (
                        revision_number != 1
                        or artifact_id in current_revision_ids
                        or revision.superseded_revision_number is not None
                        or revision.stale_dependency_effects
                    ):
                        raise IntegrityError("Imported artifact creation has invalid history")
                else:
                    prior_revision_id = current_revision_ids.get(artifact_id)
                    if prior_revision_id is None:
                        raise IntegrityError("Imported revision has no current predecessor")
                    prior = revisions_by_id[prior_revision_id]
                    superseded_value = update.get("superseded_revision_id")
                    if (
                        superseded_value != str(prior.id)
                        or revision_number != prior.revision_number + 1
                        or revision.superseded_revision_number != prior.revision_number
                        or prior.id not in revision.stale_dependency_effects
                    ):
                        raise IntegrityError("Imported revision predecessor does not match history")
                    import_stale.update(revision.stale_dependency_effects)
                verify_preserved_object(
                    layout,
                    repository_path=revision.preserved_object_path,
                    expected_digest=revision.content_digest,
                    expected_size=revision.byte_size,
                )
                revisions_by_id[revision_id] = revision
                artifact_roles[artifact_id] = artifact.role
                current_revision_ids[artifact_id] = revision_id
            effects = set(_uuid_list_metadata(event, "stale_record_ids"))
            if effects != import_stale or not effects.issubset(event.affected_record_ids):
                raise IntegrityError(f"Import event {event.id} has invalid stale effects")
            stale_ids.update(effects)
        elif event.event_type == VALIDATOR_RUN_STARTED:
            if event.run_id is None:
                raise IntegrityError(f"Validator run event {event.id} has no run ID")
            run_id = event.run_id
            approval_id = _uuid_metadata(event, "capability_approval_id")
            result_id = _uuid_metadata(event, "check_result_id")
            target_ids = _uuid_list_metadata(event, "target_artifact_revision_ids")
            path = layout.validator_run_directory / f"{run_id}.json"
            expected_validator_runs.add(path)
            run = load_record(path, RunRecord)
            _validate_common(run, event, run_id)
            approval = capability_approvals_by_id.get(approval_id)
            step_id = event.metadata.get("step_id")
            step = next((item for item in workflow.steps if item.id == step_id), None)
            check_id = event.metadata.get("check_id")
            check_version = event.metadata.get("check_version")
            invocation_digest = event.metadata.get("invocation_digest")
            current_outputs = {
                revision_id
                for artifact_id, revision_id in current_revision_ids.items()
                if step is not None and artifact_roles[artifact_id] in step.required_outputs
            }
            target_digests = tuple(
                revisions_by_id[item].content_digest
                for item in target_ids
                if item in revisions_by_id
            )
            if (
                approval is None
                or approval_id in revoked_capability_approval_ids
                or approval.capability_id != event.metadata.get("capability_id")
                or approval.side_effect_class is not run.side_effect_class
                or (
                    approval.approval_scope is CapabilityTrustState.APPROVED_ONCE
                    and approval.id in used_capability_approval_ids
                )
                or step is None
                or not isinstance(check_id, str)
                or check_id not in step.check_requirements
                or not isinstance(check_version, str)
                or not check_version
                or not isinstance(invocation_digest, str)
                or invocation_digest != run.input_context_digest
                or run.id != run_id
                or run.run_id != run_id
                or run.worker != event.actor
                or run.worker.actor_type is not ActorType.EXTERNAL_TOOL
                or run.step_id != step_id
                or run.adapter_reference != f"validator:{approval.capability_id}"
                or run.capability_ids != (approval.capability_id,)
                or run.capability_approval_ids != (approval_id,)
                or run.status is not RunState.RUNNING
                or run.started_at is None
                or run.exit_metadata
                != {
                    "check_id": check_id,
                    "check_result_id": str(result_id),
                    "check_version": check_version,
                    "kind": "validator-check",
                }
                or set(target_ids) != current_outputs
                or len(target_ids) != len(current_outputs)
                or len(target_digests) != len(target_ids)
                or run.affected_record_ids
                != (run_id, approval_id, result_id, *target_ids)
                or event.affected_record_ids != run.affected_record_ids
                or run.affected_digests
                != (invocation_digest, approval.capability_digest, *target_digests)
                or event.affected_digests != run.affected_digests
                or run_id in validator_runs_by_id
            ):
                raise IntegrityError(f"Validator run record does not match event {event.id}")
            used_capability_approval_ids.add(approval_id)
            validator_runs_by_id[run_id] = run
        elif event.event_type == ADAPTER_RUN_EXECUTED:
            if event.run_id is None or event.run_id not in runs_by_id:
                raise IntegrityError(
                    f"Adapter execution event {event.id} references an unknown run"
                )
            run = runs_by_id[event.run_id]
            execution_state = event.metadata.get("state")
            exit_code = event.metadata.get("exit_code")
            staged_result_id = event.metadata.get("staged_result_id")
            staged_id_valid = staged_result_id is None
            if isinstance(staged_result_id, str):
                try:
                    UUID(staged_result_id)
                    staged_id_valid = True
                except ValueError:
                    staged_id_valid = False
            if (
                run.adapter_reference is None
                or run.worker.actor_type is not ActorType.AGENT_ADAPTER
                or event.actor != run.worker
                or event.metadata.get("adapter_id") != run.adapter_reference
                or event.metadata.get("capability_id")
                != (run.capability_ids[0] if len(run.capability_ids) == 1 else None)
                or event.metadata.get("capability_approval_id")
                != (
                    str(run.capability_approval_ids[0])
                    if len(run.capability_approval_ids) == 1
                    else None
                )
                or event.metadata.get("step_id") != run.step_id
                or execution_state not in {"succeeded", "failed", "cancelled"}
                or isinstance(exit_code, bool)
                or not isinstance(exit_code, (int, type(None)))
                or (execution_state == "succeeded" and exit_code != 0)
                or (execution_state == "succeeded") != (staged_result_id is not None)
                or not staged_id_valid
                or event.run_id in adapter_execution_run_ids
                or event.affected_record_ids != (run.id, *run.capability_approval_ids)
                or event.affected_digests != (run.input_context_digest,)
            ):
                raise IntegrityError(f"Adapter execution event {event.id} violates run policy")
            adapter_execution_run_ids.add(event.run_id)
        elif event.event_type == RUN_CANCELLED:
            if event.run_id is None or event.run_id not in runs_by_id:
                raise IntegrityError(f"Cancellation event {event.id} references an unknown run")
            run = runs_by_id[event.run_id]
            step = next((item for item in workflow.steps if item.id == run.step_id), None)
            externally_risky = run.side_effect_class in {
                SideEffectClass.EXTERNAL_REVERSIBLE,
                SideEffectClass.EXTERNAL_IRREVERSIBLE,
                SideEffectClass.SENSITIVE,
            }
            expected_destination = (
                StepState.BLOCKED
                if externally_risky
                or step is None
                or step.cancellation_behavior is CancellationBehavior.BLOCK_FOR_OWNER_REVIEW
                else StepState.READY
            )
            if (
                (
                    event.actor != run.worker
                    and not (
                        event.actor.actor_type is ActorType.OWNER
                        and event.actor.id == owner_id
                    )
                )
                or event.metadata.get("step_id") != run.step_id
                or event.metadata.get("source_state") != StepState.IN_PROGRESS.value
                or event.metadata.get("destination_state") != expected_destination.value
                or not isinstance(event.metadata.get("reason"), str)
                or not event.metadata.get("reason")
            ):
                raise IntegrityError(f"Cancellation event {event.id} violates run policy")
        elif event.event_type == CLAIM_RECORDED:
            claim_id = _uuid_metadata(event, "claim_id")
            path = _claim_path(layout, claim_id)
            expected_claims.add(path)
            claim = load_record(path, Claim)
            _validate_common(claim, event, claim_id)
            revision_ids = _uuid_list_metadata(event, "artifact_revision_ids")
            if (
                claim.id != claim_id
                or claim.actor != event.actor
                or claim.step_id != event.metadata.get("step_id")
                or claim.claimed_artifact_revision_ids != revision_ids
                or not set(revision_ids).issubset(revisions_by_id)
            ):
                raise IntegrityError(f"Claim record does not match event {event.id}")
            claims_by_id[claim_id] = claim
            record_steps[claim_id] = claim.step_id
        elif event.event_type == CHECK_RECORDED:
            result_id = _uuid_metadata(event, "check_result_id")
            path = _check_path(layout, result_id)
            expected_checks.add(path)
            check = load_record(path, CheckResult)
            _validate_common(check, event, result_id)
            target_ids = _uuid_list_metadata(event, "target_artifact_revision_ids")
            capability_valid = True
            if check.capability_id is not None:
                run = (
                    validator_runs_by_id.get(event.run_id)
                    if event.run_id is not None
                    else None
                )
                approval = (
                    capability_approvals_by_id.get(check.capability_approval_id)
                    if check.capability_approval_id is not None
                    else None
                )
                expected_outcome = (
                    CheckOutcome.PASSED
                    if (
                        check.execution_status is CheckExecutionStatus.COMPLETED
                        and check.exit_status == 0
                    )
                    else (
                        CheckOutcome.FAILED
                        if check.execution_status is CheckExecutionStatus.COMPLETED
                        else CheckOutcome.ERROR
                    )
                )
                capture_prefix = f".forge/local/validator-runs/{event.run_id}"
                capability_valid = (
                    run is not None
                    and approval is not None
                    and check.capability_approval_id
                    not in revoked_capability_approval_ids
                    and check.run_id == run.id
                    and check.actor == run.worker
                    and check.capability_id == run.capability_ids[0]
                    and check.capability_approval_id == run.capability_approval_ids[0]
                    and check.invocation_digest == run.input_context_digest
                    and str(result_id) == run.exit_metadata.get("check_result_id")
                    and check.check_id == run.exit_metadata.get("check_id")
                    and check.check_version == run.exit_metadata.get("check_version")
                    and run.started_at is not None
                    and check.started_at >= run.started_at
                    and check.ended_at >= check.started_at
                    and check.outcome is expected_outcome
                    and check.stdout_capture_path == f"{capture_prefix}/stdout.log"
                    and check.stderr_capture_path == f"{capture_prefix}/stderr.log"
                    and check.stdout_byte_count is not None
                    and check.stderr_byte_count is not None
                    and check.stdout_byte_count + check.stderr_byte_count <= 1_048_576
                    and check.target_artifact_revision_ids
                    == tuple(run.affected_record_ids[3:])
                    and event.metadata.get("validator_run_id") == str(run.id)
                    and event.metadata.get("capability_id") == check.capability_id
                    and event.metadata.get("capability_approval_id")
                    == str(check.capability_approval_id)
                    and event.metadata.get("execution_status")
                    == (
                        check.execution_status.value
                        if check.execution_status is not None
                        else None
                    )
                    and check.affected_record_ids
                    == (run.id, approval.id, *target_ids)
                    and event.affected_record_ids
                    == (result_id, run.id, approval.id, *target_ids)
                    and event.affected_digests == check.affected_digests
                )
            if (
                check.id != result_id
                or check.actor != event.actor
                or check.check_id != event.metadata.get("check_id")
                or check.outcome.value != event.metadata.get("outcome")
                or check.target_artifact_revision_ids != target_ids
                or not set(target_ids).issubset(revisions_by_id)
                or _check_digest(check) != check.result_digest
                or check.result_digest not in event.affected_digests
                or not capability_valid
            ):
                raise IntegrityError(f"Check result does not match event {event.id}")
            checks_by_id[result_id] = check
            step_id = event.metadata.get("step_id")
            if not isinstance(step_id, str):
                raise IntegrityError(f"Check event {event.id} has no workflow step")
            record_steps[result_id] = step_id
        elif event.event_type == EVIDENCE_REGISTERED:
            evidence_id = _uuid_metadata(event, "evidence_id")
            path = _evidence_path(layout, evidence_id)
            expected_evidence.add(path)
            evidence = load_record(path, EvidencePacket)
            _validate_common(evidence, event, evidence_id)
            artifact_ids = _uuid_list_metadata(event, "artifact_revision_ids")
            check_ids = _uuid_list_metadata(event, "check_result_ids")
            claim_ids = _uuid_list_metadata(event, "claim_ids")
            if (
                evidence.id != evidence_id
                or evidence.actor != event.actor
                or evidence.artifact_revision_ids != artifact_ids
                or evidence.check_result_ids != check_ids
                or evidence.claim_ids != claim_ids
                or not set(artifact_ids).issubset(revisions_by_id)
                or not set(check_ids).issubset(checks_by_id)
                or not set(claim_ids).issubset(claims_by_id)
                or _evidence_digest(evidence) != evidence.packet_digest
                or evidence.packet_digest not in event.affected_digests
            ):
                raise IntegrityError(f"Evidence packet does not match event {event.id}")
            evidence_by_id[evidence_id] = evidence
            step_id = event.metadata.get("step_id")
            if not isinstance(step_id, str):
                raise IntegrityError(f"Evidence event {event.id} has no workflow step")
            record_steps[evidence_id] = step_id
        elif event.event_type == ACCEPTANCE_RECORDED:
            acceptance_id = _uuid_metadata(event, "acceptance_id")
            path = _acceptance_path(layout, acceptance_id)
            expected_acceptances.add(path)
            acceptance = load_record(path, AcceptanceRecord)
            _validate_common(acceptance, event, acceptance_id)
            artifact_ids = _uuid_list_metadata(event, "artifact_revision_ids")
            check_ids = _uuid_list_metadata(event, "check_result_ids")
            evidence_ids = _uuid_list_metadata(event, "evidence_ids")
            step_id = event.metadata.get("step_id")
            if (
                not isinstance(step_id, str)
                or acceptance.id != acceptance_id
                or acceptance.owner_actor != event.actor
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or acceptance.acceptance_event_id != event.id
                or acceptance.revocation_id is not None
                or acceptance.accepted_artifact_revision_ids != artifact_ids
                or acceptance.accepted_check_result_ids != check_ids
                or acceptance.accepted_evidence_ids != evidence_ids
                or not set(artifact_ids).issubset(revisions_by_id)
                or not set(check_ids).issubset(checks_by_id)
                or not set(evidence_ids).issubset(evidence_by_id)
                or set((acceptance_id, *artifact_ids, *check_ids, *evidence_ids))
                - set(event.affected_record_ids)
                or set(acceptance.affected_digests) - set(event.affected_digests)
                or canonical_json_digest(acceptance.model_dump(mode="json"))
                not in event.affected_digests
                or set((acceptance_id, *artifact_ids, *check_ids, *evidence_ids)) & stale_ids
            ):
                raise IntegrityError(f"Acceptance record does not match event {event.id}")
            acceptances_by_id[acceptance_id] = acceptance
            acceptance_steps[acceptance_id] = step_id
            record_steps[acceptance_id] = step_id
        elif event.event_type in {DECISION_RECORDED, DECISION_SUPERSEDED}:
            decision_id = _uuid_metadata(event, "decision_id")
            path = _decision_path(layout, decision_id)
            expected_decisions.add(path)
            decision = load_record(path, DecisionRecord)
            _validate_common(decision, event, decision_id)
            if (
                decision.id != decision_id
                or decision.actor != event.actor
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or not set(decision.bound_digests).issubset(event.affected_digests)
                or canonical_json_digest(decision.model_dump(mode="json"))
                not in event.affected_digests
            ):
                raise IntegrityError(f"Decision record does not match event {event.id}")
            if event.event_type == DECISION_SUPERSEDED:
                prior_id = _uuid_metadata(event, "prior_decision_id")
                supersession_id = _uuid_metadata(event, "supersession_id")
                supersession_path = _supersession_path(layout, supersession_id)
                expected_supersessions.add(supersession_path)
                supersession = load_record(supersession_path, DecisionSupersession)
                _validate_common(supersession, event, supersession_id)
                if (
                    prior_id not in decisions_by_id
                    or supersession.id != supersession_id
                    or supersession.prior_decision_id != prior_id
                    or supersession.replacement_decision_id != decision_id
                    or supersession.actor != event.actor
                    or canonical_json_digest(supersession.model_dump(mode="json"))
                    not in event.affected_digests
                ):
                    raise IntegrityError(
                        f"Decision supersession does not match event {event.id}"
                    )
                stale_ids.add(prior_id)
            decisions_by_id[decision_id] = decision
        elif event.event_type == SCOPE_AMENDED:
            amendment_id = _uuid_metadata(event, "scope_amendment_id")
            path = _scope_amendment_path(layout, amendment_id)
            expected_scope_amendments.add(path)
            amendment = load_record(path, ScopeAmendment)
            _validate_common(amendment, event, amendment_id)
            prior_state = states_before[event.id]
            if prior_state is None:
                raise IntegrityError("Scope amendment cannot be the first initiative event")
            return_step_id = event.metadata.get("workflow_return_step_id")
            if not isinstance(return_step_id, str):
                raise IntegrityError(f"Scope amendment event {event.id} has no return step")
            affected_steps = {return_step_id}
            changed = True
            while changed:
                changed = False
                for step in workflow.steps:
                    if step.id not in affected_steps and set(step.prerequisites) & affected_steps:
                        affected_steps.add(step.id)
                        changed = True
            if return_step_id not in {step.id for step in workflow.steps}:
                raise IntegrityError(f"Scope amendment event {event.id} has an unknown return step")
            affected_artifact_ids = _uuid_list_metadata(event, "affected_artifact_ids")
            expected_stale_ids = {
                record_id
                for record_id, step_id in record_steps.items()
                if step_id in affected_steps
            }
            decision_dependencies = {*expected_stale_ids, *affected_artifact_ids}
            expected_stale_ids.update(
                item.id
                for item in decisions_by_id.values()
                if set(item.affected_record_ids) & decision_dependencies
            )
            ordered_stale_ids = tuple(sorted(expected_stale_ids, key=str))
            invalidated_step_ids = tuple(
                step.id
                for step in workflow.steps
                if step.id in affected_steps
                and (
                    (
                        step.id == return_step_id
                        and prior_state.step_states[step.id] is not StepState.PENDING
                    )
                    or prior_state.step_states[step.id]
                    not in {StepState.PENDING, StepState.READY}
                )
            )
            reset_step_ids = tuple(
                step.id
                for step in workflow.steps
                if step.id in affected_steps
                and (
                    (
                        step.id == return_step_id
                        and prior_state.step_states[step.id] is StepState.PENDING
                    )
                    or (
                        step.id != return_step_id
                        and prior_state.step_states[step.id]
                        in {StepState.PENDING, StepState.READY}
                    )
                )
            )
            affected_active_runs = tuple(
                run_id
                for run_id in prior_state.active_run_ids
                if run_id in runs_by_id and runs_by_id[run_id].step_id in affected_steps
            )
            affected_requirements = amendment.affected_requirements
            affected_step_records = [
                step for step in workflow.steps if step.id in affected_steps
            ]
            check_requirements = {
                item
                for step in affected_step_records
                for item in step.check_requirements
            }
            artifact_classes = {
                item
                for step in affected_step_records
                for item in (*step.required_inputs, *step.required_outputs)
            }
            evidence_classes = set(workflow.required_evidence_classes)
            requirement_set = set(affected_requirements)
            known_requirements = {
                *workflow.required_artifact_classes,
                *workflow.required_evidence_classes,
            }
            for step in workflow.steps:
                known_requirements.update(step.required_inputs)
                known_requirements.update(step.required_outputs)
                known_requirements.update(step.claim_requirements)
                known_requirements.update(step.check_requirements)
                known_requirements.update(step.acceptance_requirements)
            for gate in workflow.required_gates:
                known_requirements.add(gate.id)
                known_requirements.add(gate.authority_requirement)
                known_requirements.update(gate.required_artifact_classes)
                known_requirements.update(gate.required_evidence_classes)
                known_requirements.update(gate.required_check_ids)
            for transition in workflow.transitions:
                known_requirements.add(transition.authority_requirement)
                known_requirements.update(transition.conditions)
            expected_gate_ids = tuple(
                gate.id
                for gate in workflow.required_gates
                if (
                    gate.id in requirement_set
                    or gate.authority_requirement in requirement_set
                    or set(gate.required_check_ids) & check_requirements
                    or set(gate.required_artifact_classes) & artifact_classes
                    or set(gate.required_evidence_classes) & evidence_classes
                )
            )
            expected_check_ids = tuple(
                sorted((set(checks_by_id) & expected_stale_ids), key=str)
            )
            expected_acceptance_ids = tuple(
                sorted((set(acceptances_by_id) & expected_stale_ids), key=str)
            )
            current_artifact_digests = tuple(
                revisions_by_id[current_revision_ids[item]].content_digest
                for item in affected_artifact_ids
                if item in current_revision_ids
            )
            governed_dependencies = tuple(
                dict.fromkeys((*affected_artifact_ids, *ordered_stale_ids))
            )
            record_digest = canonical_json_digest(amendment.model_dump(mode="json"))
            if (
                amendment.id != amendment_id
                or amendment.actor != event.actor
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or amendment.workflow_return_step_id != return_step_id
                or not amendment.affected_requirements
                or len(amendment.affected_requirements)
                != len(set(amendment.affected_requirements))
                or requirement_set - known_requirements
                or len(affected_artifact_ids) != len(set(affected_artifact_ids))
                or set(affected_artifact_ids) - set(current_revision_ids)
                or amendment.affected_artifact_ids != affected_artifact_ids
                or amendment.invalidated_check_ids != expected_check_ids
                or amendment.invalidated_acceptance_ids != expected_acceptance_ids
                or amendment.invalidated_gate_ids != expected_gate_ids
                or amendment.affected_record_ids != governed_dependencies
                or amendment.affected_digests != current_artifact_digests
                or not _string_list_matches(
                    event.metadata.get("affected_requirement_ids"),
                    affected_requirements,
                )
                or _uuid_list_metadata(event, "invalidated_check_ids")
                != expected_check_ids
                or _uuid_list_metadata(event, "invalidated_acceptance_ids")
                != expected_acceptance_ids
                or not _string_list_matches(
                    event.metadata.get("invalidated_gate_ids"),
                    expected_gate_ids,
                )
                or _uuid_list_metadata(event, "stale_record_ids")
                != ordered_stale_ids
                or not _string_list_matches(
                    event.metadata.get("invalidated_step_ids"),
                    invalidated_step_ids,
                )
                or not _string_list_matches(
                    event.metadata.get("reset_step_ids"),
                    reset_step_ids,
                )
                or _uuid_list_metadata(event, "invalidated_run_ids")
                or affected_active_runs
                or event.affected_record_ids
                != (amendment_id, *governed_dependencies)
                or event.affected_digests
                != (*current_artifact_digests, record_digest)
            ):
                raise IntegrityError(f"Scope amendment does not match event {event.id}")
            stale_ids.update(ordered_stale_ids)
        elif event.event_type == ACCEPTANCE_REVOKED:
            acceptance_id = _uuid_metadata(event, "acceptance_id")
            revocation_id = _uuid_metadata(event, "revocation_id")
            path = _revocation_path(layout, revocation_id)
            expected_revocations.add(path)
            revocation = load_record(path, ApprovalRevocation)
            _validate_common(revocation, event, revocation_id)
            effects = _uuid_list_metadata(event, "stale_record_ids")
            if (
                acceptance_id not in acceptances_by_id
                or acceptance_id in revoked_acceptance_ids
                or revocation.id != revocation_id
                or revocation.approval_id != acceptance_id
                or revocation.actor != event.actor
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or event.metadata.get("step_id") != acceptance_steps.get(acceptance_id)
                or acceptance_id not in effects
                or not set(effects).issubset(event.affected_record_ids)
                or canonical_json_digest(revocation.model_dump(mode="json"))
                not in event.affected_digests
            ):
                raise IntegrityError(f"Acceptance revocation does not match event {event.id}")
            revoked_acceptance_ids.add(acceptance_id)
            stale_ids.update(effects)
        elif event.event_type == COMMAND_RECOVERED:
            recovery_id = _uuid_metadata(event, "command_recovery_record_id")
            recovery_path = _command_recovery_path(layout, recovery_id)
            expected_command_recoveries.add(recovery_path)
            recovery = load_record(recovery_path, CommandRecoveryRecord)
            _validate_common(recovery, event, recovery_id)
            record_digest = canonical_json_digest(recovery.model_dump(mode="json"))
            receipt = IdempotencyReceipt(
                key=recovery.interrupted_key,
                command=recovery.interrupted_command,
                request_digest=recovery.interrupted_request_digest,
                completed_at=recovery.receipt_completed_at,
                events=recovery.recovered_events,
            )
            receipt_digest = canonical_json_digest(receipt.model_dump(mode="json"))
            recovered_ids = tuple(item.event_id for item in recovery.recovered_events)
            actual_events = tuple(item for item in events if item.id in set(recovered_ids))
            actual_references = tuple(
                IdempotencyEventReference(
                    event_id=item.id,
                    initiative_id=item.initiative_id,
                    sequence=item.sequence,
                    event_hash=item.event_hash,
                )
                for item in actual_events
                if item.event_hash is not None
            )
            expected_identity = {
                "key": recovery.interrupted_key,
                "command": recovery.interrupted_command,
                "request_digest": recovery.interrupted_request_digest,
            }
            expected_sequences = tuple(
                range(event.sequence - len(recovery.recovered_events), event.sequence)
            )
            if (
                recovery.id != recovery_id
                or recovery.recovery_event_id != event.id
                or recovery.actor != event.actor
                or recovery.actor_id != owner_id
                or recovery.recorded_at != event.timestamp
                or recovery.authorization_basis != event.authorization_basis
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or recovery.recovered_receipt_digest != receipt_digest
                or recovery.affected_digests != (receipt_digest,)
                or event.affected_record_ids != (recovery_id,)
                or event.affected_digests != (record_digest, receipt_digest)
                or actual_references != recovery.recovered_events
                or tuple(item.sequence for item in recovery.recovered_events)
                != expected_sequences
                or any(
                    item.metadata.get("idempotency") != expected_identity
                    for item in actual_events
                )
                or event.metadata.get("reason") != recovery.reason
                or event.metadata.get("interrupted_key") != recovery.interrupted_key
                or event.metadata.get("interrupted_command")
                != recovery.interrupted_command
                or event.metadata.get("interrupted_request_digest")
                != recovery.interrupted_request_digest
                or event.metadata.get("receipt_completed_at")
                != recovery.model_dump(mode="json")["receipt_completed_at"]
                or not _string_list_matches(
                    event.metadata.get("recovered_event_ids"),
                    tuple(str(item) for item in recovered_ids),
                )
                or event.metadata.get("recovered_receipt_digest") != receipt_digest
            ):
                raise IntegrityError(f"Command recovery record does not match event {event.id}")

        elif event.event_type == INTEGRITY_RECOVERED:
            recovery_id = _uuid_metadata(event, "recovery_record_id")
            recovery_path = _recovery_path(layout, recovery_id)
            expected_recoveries.add(recovery_path)
            recovery = load_record(recovery_path, RecoveryRecord)
            _validate_common(recovery, event, recovery_id)
            record_digest = canonical_json_digest(recovery.model_dump(mode="json"))
            if (
                recovery.id != recovery_id
                or recovery.recovery_event_id != event.id
                or recovery.actor != event.actor
                or recovery.actor_id != owner_id
                or recovery.source_journal_head_sequence != event.sequence - 1
                or recovery.source_journal_head_hash != event.previous_event_hash
                or event.metadata.get("reason") != recovery.reason
                or event.metadata.get("snapshot_condition")
                != recovery.snapshot_condition.value
                or event.metadata.get("source_journal_head_sequence")
                != recovery.source_journal_head_sequence
                or event.metadata.get("source_journal_head_hash")
                != recovery.source_journal_head_hash
                or record_digest not in event.affected_digests
            ):
                raise IntegrityError(f"Recovery record does not match event {event.id}")
            preserved_fields = (
                event.metadata.get("preserved_snapshot_path"),
                event.metadata.get("preserved_snapshot_digest"),
                event.metadata.get("preserved_snapshot_size"),
            )
            record_fields = (
                recovery.preserved_snapshot_path,
                recovery.preserved_snapshot_digest,
                recovery.preserved_snapshot_size,
            )
            if preserved_fields != record_fields:
                raise IntegrityError(f"Recovery preservation metadata disagrees: {event.id}")
            if recovery.snapshot_condition is SnapshotCondition.MISSING:
                if any(value is not None for value in record_fields):
                    raise IntegrityError(
                        f"Missing snapshot recovery has preserved data: {event.id}"
                    )
            else:
                preserved_path = (
                    layout.root / str(recovery.preserved_snapshot_path)
                )
                expected_path = layout.recovery_snapshot_directory / f"{recovery_id}.bin"
                if preserved_path != expected_path:
                    raise IntegrityError(f"Recovery snapshot path is not canonical: {event.id}")
                expected_recovery_snapshots.add(expected_path)
                if expected_path.is_symlink() or not expected_path.is_file():
                    raise IntegrityError(f"Recovery snapshot is missing or unsafe: {event.id}")
                try:
                    if expected_path.stat().st_size > MAX_SNAPSHOT_BYTES:
                        raise IntegrityError(
                            f"Preserved recovery snapshot exceeds {MAX_SNAPSHOT_BYTES} bytes"
                        )
                    preserved = expected_path.read_bytes()
                except OSError as error:
                    raise IntegrityError(
                        f"Cannot read preserved recovery snapshot: {error}"
                    ) from error
                if (
                    len(preserved) != recovery.preserved_snapshot_size
                    or sha256_digest(preserved) != recovery.preserved_snapshot_digest
                    or recovery.preserved_snapshot_digest not in event.affected_digests
                ):
                    raise IntegrityError(f"Preserved recovery snapshot is invalid: {event.id}")

        elif event.event_type == JOURNAL_RECOVERED:
            recovery_id = _uuid_metadata(event, "journal_recovery_record_id")
            recovery_path = _recovery_path(layout, recovery_id)
            source_path = _recovery_journal_path(layout, recovery_id)
            expected_recoveries.add(recovery_path)
            expected_recovery_journals.add(source_path)
            recovery = load_record(recovery_path, JournalRecoveryRecord)
            _validate_common(recovery, event, recovery_id)
            record_digest = canonical_json_digest(recovery.model_dump(mode="json"))
            snapshot_fields = (
                recovery.preserved_snapshot_path,
                recovery.preserved_snapshot_digest,
                recovery.preserved_snapshot_size,
            )
            event_snapshot_fields = (
                event.metadata.get("preserved_snapshot_path"),
                event.metadata.get("preserved_snapshot_digest"),
                event.metadata.get("preserved_snapshot_size"),
            )
            required_digests = {
                record_digest,
                recovery.preserved_journal_digest,
                recovery.truncated_tail_digest,
            }
            if recovery.preserved_snapshot_digest is not None:
                required_digests.add(recovery.preserved_snapshot_digest)
            if (
                recovery.id != recovery_id
                or recovery.recovery_event_id != event.id
                or recovery.actor != event.actor
                or recovery.actor_id != owner_id
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or recovery.damage_condition
                is not JournalDamageCondition.TRUNCATED_FINAL_RECORD
                or recovery.valid_event_count != event.sequence - 1
                or recovery.source_journal_head_sequence != event.sequence - 1
                or recovery.source_journal_head_hash != event.previous_event_hash
                or event.metadata.get("reason") != recovery.reason
                or event.metadata.get("damage_condition")
                != recovery.damage_condition.value
                or event.metadata.get("valid_event_count")
                != recovery.valid_event_count
                or event.metadata.get("source_journal_head_sequence")
                != recovery.source_journal_head_sequence
                or event.metadata.get("source_journal_head_hash")
                != recovery.source_journal_head_hash
                or event.metadata.get("preserved_journal_path")
                != recovery.preserved_journal_path
                or event.metadata.get("preserved_journal_digest")
                != recovery.preserved_journal_digest
                or event.metadata.get("preserved_journal_size")
                != recovery.preserved_journal_size
                or event.metadata.get("valid_prefix_size")
                != recovery.valid_prefix_size
                or event.metadata.get("truncated_tail_digest")
                != recovery.truncated_tail_digest
                or event.metadata.get("truncated_tail_size")
                != recovery.truncated_tail_size
                or event.metadata.get("snapshot_condition")
                != recovery.snapshot_condition.value
                or event_snapshot_fields != snapshot_fields
                or not required_digests.issubset(event.affected_digests)
                or set(recovery.affected_digests)
                != required_digests - {record_digest}
            ):
                raise IntegrityError(f"Journal recovery record does not match event {event.id}")
            expected_source_reference = (
                f".forge/active/recovery-journals/{recovery_id}.events.jsonl"
            )
            if recovery.preserved_journal_path != expected_source_reference:
                raise IntegrityError(f"Recovery journal path is not canonical: {event.id}")
            if source_path.is_symlink() or not source_path.is_file():
                raise IntegrityError(f"Preserved recovery journal is missing or unsafe: {event.id}")
            try:
                source_bytes = source_path.read_bytes()
            except OSError as error:
                raise IntegrityError(f"Cannot read preserved recovery journal: {error}") from error
            if (
                not source_bytes
                or len(source_bytes) > MAX_JOURNAL_RECOVERY_BYTES
                or len(source_bytes) != recovery.preserved_journal_size
                or sha256_digest(source_bytes) != recovery.preserved_journal_digest
            ):
                raise IntegrityError(f"Preserved recovery journal is invalid: {event.id}")
            source_candidate = inspect_journal_recovery_candidate(source_path)
            prefix_events = events[: recovery.valid_event_count]
            if (
                source_candidate is None
                or source_candidate.events != prefix_events
                or len(source_candidate.valid_prefix_bytes) != recovery.valid_prefix_size
                or len(source_candidate.truncated_tail) != recovery.truncated_tail_size
                or sha256_digest(source_candidate.truncated_tail)
                != recovery.truncated_tail_digest
            ):
                raise IntegrityError(
                    f"Preserved journal does not reproduce recovery evidence: {event.id}"
                )

            if recovery.snapshot_condition is JournalRecoverySnapshotCondition.MISSING:
                if any(value is not None for value in snapshot_fields):
                    raise IntegrityError(
                        f"Missing journal-recovery snapshot has preserved data: {event.id}"
                    )
            else:
                expected_snapshot_path = (
                    layout.recovery_snapshot_directory / f"{recovery_id}.bin"
                )
                preserved_snapshot_path = layout.root / str(
                    recovery.preserved_snapshot_path
                )
                if preserved_snapshot_path != expected_snapshot_path:
                    raise IntegrityError(
                        f"Journal-recovery snapshot path is not canonical: {event.id}"
                    )
                expected_recovery_snapshots.add(expected_snapshot_path)
                if expected_snapshot_path.is_symlink() or not expected_snapshot_path.is_file():
                    raise IntegrityError(
                        f"Journal-recovery snapshot is missing or unsafe: {event.id}"
                    )
                try:
                    preserved_snapshot = expected_snapshot_path.read_bytes()
                except OSError as error:
                    raise IntegrityError(
                        f"Cannot read journal-recovery snapshot: {error}"
                    ) from error
                if (
                    len(preserved_snapshot) != recovery.preserved_snapshot_size
                    or sha256_digest(preserved_snapshot)
                    != recovery.preserved_snapshot_digest
                ):
                    raise IntegrityError(
                        f"Preserved journal-recovery snapshot is invalid: {event.id}"
                    )
                try:
                    observed_snapshot = MaterializedState.model_validate_json(
                        preserved_snapshot
                    )
                except ValueError:
                    observed_condition = JournalRecoverySnapshotCondition.INVALID
                else:
                    prefix_state = replay_events(
                        prefix_events,
                        WorkflowStateReducer(workflow, owner_id),
                    )
                    observed_condition = (
                        JournalRecoverySnapshotCondition.HEALTHY
                        if observed_snapshot == prefix_state
                        else JournalRecoverySnapshotCondition.MISMATCHED
                    )
                if recovery.snapshot_condition is not observed_condition:
                    raise IntegrityError(
                        f"Journal-recovery snapshot condition is invalid: {event.id}"
                    )

        elif event.event_type == SCHEMA_MIGRATED:
            migration_id = _uuid_metadata(event, "migration_record_id")
            record_path = _migration_path(layout, migration_id)
            source_path = _migration_source_path(layout, migration_id)
            expected_migrations.add(record_path)
            expected_migration_sources.add(source_path)
            migration = load_record(record_path, MigrationRecord)
            _validate_common(migration, event, migration_id)
            record_digest = canonical_json_digest(migration.model_dump(mode="json"))
            if (
                migration.id != migration_id
                or migration.migration_event_id != event.id
                or migration.migration_id != LEGACY_JOURNAL_MIGRATION_ID
                or migration.migration_actor != event.actor
                or migration.migration_actor != migration_actor()
                or event.actor.actor_type is not ActorType.MIGRATION
                or migration.owner_actor.actor_type is not ActorType.OWNER
                or migration.owner_actor.id != owner_id
                or migration.source_event_count != event.sequence - 1
                or migration.source_schema_version
                != LEGACY_JOURNAL_MIGRATION.source_schema_version
                or migration.target_schema_version
                != LEGACY_JOURNAL_MIGRATION.target_schema_version
                or migration.source_format != LEGACY_JOURNAL_MIGRATION.source_format
                or migration.target_format != LEGACY_JOURNAL_MIGRATION.target_format
                or migration.affected_digests != (migration.preserved_source_digest,)
                or event.metadata.get("migration_id") != migration.migration_id
                or event.metadata.get("owner_actor_id") != str(owner_id)
                or event.metadata.get("source_schema_version")
                != migration.source_schema_version
                or event.metadata.get("target_schema_version")
                != migration.target_schema_version
                or event.metadata.get("source_format") != migration.source_format
                or event.metadata.get("target_format") != migration.target_format
                or event.metadata.get("source_event_count")
                != migration.source_event_count
                or event.metadata.get("preserved_source_path")
                != migration.preserved_source_path
                or event.metadata.get("preserved_source_digest")
                != migration.preserved_source_digest
                or event.metadata.get("preserved_source_size")
                != migration.preserved_source_size
                or record_digest not in event.affected_digests
                or migration.preserved_source_digest not in event.affected_digests
            ):
                raise IntegrityError(f"Migration record does not match event {event.id}")
            expected_source_reference = (
                f".forge/active/migration-sources/{migration_id}.events.jsonl"
            )
            if migration.preserved_source_path != expected_source_reference:
                raise IntegrityError(f"Migration source path is not canonical: {event.id}")
            if source_path.is_symlink() or not source_path.is_file():
                raise IntegrityError(f"Migration source is missing or unsafe: {event.id}")
            try:
                source_bytes = source_path.read_bytes()
            except OSError as error:
                raise IntegrityError(f"Cannot read preserved migration source: {error}") from error
            if (
                not source_bytes
                or len(source_bytes) > MAX_MIGRATION_SOURCE_BYTES
                or len(source_bytes) != migration.preserved_source_size
                or sha256_digest(source_bytes) != migration.preserved_source_digest
            ):
                raise IntegrityError(f"Preserved migration source is invalid: {event.id}")
            source_events = read_journal(source_path)
            migrated_prefix = events[: migration.source_event_count]
            unsealed_prefix = tuple(
                item.model_copy(
                    update={"previous_event_hash": None, "event_hash": None}
                )
                for item in migrated_prefix
            )
            if (
                len(source_events) != migration.source_event_count
                or any(item.event_hash is not None for item in source_events)
                or source_events != unsealed_prefix
                or not migrated_prefix
                or event.previous_event_hash != migrated_prefix[-1].event_hash
            ):
                raise IntegrityError(f"Migrated journal differs from preserved source: {event.id}")

        elif event.event_type == INITIATIVE_CLOSED:
            closure_id = _uuid_metadata(event, "closure_record_id")
            final_acceptance_ids = _uuid_list_metadata(event, "final_acceptance_ids")
            current_artifact_ids = _uuid_list_metadata(
                event, "current_artifact_revision_ids"
            )
            accepted_artifact_ids = _uuid_list_metadata(
                event, "accepted_artifact_revision_ids"
            )
            path = _closure_path(layout, closure_id)
            expected_closures.add(path)
            closure = load_record(path, ClosureRecord)
            _validate_common(closure, event, closure_id)
            archive_reference = event.metadata.get("archive_reference")
            selected_acceptances = [
                acceptances_by_id[item]
                for item in final_acceptance_ids
                if item in acceptances_by_id
            ]
            expected_steps = {step.id for step in workflow.steps}
            selected_steps = {
                acceptance_steps[item.id] for item in selected_acceptances
            }
            selected_step_order = tuple(
                acceptance_steps[item.id] for item in selected_acceptances
            )
            expected_current_ids = tuple(
                sorted(current_revision_ids.values(), key=str)
            )
            expected_accepted_ids = tuple(
                sorted(
                    {
                        revision_id
                        for acceptance in selected_acceptances
                        for revision_id in acceptance.accepted_artifact_revision_ids
                    },
                    key=str,
                )
            )
            expected_archive = f".forge/archive/{event.initiative_id}"
            current_digests = {
                revisions_by_id[item].content_digest for item in expected_current_ids
            }
            if (
                event is not events[-1]
                or closure.id != closure_id
                or closure.owner_actor != event.actor
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or closure.terminal_state is not InitiativeLifecycleState.CLOSED
                or closure.closure_event_id != event.id
                or closure.final_acceptance_ids != final_acceptance_ids
                or closure.current_artifact_revision_ids != current_artifact_ids
                or closure.accepted_artifact_revision_ids != accepted_artifact_ids
                or closure.archive_reference != archive_reference
                or archive_reference != expected_archive
                or len(selected_acceptances) != len(final_acceptance_ids)
                or selected_steps != expected_steps
                or selected_step_order != tuple(step.id for step in workflow.steps)
                or len(final_acceptance_ids) != len(expected_steps)
                or set(final_acceptance_ids) & (stale_ids | revoked_acceptance_ids)
                or current_artifact_ids != expected_current_ids
                or accepted_artifact_ids != expected_accepted_ids
                or not set(accepted_artifact_ids).issubset(current_artifact_ids)
                or set((closure_id, *final_acceptance_ids, *current_artifact_ids))
                - set(event.affected_record_ids)
                or current_digests - set(event.affected_digests)
                or set(closure.affected_digests) != current_digests
                or set(closure.affected_record_ids)
                != set((*final_acceptance_ids, *current_artifact_ids, *accepted_artifact_ids))
                or canonical_json_digest(closure.model_dump(mode="json"))
                not in event.affected_digests
                or state.lifecycle_state is not InitiativeLifecycleState.CLOSED
            ):
                raise IntegrityError(f"Closure record does not match event {event.id}")
        elif event.event_type == INITIATIVE_ABANDONED:
            abandonment_id = _uuid_metadata(event, "abandonment_record_id")
            current_artifact_ids = _uuid_list_metadata(
                event, "current_artifact_revision_ids"
            )
            path = _abandonment_path(layout, abandonment_id)
            expected_abandonments.add(path)
            abandonment = load_record(path, AbandonmentRecord)
            _validate_common(abandonment, event, abandonment_id)
            archive_reference = event.metadata.get("archive_reference")
            unresolved_risks = event.metadata.get("unresolved_risks")
            unfinished_steps = event.metadata.get("unfinished_step_ids")
            risks_match = _string_list_matches(
                unresolved_risks, abandonment.unresolved_risks
            )
            steps_match = _string_list_matches(
                unfinished_steps, abandonment.unfinished_step_ids
            )
            expected_current_ids = tuple(sorted(current_revision_ids.values(), key=str))
            expected_unfinished = tuple(
                step.id
                for step in workflow.steps
                if state.step_states[step.id] is not StepState.COMPLETED
            )
            expected_archive = f".forge/archive/{event.initiative_id}"
            current_digests = {
                revisions_by_id[item].content_digest for item in expected_current_ids
            }
            if (
                event is not events[-1]
                or abandonment.id != abandonment_id
                or abandonment.owner_actor != event.actor
                or event.actor.actor_type is not ActorType.OWNER
                or event.actor.id != owner_id
                or abandonment.terminal_state is not InitiativeLifecycleState.ABANDONED
                or abandonment.abandonment_event_id != event.id
                or abandonment.reason != event.metadata.get("reason")
                or abandonment.unfinished_work_summary
                != event.metadata.get("unfinished_work_summary")
                or not risks_match
                or not steps_match
                or abandonment.unfinished_step_ids != expected_unfinished
                or abandonment.current_artifact_revision_ids != current_artifact_ids
                or current_artifact_ids != expected_current_ids
                or abandonment.archive_reference != archive_reference
                or archive_reference != expected_archive
                or set((abandonment_id, *current_artifact_ids))
                - set(event.affected_record_ids)
                or current_digests - set(event.affected_digests)
                or set(abandonment.affected_digests) != current_digests
                or set(abandonment.affected_record_ids) != set(current_artifact_ids)
                or canonical_json_digest(abandonment.model_dump(mode="json"))
                not in event.affected_digests
                or state.lifecycle_state is not InitiativeLifecycleState.ABANDONED
            ):
                raise IntegrityError(f"Abandonment record does not match event {event.id}")
        elif event.event_type == STEP_TRANSITIONED:
            destination = event.metadata.get("destination_state")
            step_id = event.metadata.get("step_id")
            step = next((item for item in workflow.steps if item.id == step_id), None)
            if step is None:
                raise IntegrityError(f"Transition event {event.id} references an unknown step")
            if destination == StepState.IN_PROGRESS.value:
                if event.run_id is None:
                    raise IntegrityError("Begin transition has no run ID")
                run_path = layout.governed_run_directory / f"{event.run_id}.json"
                expected_runs.add(run_path)
                run = load_record(run_path, RunRecord)
                _validate_common(run, event, run.id)
                bound_approvals = tuple(
                    capability_approvals_by_id.get(item)
                    for item in run.capability_approval_ids
                )
                if (
                    run.id != event.run_id
                    or run.worker != event.actor
                    or run.step_id != step.id
                    or run.status is not RunState.RUNNING
                    or run.started_at is None
                    or len(run.capability_ids) != len(run.capability_approval_ids)
                    or any(item is None for item in bound_approvals)
                    or set(run.capability_approval_ids) & revoked_capability_approval_ids
                    or any(
                        approval is not None
                        and approval.capability_id != capability_id
                        for capability_id, approval in zip(
                            run.capability_ids, bound_approvals, strict=True
                        )
                    )
                    or any(
                        approval is not None
                        and approval.side_effect_class is not run.side_effect_class
                        for approval in bound_approvals
                    )
                    or any(
                        approval is not None
                        and approval.approval_scope is CapabilityTrustState.APPROVED_ONCE
                        and approval.id in used_capability_approval_ids
                        for approval in bound_approvals
                    )
                    or not set(run.capability_approval_ids).issubset(
                        event.affected_record_ids
                    )
                    or (run.adapter_reference is None and bool(run.capability_ids))
                ):
                    raise IntegrityError(f"Run record does not match begin event {event.id}")
                used_capability_approval_ids.update(run.capability_approval_ids)
                runs_by_id[run.id] = run
            current_outputs = {
                revision_id
                for artifact_id, revision_id in current_revision_ids.items()
                if artifact_roles[artifact_id] in step.required_outputs
            }
            if destination == StepState.AWAITING_VERIFICATION.value:
                support = _condition_record_ids(event, "claim-recorded")
                supported_claims = [claims_by_id[item] for item in support if item in claims_by_id]
                if not any(
                    claim.step_id == step.id
                    and set(claim.claimed_artifact_revision_ids) == current_outputs
                    for claim in supported_claims
                ):
                    raise IntegrityError("Submit transition is not backed by a current claim")
            elif destination == StepState.AWAITING_ACCEPTANCE.value:
                check_support = _condition_record_ids(event, "required-checks-passed")
                evidence_support = _condition_record_ids(event, "required-evidence-registered")
                supported_checks = [
                    checks_by_id[item] for item in check_support if item in checks_by_id
                ]
                passing_ids: set[UUID] = set()
                for required_check in step.check_requirements:
                    matching = [
                        check
                        for check in supported_checks
                        if check.check_id == required_check
                        and check.outcome is CheckOutcome.PASSED
                        and set(check.target_artifact_revision_ids) == current_outputs
                    ]
                    if not matching:
                        raise IntegrityError(
                            f"Verification transition lacks current passing check {required_check}"
                        )
                    passing_ids.add(matching[-1].id)
                supported_packets = [
                    evidence_by_id[item] for item in evidence_support if item in evidence_by_id
                ]
                if not any(
                    current_outputs.issubset(packet.artifact_revision_ids)
                    and passing_ids.issubset(packet.check_result_ids)
                    and any(claim_id in claims_by_id for claim_id in packet.claim_ids)
                    for packet in supported_packets
                ):
                    raise IntegrityError("Verification transition lacks current evidence support")
            elif destination == StepState.COMPLETED.value:
                support = _condition_record_ids(event, "owner-acceptance-recorded")
                matching = [
                    acceptances_by_id[item]
                    for item in support
                    if item in acceptances_by_id and item not in stale_ids
                ]
                if not any(
                    acceptance_steps[item.id] == step.id
                    and set(item.accepted_artifact_revision_ids) == current_outputs
                    for item in matching
                ):
                    raise IntegrityError(
                        "Acceptance transition lacks current owner acceptance support"
                    )

        seen_event_record_ids.update(event.affected_record_ids)

    _validate_directory(layout.artifact_record_directory, expected_artifact_records)
    _validate_directory(layout.artifact_revision_directory, expected_revisions)
    if expected_artifact_records or layout.artifact_directory.exists():
        if layout.artifact_directory.is_symlink() or not layout.artifact_directory.is_dir():
            raise IntegrityError("Artifact record root is missing or unsafe")
        expected_children = {
            layout.artifact_record_directory,
            layout.artifact_revision_directory,
        }
        if set(layout.artifact_directory.iterdir()) != expected_children:
            raise IntegrityError("Artifact record root contains unexpected entries")
    _validate_directory(layout.claim_directory, expected_claims)
    _validate_directory(layout.check_directory, expected_checks)
    _validate_directory(layout.evidence_directory, expected_evidence)
    _validate_directory(layout.acceptance_directory, expected_acceptances)
    _validate_directory(layout.revocation_directory, expected_revocations)
    _validate_directory(
        layout.capability_approval_directory,
        expected_capability_approvals,
    )
    _validate_directory(
        layout.capability_revocation_directory,
        expected_capability_revocations,
    )
    _validate_directory(
        layout.pack_trust_decision_directory,
        expected_pack_trust_decisions,
    )
    _validate_directory(layout.decision_directory, expected_decisions)
    _validate_directory(layout.decision_supersession_directory, expected_supersessions)
    _validate_directory(layout.scope_amendment_directory, expected_scope_amendments)
    _validate_directory(layout.imported_result_directory, expected_imported_results)
    _validate_directory(layout.closure_directory, expected_closures)
    _validate_directory(layout.abandonment_directory, expected_abandonments)
    _validate_directory(layout.governed_run_directory, expected_runs)
    _validate_directory(layout.validator_run_directory, expected_validator_runs)
    _validate_directory(
        layout.command_recovery_record_directory,
        expected_command_recoveries,
    )
    _validate_directory(layout.recovery_record_directory, expected_recoveries)
    _validate_directory(layout.recovery_snapshot_directory, expected_recovery_snapshots)
    _validate_directory(layout.recovery_journal_directory, expected_recovery_journals)
    _validate_directory(layout.migration_record_directory, expected_migrations)
    _validate_directory(layout.migration_source_directory, expected_migration_sources)
    expected_state = {
        artifact_id: revisions_by_id[revision_id].revision_number
        for artifact_id, revision_id in current_revision_ids.items()
    }
    if state.current_artifact_revisions != expected_state:
        raise IntegrityError("Materialized artifact revisions do not match governed records")
    if set(state.stale_record_ids) != stale_ids:
        raise IntegrityError("Materialized stale records do not match governed invalidations")


# Compatibility alias retained for callers from earlier M1 increments.
validate_increment4_records = validate_governed_records
