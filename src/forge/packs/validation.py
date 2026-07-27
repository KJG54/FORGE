"""Conformance rules for declarative FORGE packs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from forge.contracts.packs import PackManifest
from forge.contracts.structural_validators import StructuralValidatorDefinition
from forge.contracts.workflows import WorkflowDefinition
from forge.errors import ConfigurationError, IntegrityError

SUPPORTED_SCHEMA_COMPATIBILITY = "forge-contracts-1"
SUPPORTED_AUTHORITIES = {"owner", "participant", "forge-cli"}


class PackResourceKind(StrEnum):
    TEMPLATE = "template"
    STRUCTURAL_VALIDATOR = "structural-validator"


@dataclass(frozen=True)
class PackResource:
    path: str
    kind: PackResourceKind
    content: bytes
    content_digest: str
    definition: StructuralValidatorDefinition | None = None


@dataclass(frozen=True)
class ValidatedPack:
    source_path: Path
    manifest: PackManifest
    workflows: tuple[WorkflowDefinition, ...]
    resources: tuple[PackResource, ...] = ()
    bundled: bool = False

    def workflow(self, workflow_id: str | None = None) -> WorkflowDefinition:
        selected = workflow_id or self.manifest.provided_workflow_ids[0]
        for workflow in self.workflows:
            if workflow.id == selected:
                return workflow
        raise ConfigurationError(
            f"Pack {self.manifest.id} does not provide workflow {selected!r}"
        )


def calculate_pack_digest(
    manifest: PackManifest,
    workflows: tuple[WorkflowDefinition, ...],
    resources: tuple[PackResource, ...] = (),
) -> str:
    """Bind a pack manifest, workflows, and declared resource bytes without self-hashing."""
    payload = {
        "manifest": manifest.model_dump(mode="json", exclude={"integrity_digest"}),
        "workflows": [
            workflow.model_dump(mode="json")
            for workflow in sorted(workflows, key=lambda item: (item.id, item.version))
        ],
    }
    if resources:
        payload["resources"] = [
            {
                "path": resource.path,
                "kind": resource.kind.value,
                "content_digest": resource.content_digest,
            }
            for resource in sorted(resources, key=lambda item: (item.path, item.kind.value))
        ]
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _validate_workflow_reachability(workflow: WorkflowDefinition) -> None:
    if not workflow.steps:
        raise ConfigurationError(f"Workflow {workflow.id} must define at least one step")
    reachable: set[str] = set()
    remaining = {step.id: step for step in workflow.steps}
    while remaining:
        newly_reachable = {
            step_id
            for step_id, step in remaining.items()
            if set(step.prerequisites) <= reachable
        }
        if not newly_reachable:
            raise ConfigurationError(
                f"Workflow {workflow.id} contains cyclic or unreachable step prerequisites: "
                f"{sorted(remaining)}"
            )
        reachable.update(newly_reachable)
        for step_id in newly_reachable:
            del remaining[step_id]


def validate_pack(pack: ValidatedPack) -> None:
    manifest = pack.manifest
    workflows = pack.workflows
    resources = pack.resources
    if manifest.explanation_paths:
        raise ConfigurationError(
            "M5 Increment 3 supports templates and structural-validator data resources only; "
            "explanation resources remain unavailable"
        )
    declared_paths = (
        *manifest.template_paths,
        *manifest.explanation_paths,
        *manifest.data_resource_paths,
    )
    if len(declared_paths) != len(set(declared_paths)):
        raise ConfigurationError("Pack resource paths must be unique across all resource classes")
    resource_paths = tuple(resource.path for resource in resources)
    if len(resource_paths) != len(set(resource_paths)):
        raise ConfigurationError("Validated pack resources must have unique paths")
    expected_resource_paths = {
        *manifest.template_paths,
        *manifest.data_resource_paths,
    }
    if set(resource_paths) != expected_resource_paths:
        raise ConfigurationError(
            f"Pack {manifest.id} resource bytes do not match its declared resource paths"
        )
    template_paths = {
        resource.path
        for resource in resources
        if resource.kind is PackResourceKind.TEMPLATE
    }
    validator_resources = tuple(
        resource
        for resource in resources
        if resource.kind is PackResourceKind.STRUCTURAL_VALIDATOR
    )
    validator_paths = {resource.path for resource in validator_resources}
    if template_paths != set(manifest.template_paths):
        raise ConfigurationError(
            f"Pack {manifest.id} template resources do not match template_paths"
        )
    if validator_paths != set(manifest.data_resource_paths):
        raise ConfigurationError(
            f"Pack {manifest.id} structural validators do not match data_resource_paths"
        )
    for resource in resources:
        if resource.kind not in {
            PackResourceKind.TEMPLATE,
            PackResourceKind.STRUCTURAL_VALIDATOR,
        }:
            raise ConfigurationError(
                f"Pack {manifest.id} contains unsupported resource kind {resource.kind.value!r}"
            )
        if (
            resource.kind is PackResourceKind.TEMPLATE
            and resource.definition is not None
        ):
            raise ConfigurationError("Pack templates cannot contain validator definitions")
        if (
            resource.kind is PackResourceKind.STRUCTURAL_VALIDATOR
            and resource.definition is None
        ):
            raise ConfigurationError(
                f"Pack structural validator {resource.path} has no valid definition"
            )
        calculated_resource_digest = (
            f"sha256:{hashlib.sha256(resource.content).hexdigest()}"
        )
        if calculated_resource_digest != resource.content_digest:
            raise IntegrityError(
                f"Pack resource digest mismatch for {resource.path}: expected "
                f"{resource.content_digest}, calculated {calculated_resource_digest}"
            )
    definitions = tuple(
        resource.definition
        for resource in validator_resources
        if resource.definition is not None
    )
    definition_ids = [definition.id for definition in definitions]
    if len(definition_ids) != len(set(definition_ids)):
        raise ConfigurationError("Pack structural validator IDs must be unique")
    for definition in definitions:
        matching_steps = [
            step
            for workflow in workflows
            for step in workflow.steps
            if definition.check_id in step.check_requirements
        ]
        if not matching_steps:
            raise ConfigurationError(
                f"Structural validator {definition.id} check {definition.check_id!r} "
                "is not required by a provided workflow"
            )
        for rule in definition.artifact_rules:
            if any(
                rule.artifact_role not in step.required_outputs
                for step in matching_steps
            ):
                raise ConfigurationError(
                    f"Structural validator {definition.id} artifact role "
                    f"{rule.artifact_role!r} is not a required output of every matching step"
                )
    if SUPPORTED_SCHEMA_COMPATIBILITY not in manifest.schema_compatibility:
        raise ConfigurationError(
            f"Pack {manifest.id} does not declare {SUPPORTED_SCHEMA_COMPATIBILITY!r} compatibility"
        )
    provided = tuple(workflow.id for workflow in workflows)
    if len(provided) != len(set(provided)):
        raise ConfigurationError(f"Pack {manifest.id} contains duplicate workflow IDs")
    if set(provided) != set(manifest.provided_workflow_ids):
        raise ConfigurationError(
            f"Pack {manifest.id} workflow files do not match provided_workflow_ids"
        )
    for workflow in workflows:
        if workflow.pack_id != manifest.id:
            raise ConfigurationError(
                f"Workflow {workflow.id} belongs to {workflow.pack_id}, not {manifest.id}"
            )
        _validate_workflow_reachability(workflow)
        if not {"standard", "guided"} <= set(workflow.explanation_content):
            raise ConfigurationError(
                f"Workflow {workflow.id} must provide standard and guided explanations"
            )
        transitions = {transition.id: transition for transition in workflow.transitions}
        for transition in transitions.values():
            if transition.event_type != "step-transitioned":
                raise ConfigurationError(
                    f"M1 workflow transition {transition.id} must use step-transitioned events"
                )
            if transition.authority_requirement not in SUPPORTED_AUTHORITIES:
                raise ConfigurationError(
                    f"Transition {transition.id} uses unsupported authority requirement "
                    f"{transition.authority_requirement!r}"
                )
        for step in workflow.steps:
            if not step.allowed_actors:
                raise ConfigurationError(f"Workflow step {step.id} has no allowed actors")
            if not step.allowed_transitions:
                raise ConfigurationError(f"Workflow step {step.id} has no transitions")

    calculated = calculate_pack_digest(manifest, workflows, resources)
    if calculated != manifest.integrity_digest:
        raise IntegrityError(
            f"Pack {manifest.id} integrity digest mismatch: expected "
            f"{manifest.integrity_digest}, calculated {calculated}"
        )
