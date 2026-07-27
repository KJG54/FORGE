"""Deterministic in-process evaluation of trusted declarative structure rules."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from forge import __version__
from forge.contracts.artifacts import ArtifactRevision
from forge.contracts.base import utc_now
from forge.contracts.events import AuditEvent
from forge.contracts.state import StepState
from forge.contracts.structural_validators import StructuralValidatorDefinition
from forge.contracts.verification import CheckOutcome, CheckResult
from forge.core.artifacts import current_revisions_for_roles, list_artifacts
from forge.core.authorization import forge_cli_actor
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.transitions import CHECK_RECORDED
from forge.core.verification import (
    CheckRecordingResult,
    append_check_result,
    check_digest_payload,
)
from forge.errors import ConflictError, IntegrityError
from forge.packs.validation import PackResource, PackResourceKind
from forge.security.paths import resolve_repository_path
from forge.storage.objects import canonical_json_digest
from forge.storage.repository import RepositoryLayout

MAX_STRUCTURAL_ARTIFACT_BYTES = 1_048_576
MAX_STRUCTURAL_FINDINGS = 512
_STRUCTURAL_LIMITATION = (
    "This deterministic result checks declared text structure only. It does not establish "
    "source authenticity, citation correctness, semantic quality, methodological validity, "
    "factual truth, evidence sufficiency, verification, or owner acceptance."
)


@dataclass(frozen=True)
class StructuralCheckResult:
    definition: StructuralValidatorDefinition
    resource: PackResource
    recording: CheckRecordingResult
    findings: tuple[str, ...]


def _validator_resource(
    active: ActiveInitiative,
    *,
    validator_id: str,
    check_id: str,
) -> tuple[PackResource, StructuralValidatorDefinition]:
    matches = [
        resource
        for resource in active.pack_resources
        if (
            resource.kind is PackResourceKind.STRUCTURAL_VALIDATOR
            and resource.definition is not None
            and resource.definition.id == validator_id
        )
    ]
    if len(matches) != 1:
        raise ConflictError(
            f"Locked pack has no unique structural validator {validator_id!r}"
        )
    resource = matches[0]
    definition = resource.definition
    assert definition is not None
    if definition.check_id != check_id:
        raise ConflictError(
            f"Structural validator {validator_id!r} records {definition.check_id!r}, "
            f"not {check_id!r}"
        )
    return resource, definition


def _read_artifact(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read structural-check artifact {path}: {error}") from error


def _rule_findings(
    *,
    role: str,
    media_type: str,
    content: bytes,
    allowed_media_types: tuple[str, ...],
    required_headings: tuple[str, ...],
    required_field_prefixes: tuple[str, ...],
) -> list[str]:
    findings: list[str] = []
    if media_type not in allowed_media_types:
        return [f"{role}:unsupported-media-type:{media_type}"]
    if len(content) > MAX_STRUCTURAL_ARTIFACT_BYTES:
        return [
            f"{role}:artifact-exceeds-{MAX_STRUCTURAL_ARTIFACT_BYTES}-byte-structure-limit"
        ]
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [f"{role}:artifact-is-not-utf-8-text"]
    lines = tuple(line.strip() for line in text.splitlines())
    line_set = set(lines)
    for heading in required_headings:
        if heading not in line_set:
            findings.append(f"{role}:missing-heading:{heading}")
    for prefix in required_field_prefixes:
        values = [
            line.removeprefix(prefix).strip()
            for line in lines
            if line.startswith(prefix)
        ]
        if not values:
            findings.append(f"{role}:missing-field:{prefix}")
        elif not any(values):
            findings.append(f"{role}:empty-field:{prefix}")
    return findings


def execute_structural_check(
    layout: RepositoryLayout,
    *,
    step_id: str,
    check_id: str,
    validator_id: str,
) -> StructuralCheckResult:
    """Evaluate one locked data-only validator and record one immutable check."""

    active = load_active_initiative(layout)
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise ConflictError(f"Unknown workflow step {step_id!r}")
    if active.state.step_states.get(step_id) is not StepState.AWAITING_VERIFICATION:
        raise ConflictError(f"Step {step_id} is not awaiting verification")
    if check_id not in step.check_requirements:
        raise ConflictError(
            f"Check {check_id!r} is not declared for step {step_id}; required checks are "
            f"{list(step.check_requirements)}"
        )
    resource, definition = _validator_resource(
        active,
        validator_id=validator_id,
        check_id=check_id,
    )
    revisions = current_revisions_for_roles(active, step.required_outputs)
    artifact_roles = {
        view.artifact.id: view.artifact.role
        for view in list_artifacts(layout)
    }
    revisions_by_role: dict[str, list[ArtifactRevision]] = {}
    for revision in revisions:
        role = artifact_roles.get(revision.artifact_id)
        if role is None:
            raise IntegrityError(
                f"Artifact revision {revision.id} has no governed artifact role"
            )
        revisions_by_role.setdefault(role, []).append(revision)

    started_at = utc_now()
    findings: list[str] = []
    for rule in definition.artifact_rules:
        matching = revisions_by_role.get(rule.artifact_role, [])
        if not matching:
            findings.append(f"{rule.artifact_role}:missing-current-artifact")
            continue
        for revision_object in matching:
            artifact_path = resolve_repository_path(
                layout.root,
                revision_object.path,
                must_exist=True,
            )
            findings.extend(
                _rule_findings(
                    role=rule.artifact_role,
                    media_type=revision_object.media_type,
                    content=_read_artifact(artifact_path),
                    allowed_media_types=rule.allowed_media_types,
                    required_headings=rule.required_headings,
                    required_field_prefixes=rule.required_field_prefixes,
                )
            )
            if len(findings) >= MAX_STRUCTURAL_FINDINGS:
                findings = findings[:MAX_STRUCTURAL_FINDINGS]
                findings.append("finding-limit-reached")
                break
        if len(findings) > MAX_STRUCTURAL_FINDINGS:
            break

    ended_at = utc_now()
    actor = forge_cli_actor()
    target_ids = tuple(revision.id for revision in revisions)
    outcome = CheckOutcome.PASSED if not findings else CheckOutcome.FAILED
    limitations = tuple(dict.fromkeys((_STRUCTURAL_LIMITATION, *definition.limitations)))
    invocation_metadata = {
        "evaluated-artifact-roles": json.dumps(
            [rule.artifact_role for rule in definition.artifact_rules]
        ),
        "findings": json.dumps(findings, ensure_ascii=False),
        "mode": "declarative-in-process-structure",
        "validator-definition-digest": resource.content_digest,
        "validator-id": definition.id,
        "validator-resource-path": resource.path,
        "validator-version": definition.version,
    }
    result_digest = canonical_json_digest(
        check_digest_payload(
            check_id=check_id,
            check_version=definition.version,
            target_ids=target_ids,
            invocation_metadata=invocation_metadata,
            started_at=started_at,
            ended_at=ended_at,
            exit_status=None,
            outcome=outcome,
            limitations=limitations,
            actor=actor,
        )
    )
    sequence = active.state.journal_head_sequence + 1
    result_id = uuid4()
    basis = (
        "FORGE CLI evaluated owner-trusted exact declarative structure rules without "
        "executable capability authority"
    )
    artifact_digests = tuple(revision.content_digest for revision in revisions)
    check = CheckResult(
        id=result_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=ended_at,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=target_ids,
        affected_digests=(resource.content_digest, *artifact_digests),
        check_id=check_id,
        check_version=definition.version,
        target_artifact_revision_ids=target_ids,
        invocation_metadata=invocation_metadata,
        started_at=started_at,
        ended_at=ended_at,
        outcome=outcome,
        limitations=limitations,
        result_digest=result_digest,
        actor=actor,
    )
    event = AuditEvent(
        id=uuid4(),
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=ended_at,
        event_type=CHECK_RECORDED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(result_id, *target_ids),
        affected_digests=(
            result_digest,
            resource.content_digest,
            *artifact_digests,
        ),
        metadata={
            "check_id": check_id,
            "check_result_id": str(result_id),
            "outcome": outcome.value,
            "step_id": step_id,
            "structural_validator_id": definition.id,
            "structural_validator_resource_digest": resource.content_digest,
            "target_artifact_revision_ids": [str(item) for item in target_ids],
        },
    )
    append_check_result(active, check, event)
    recording = CheckRecordingResult(check, event)
    return StructuralCheckResult(definition, resource, recording, tuple(findings))
