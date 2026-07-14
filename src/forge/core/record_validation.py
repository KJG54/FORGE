"""Cross-check governed records against journal events and preserved bytes."""

from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID

from forge.contracts.actors import ActorType
from forge.contracts.agents import AgentResult
from forge.contracts.archives import ClosureRecord
from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.contracts.capabilities import SideEffectClass
from forge.contracts.decisions import ApprovalRevocation, DecisionRecord, DecisionSupersession
from forge.contracts.events import AuditEvent
from forge.contracts.runs import RunRecord
from forge.contracts.state import InitiativeLifecycleState, MaterializedState, RunState, StepState
from forge.contracts.verification import (
    AcceptanceRecord,
    CheckOutcome,
    CheckResult,
    Claim,
    EvidencePacket,
)
from forge.contracts.workflows import CancellationBehavior, WorkflowDefinition
from forge.core.transitions import (
    ACCEPTANCE_RECORDED,
    ACCEPTANCE_REVOKED,
    ARTIFACT_REGISTERED,
    ARTIFACT_REVISED,
    CHECK_RECORDED,
    CLAIM_RECORDED,
    DECISION_RECORDED,
    DECISION_SUPERSEDED,
    EVIDENCE_REGISTERED,
    INITIATIVE_CLOSED,
    RESULT_IMPORTED,
    RUN_CANCELLED,
    STEP_TRANSITIONED,
)
from forge.errors import IntegrityError, SecurityError
from forge.storage.configuration import load_configuration
from forge.storage.objects import canonical_json_digest, verify_preserved_object
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout


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


def _decision_path(layout: RepositoryLayout, decision_id: UUID) -> Path:
    return layout.decision_directory / f"{decision_id}.json"


def _supersession_path(layout: RepositoryLayout, supersession_id: UUID) -> Path:
    return layout.decision_supersession_directory / f"{supersession_id}.json"


def _imported_result_path(layout: RepositoryLayout, result_id: UUID) -> Path:
    return layout.imported_result_directory / f"{result_id}.json"


def _closure_path(layout: RepositoryLayout, closure_id: UUID) -> Path:
    return layout.closure_directory / f"{closure_id}.json"


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
    return canonical_json_digest(
        {
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
    )


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
    expected_decisions: set[Path] = set()
    expected_supersessions: set[Path] = set()
    expected_imported_results: set[Path] = set()
    expected_closures: set[Path] = set()
    expected_runs: set[Path] = set()
    revisions_by_id: dict[UUID, ArtifactRevision] = {}
    artifact_roles: dict[UUID, str] = {}
    current_revision_ids: dict[UUID, UUID] = {}
    claims_by_id: dict[UUID, Claim] = {}
    checks_by_id: dict[UUID, CheckResult] = {}
    evidence_by_id: dict[UUID, EvidencePacket] = {}
    acceptances_by_id: dict[UUID, AcceptanceRecord] = {}
    acceptance_steps: dict[UUID, str] = {}
    decisions_by_id: dict[UUID, DecisionRecord] = {}
    runs_by_id: dict[UUID, RunRecord] = {}
    revoked_acceptance_ids: set[UUID] = set()
    stale_ids: set[UUID] = set()
    seen_event_record_ids: set[UUID] = set()
    owner_id = load_configuration(layout.configuration_file).owner.id

    for event in events:
        if event.event_type in {ARTIFACT_REGISTERED, ARTIFACT_REVISED}:
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
        elif event.event_type == CHECK_RECORDED:
            result_id = _uuid_metadata(event, "check_result_id")
            path = _check_path(layout, result_id)
            expected_checks.add(path)
            check = load_record(path, CheckResult)
            _validate_common(check, event, result_id)
            target_ids = _uuid_list_metadata(event, "target_artifact_revision_ids")
            if (
                check.id != result_id
                or check.actor != event.actor
                or check.check_id != event.metadata.get("check_id")
                or check.outcome.value != event.metadata.get("outcome")
                or check.target_artifact_revision_ids != target_ids
                or not set(target_ids).issubset(revisions_by_id)
                or _check_digest(check) != check.result_digest
                or check.result_digest not in event.affected_digests
            ):
                raise IntegrityError(f"Check result does not match event {event.id}")
            checks_by_id[result_id] = check
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
                if (
                    run.id != event.run_id
                    or run.worker != event.actor
                    or run.step_id != step.id
                    or run.status is not RunState.RUNNING
                    or run.started_at is None
                ):
                    raise IntegrityError(f"Run record does not match begin event {event.id}")
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
    _validate_directory(layout.decision_directory, expected_decisions)
    _validate_directory(layout.decision_supersession_directory, expected_supersessions)
    _validate_directory(layout.imported_result_directory, expected_imported_results)
    _validate_directory(layout.closure_directory, expected_closures)
    _validate_directory(layout.governed_run_directory, expected_runs)
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
