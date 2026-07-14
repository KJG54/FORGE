"""Cross-check Increment 4 governed records against journal events and preserved bytes."""

from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID

from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.contracts.events import AuditEvent
from forge.contracts.state import MaterializedState, StepState
from forge.contracts.verification import CheckOutcome, CheckResult, Claim, EvidencePacket
from forge.contracts.workflows import WorkflowDefinition
from forge.core.transitions import (
    ARTIFACT_REGISTERED,
    ARTIFACT_REVISED,
    CHECK_RECORDED,
    CLAIM_RECORDED,
    EVIDENCE_REGISTERED,
    STEP_TRANSITIONED,
)
from forge.errors import IntegrityError, SecurityError
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


def validate_increment4_records(
    layout: RepositoryLayout,
    events: tuple[AuditEvent, ...],
    state: MaterializedState,
    workflow: WorkflowDefinition,
) -> None:
    """Validate every Increment 4 record and its event/object dependencies."""
    expected_artifact_records: set[Path] = set()
    expected_revisions: set[Path] = set()
    expected_claims: set[Path] = set()
    expected_checks: set[Path] = set()
    expected_evidence: set[Path] = set()
    revisions_by_id: dict[UUID, ArtifactRevision] = {}
    artifact_roles: dict[UUID, str] = {}
    current_revision_ids: dict[UUID, UUID] = {}
    claims_by_id: dict[UUID, Claim] = {}
    checks_by_id: dict[UUID, CheckResult] = {}
    evidence_by_id: dict[UUID, EvidencePacket] = {}

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
            verify_preserved_object(
                layout,
                repository_path=revision.preserved_object_path,
                expected_digest=revision.content_digest,
                expected_size=revision.byte_size,
            )
            revisions_by_id[revision_id] = revision
            artifact_roles[artifact_id] = artifact.role
            current_revision_ids[artifact_id] = revision_id
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
        elif event.event_type == STEP_TRANSITIONED:
            destination = event.metadata.get("destination_state")
            step_id = event.metadata.get("step_id")
            step = next((item for item in workflow.steps if item.id == step_id), None)
            if step is None:
                raise IntegrityError(f"Transition event {event.id} references an unknown step")
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
    expected_state = {
        artifact_id: revisions_by_id[revision_id].revision_number
        for artifact_id, revision_id in current_revision_ids.items()
    }
    if state.current_artifact_revisions != expected_state:
        raise IntegrityError("Materialized artifact revisions do not match governed records")
