"""Executable capability registry and owner-controlled trust lifecycle."""

from __future__ import annotations

import shutil
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from forge import __version__
from forge.adapters import AdapterDiagnostic
from forge.contracts.actors import Actor
from forge.contracts.base import utc_now
from forge.contracts.capabilities import (
    CapabilityApproval,
    CapabilityDefinition,
    CapabilityRevocation,
    CapabilityTrustState,
    LocalValidatorDefinition,
    SideEffectClass,
)
from forge.contracts.events import AuditEvent
from forge.contracts.runs import RunRecord
from forge.core.agent_adapters import AdapterSelection, inspect_agent_adapter
from forge.core.authorization import require_owner
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.transitions import CAPABILITY_APPROVED, CAPABILITY_REVOKED
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.security.paths import resolve_repository_path
from forge.storage.configuration import load_configuration
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout
from forge.storage.snapshots import append_event_and_update_snapshot

_ADAPTER_CAPABILITIES = {
    "codex": "agent.codex.execute",
    "claude": "agent.claude.execute",
}
_CAPABILITY_VERSION = "1.0.0"
_WORKING_DIRECTORY_RULES = (".forge/local/runs",)
_OUTPUT_LOCATIONS = (
    ".forge/local/runs/<run-id>/stdout.jsonl",
    ".forge/local/runs/<run-id>/stderr.log",
    ".forge/local/runs/<run-id>/workspace/result",
)


@dataclass(frozen=True)
class CapabilityInspection:
    capability_type: Literal["agent", "validator"]
    definition: CapabilityDefinition
    definition_digest: str
    provider_version: str | None
    environment_access: tuple[str, ...]
    output_locations: tuple[str, ...]
    availability_detail: str
    compatible: bool

    @property
    def approval_durations(self) -> tuple[str, ...]:
        return (
            "approved-once: one governed run attempt",
            "approved-for-version: this capability version and invocation profile",
            "approved-for-project: current project initiative while the profile is unchanged",
        )


@dataclass(frozen=True)
class CapabilityApprovalView:
    approval: CapabilityApproval
    revocation: CapabilityRevocation | None
    consumed: bool
    applicable: bool

    @property
    def active(self) -> bool:
        return self.revocation is None and not self.consumed and self.applicable


@dataclass(frozen=True)
class CapabilityApprovalResult:
    approval: CapabilityApproval
    event: AuditEvent


@dataclass(frozen=True)
class CapabilityRevocationResult:
    revocation: CapabilityRevocation
    event: AuditEvent


def capability_id_for_adapter(adapter_id: str) -> str:
    try:
        return _ADAPTER_CAPABILITIES[adapter_id]
    except KeyError as error:
        raise ConflictError(f"Adapter {adapter_id!r} has no executable capability") from error


def _adapter_id_for_capability(capability_id: str) -> str:
    for adapter_id, registered_id in _ADAPTER_CAPABILITIES.items():
        if registered_id == capability_id:
            return adapter_id
    raise ConflictError(f"Unknown capability {capability_id!r}")


def _diagnostic(layout: RepositoryLayout, adapter_id: str) -> AdapterDiagnostic:
    selection = inspect_agent_adapter(layout, requested_adapter_id=adapter_id)
    return selection.requested_diagnostic or selection.diagnostic


def _inspection_from_diagnostic(
    adapter_id: str,
    diagnostic: AdapterDiagnostic,
) -> CapabilityInspection:
    capability_id = capability_id_for_adapter(adapter_id)
    definition = CapabilityDefinition(
        id=capability_id,
        version=_CAPABILITY_VERSION,
        provider=diagnostic.display_name,
        purpose=(
            "Execute one compatible local agent CLI in a disposable workspace and stage "
            "its untrusted result"
        ),
        input_schema_reference="canonical-agent-context",
        output_schema_reference="agent-result",
        executable=diagnostic.executable,
        arguments=(*diagnostic.argument_prefix, *diagnostic.invocation_arguments),
        working_directory_rules=_WORKING_DIRECTORY_RULES,
        timeout_seconds=3600,
        side_effect_class=SideEffectClass.REPOSITORY_WRITE,
        authorization_class="owner-capability-approval",
        trust_requirement=CapabilityTrustState.DISABLED,
        verification_hooks=("staged-result-validation",),
    )
    return CapabilityInspection(
        capability_type="agent",
        definition=definition,
        definition_digest=canonical_json_digest(definition.model_dump(mode="json")),
        provider_version=diagnostic.detected_version,
        environment_access=diagnostic.environment_keys,
        output_locations=_OUTPUT_LOCATIONS,
        availability_detail=diagnostic.availability.detail,
        compatible=(
            diagnostic.availability.available
            and diagnostic.compatibility.state.value == "compatible"
            and diagnostic.authentication_state in {"authenticated", "not-required"}
        ),
    )


def _resolve_local_executable(
    layout: RepositoryLayout,
    declared_executable: str,
) -> tuple[str | None, str]:
    candidate = Path(declared_executable)
    try:
        if candidate.is_absolute():
            resolved = candidate.resolve(strict=True)
        elif "/" in declared_executable or "\\" in declared_executable:
            resolved = resolve_repository_path(
                layout.root,
                declared_executable,
                must_exist=True,
            )
        else:
            discovered = shutil.which(declared_executable)
            if discovered is None:
                return None, f"Executable {declared_executable!r} was not found on PATH"
            resolved = Path(discovered).resolve(strict=True)
    except (OSError, RuntimeError, SecurityError) as error:
        return None, f"Executable {declared_executable!r} cannot be resolved safely: {error}"
    if not resolved.is_file():
        return None, f"Resolved executable is not a regular file: {resolved}"
    if resolved.suffix.lower() in {".bat", ".cmd"}:
        return None, (
            "Windows batch command shims are not accepted for validators; declare a native "
            "executable and argument vector"
        )
    return str(resolved), f"Resolved declared local executable to {resolved}"


def _inspection_from_local_validator(
    layout: RepositoryLayout,
    validator: LocalValidatorDefinition,
) -> CapabilityInspection:
    executable, availability_detail = _resolve_local_executable(
        layout,
        validator.executable,
    )
    working_directory_available = True
    if validator.working_directory is not None:
        try:
            working_directory = resolve_repository_path(
                layout.root,
                validator.working_directory,
                must_exist=True,
            )
        except SecurityError as error:
            working_directory_available = False
            availability_detail = (
                f"{availability_detail}; working directory cannot be resolved safely: {error}"
            )
        else:
            if not working_directory.is_dir():
                working_directory_available = False
                availability_detail = (
                    f"{availability_detail}; working directory is not a directory: "
                    f"{working_directory}"
                )
    working_directory_rules = (
        (validator.working_directory,) if validator.working_directory is not None else ()
    )
    definition = CapabilityDefinition(
        id=validator.id,
        version=validator.version,
        provider=validator.provider,
        purpose=validator.purpose,
        input_schema_reference="artifact-revision-set",
        output_schema_reference="check-result",
        executable=executable,
        arguments=validator.arguments,
        working_directory_rules=working_directory_rules,
        timeout_seconds=validator.timeout_seconds,
        side_effect_class=validator.side_effect_class,
        authorization_class="owner-capability-approval",
        trust_requirement=CapabilityTrustState.DISABLED,
        verification_hooks=validator.expected_outputs,
    )
    return CapabilityInspection(
        capability_type="validator",
        definition=definition,
        definition_digest=canonical_json_digest(definition.model_dump(mode="json")),
        provider_version=validator.provider_version,
        environment_access=validator.environment_access,
        output_locations=validator.expected_outputs,
        availability_detail=availability_detail,
        compatible=executable is not None and working_directory_available,
    )


def _local_validator_inspections(
    layout: RepositoryLayout,
) -> tuple[CapabilityInspection, ...]:
    configuration = load_configuration(layout.configuration_file)
    return tuple(
        _inspection_from_local_validator(layout, validator)
        for validator in configuration.capabilities.local_validators
    )


def list_capabilities(layout: RepositoryLayout) -> tuple[CapabilityInspection, ...]:
    agent_inspections = tuple(
        _inspection_from_diagnostic(adapter_id, _diagnostic(layout, adapter_id))
        for adapter_id in sorted(_ADAPTER_CAPABILITIES)
    )
    return tuple(
        sorted(
            (*agent_inspections, *_local_validator_inspections(layout)),
            key=lambda item: item.definition.id,
        )
    )


def inspect_capability(layout: RepositoryLayout, capability_id: str) -> CapabilityInspection:
    normalized = capability_id.strip()
    if normalized in _ADAPTER_CAPABILITIES.values():
        adapter_id = _adapter_id_for_capability(normalized)
        return _inspection_from_diagnostic(adapter_id, _diagnostic(layout, adapter_id))
    matches = [
        item
        for item in _local_validator_inspections(layout)
        if item.definition.id == normalized
    ]
    if not matches:
        raise ConflictError(f"Unknown capability {normalized!r}")
    return matches[0]


def inspect_selected_capability(
    selection: AdapterSelection,
) -> CapabilityInspection:
    return _inspection_from_diagnostic(selection.adapter.adapter_id, selection.diagnostic)


def _approval_path(layout: RepositoryLayout, record_id: UUID) -> Path:
    return layout.capability_approval_directory / f"{record_id}.json"


def _revocation_path(layout: RepositoryLayout, record_id: UUID) -> Path:
    return layout.capability_revocation_directory / f"{record_id}.json"


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


def _append_record_event(
    active: ActiveInitiative,
    path: Path,
    record: CapabilityApproval | CapabilityRevocation,
    event: AuditEvent,
) -> None:
    created = _ensure_record_directory(path.parent)
    try:
        write_record(path, record)
        append_event_and_update_snapshot(
            active.layout.event_journal_file,
            active.layout.state_file,
            event,
            active.reducer,
        )
    except Exception:
        if not _event_committed(active.layout, event.id):
            path.unlink(missing_ok=True)
            if created:
                with suppress(OSError):
                    path.parent.rmdir()
        raise


def _load_approvals(layout: RepositoryLayout) -> tuple[CapabilityApproval, ...]:
    directory = layout.capability_approval_directory
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise IntegrityError(f"Capability approval directory is missing or unsafe: {directory}")
    return tuple(
        sorted(
            (load_record(path, CapabilityApproval) for path in directory.glob("*.json")),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def _load_revocations(layout: RepositoryLayout) -> tuple[CapabilityRevocation, ...]:
    directory = layout.capability_revocation_directory
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise IntegrityError(f"Capability revocation directory is missing or unsafe: {directory}")
    return tuple(
        sorted(
            (load_record(path, CapabilityRevocation) for path in directory.glob("*.json")),
            key=lambda item: (item.event_sequence, str(item.id)),
        )
    )


def _used_approval_ids(layout: RepositoryLayout) -> set[UUID]:
    directory = layout.governed_run_directory
    if not directory.exists():
        return set()
    return {
        approval_id
        for path in directory.glob("*.json")
        for approval_id in load_record(path, RunRecord).capability_approval_ids
    }


def _profile_matches(
    approval: CapabilityApproval,
    inspection: CapabilityInspection,
) -> bool:
    definition = inspection.definition
    exact_profile = (
        approval.provider == definition.provider
        and approval.provider_version == inspection.provider_version
        and approval.executable == definition.executable
        and approval.arguments == definition.arguments
        and approval.working_directory_rules == definition.working_directory_rules
        and approval.environment_access == inspection.environment_access
        and approval.side_effect_class is definition.side_effect_class
    )
    if not exact_profile or approval.capability_id != definition.id:
        return False
    if inspection.capability_type == "validator":
        return (
            approval.capability_version == definition.version
            and approval.capability_digest == inspection.definition_digest
        )
    if approval.approval_scope is CapabilityTrustState.APPROVED_FOR_PROJECT:
        return True
    return (
        approval.capability_version == definition.version
        and approval.capability_digest == inspection.definition_digest
    )


def list_capability_approvals(
    layout: RepositoryLayout,
    *,
    capability_id: str | None = None,
) -> tuple[CapabilityApprovalView, ...]:
    if not layout.initiative_file.exists():
        return ()
    load_active_initiative(
        layout,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    revocations = {item.approval_id: item for item in _load_revocations(layout)}
    used = _used_approval_ids(layout)
    inspections = {
        item.definition.id: item
        for item in list_capabilities(layout)
    }
    views: list[CapabilityApprovalView] = []
    for approval in _load_approvals(layout):
        if capability_id is not None and approval.capability_id != capability_id:
            continue
        inspection = inspections.get(approval.capability_id)
        views.append(
            CapabilityApprovalView(
                approval=approval,
                revocation=revocations.get(approval.id),
                consumed=(
                    approval.approval_scope is CapabilityTrustState.APPROVED_ONCE
                    and approval.id in used
                ),
                applicable=(
                    inspection is not None and _profile_matches(approval, inspection)
                ),
            )
        )
    return tuple(views)


def approve_capability(
    layout: RepositoryLayout,
    *,
    capability_id: str,
    scope: CapabilityTrustState,
    rationale: str,
    actor: Actor,
) -> CapabilityApprovalResult:
    active = load_active_initiative(layout, allow_untrusted_pack=True)
    require_owner(actor, active.initiative.owner_identity_id, "approve executable capability")
    if scope is CapabilityTrustState.DISABLED:
        raise ConfigurationError("Use an approval scope that grants execution")
    rationale = rationale.strip()
    if not rationale:
        raise ConfigurationError("Capability approval rationale must not be empty")
    inspection = inspect_capability(layout, capability_id)
    definition = inspection.definition
    if not inspection.compatible or definition.executable is None:
        raise ConflictError(
            f"Capability {definition.id} cannot be approved: {inspection.availability_detail}"
        )
    if inspection.provider_version is None:
        raise ConflictError(f"Capability {definition.id} has no detected provider version")
    active_duplicates = [
        item for item in list_capability_approvals(layout, capability_id=definition.id)
        if item.active
        and _profile_matches(item.approval, inspection)
        and item.approval.approval_scope is scope
    ]
    if active_duplicates:
        raise ConflictError(
            f"Capability {definition.id} already has an active {scope.value} approval"
        )
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    approval_id = uuid4()
    event_id = uuid4()
    basis = "configured owner approved the exact inspected executable capability profile"
    approval = CapabilityApproval(
        id=approval_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=(approval_id,),
        affected_digests=(inspection.definition_digest,),
        capability_id=definition.id,
        capability_version=definition.version,
        capability_digest=inspection.definition_digest,
        provider=definition.provider,
        provider_version=inspection.provider_version,
        executable=definition.executable,
        arguments=definition.arguments,
        working_directory_rules=definition.working_directory_rules,
        environment_access=inspection.environment_access,
        side_effect_class=definition.side_effect_class,
        approval_scope=scope,
        rationale=rationale,
        owner_actor=actor,
        approval_event_id=event_id,
    )
    record_digest = canonical_json_digest(approval.model_dump(mode="json"))
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=CAPABILITY_APPROVED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(approval_id,),
        affected_digests=(inspection.definition_digest, record_digest),
        metadata={
            "approval_id": str(approval_id),
            "approval_scope": scope.value,
            "capability_id": definition.id,
            "capability_version": definition.version,
            "provider_version": inspection.provider_version,
        },
    )
    _append_record_event(active, _approval_path(layout, approval_id), approval, event)
    return CapabilityApprovalResult(approval, event)


def revoke_capability_approval(
    layout: RepositoryLayout,
    *,
    approval_id: UUID,
    reason: str,
    actor: Actor,
) -> CapabilityRevocationResult:
    active = load_active_initiative(layout, allow_untrusted_pack=True)
    require_owner(actor, active.initiative.owner_identity_id, "revoke capability approval")
    reason = reason.strip()
    if not reason:
        raise ConfigurationError("Capability revocation reason must not be empty")
    views = list_capability_approvals(layout)
    view = next((item for item in views if item.approval.id == approval_id), None)
    if view is None:
        raise ConflictError(f"Unknown capability approval {approval_id}")
    if view.revocation is not None:
        raise ConflictError(f"Capability approval {approval_id} is already revoked")
    now = utc_now()
    sequence = active.state.journal_head_sequence + 1
    revocation_id = uuid4()
    event_id = uuid4()
    basis = "configured owner revoked executable capability authorization"
    revocation = CapabilityRevocation(
        id=revocation_id,
        initiative_id=active.initiative.id,
        actor_id=actor.id,
        recorded_at=now,
        event_sequence=sequence,
        authorization_basis=basis,
        tool_version=__version__,
        affected_record_ids=(approval_id,),
        affected_digests=(view.approval.capability_digest,),
        approval_id=approval_id,
        reason=reason,
        owner_actor=actor,
        revocation_event_id=event_id,
    )
    record_digest = canonical_json_digest(revocation.model_dump(mode="json"))
    event = AuditEvent(
        id=event_id,
        initiative_id=active.initiative.id,
        sequence=sequence,
        timestamp=now,
        event_type=CAPABILITY_REVOKED,
        actor=actor,
        authorization_basis=basis,
        affected_record_ids=(revocation_id, approval_id),
        affected_digests=(view.approval.capability_digest, record_digest),
        metadata={
            "approval_id": str(approval_id),
            "capability_id": view.approval.capability_id,
            "revocation_id": str(revocation_id),
        },
    )
    _append_record_event(active, _revocation_path(layout, revocation_id), revocation, event)
    return CapabilityRevocationResult(revocation, event)


def require_capability_approval(
    layout: RepositoryLayout,
    selection: AdapterSelection,
) -> CapabilityApproval:
    inspection = inspect_selected_capability(selection)
    matches = [
        item for item in list_capability_approvals(
            layout, capability_id=inspection.definition.id
        )
        if item.active and _profile_matches(item.approval, inspection)
    ]
    if not matches:
        raise ConflictError(
            f"Capability {inspection.definition.id} is disabled; inspect and approve it with "
            f"'forge capability approve {inspection.definition.id}'"
        )
    priority = {
        CapabilityTrustState.APPROVED_ONCE: 0,
        CapabilityTrustState.APPROVED_FOR_VERSION: 1,
        CapabilityTrustState.APPROVED_FOR_PROJECT: 2,
    }
    return min(
        matches,
        key=lambda item: (priority[item.approval.approval_scope], item.approval.event_sequence),
    ).approval
