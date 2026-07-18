"""Deterministic, provider-neutral canonical agent context generation."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from uuid import UUID

from forge.contracts.agents import (
    AgentContextDecision,
    AgentContextInput,
    AgentContextReturnContract,
    AgentContextStep,
    CanonicalAgentContext,
)
from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.contracts.decisions import DecisionRecord
from forge.contracts.state import InitiativeLifecycleState, StepState
from forge.core.artifacts import assert_working_revision_current
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.journal import read_journal
from forge.storage.locking import repository_mutation_lock
from forge.storage.records import load_record, render_record
from forge.storage.repository import RepositoryLayout


class AgentContextTarget(StrEnum):
    NEUTRAL = "neutral"
    CODEX = "codex"
    CLAUDE = "claude"


@dataclass(frozen=True)
class AgentContextGenerationResult:
    context: CanonicalAgentContext
    json_path: Path
    markdown_path: Path


_ACTIONABLE_STATES = {StepState.READY, StepState.IN_PROGRESS, StepState.INVALIDATED}


def _selected_inputs(
    active: ActiveInitiative,
    required_roles: tuple[str, ...],
) -> tuple[tuple[AgentContextInput, ...], tuple[str, ...]]:
    if not required_roles:
        return (), ()
    selected: list[AgentContextInput] = []
    blockers: list[str] = []
    found_roles: set[str] = set()
    for artifact_id, revision_number in sorted(
        active.state.current_artifact_revisions.items(), key=lambda item: str(item[0])
    ):
        record = load_record(
            active.layout.artifact_record_directory / f"{artifact_id}.{revision_number}.json",
            ArtifactRecord,
        )
        if record.role not in required_roles:
            continue
        revision = _current_revision(active, artifact_id, revision_number)
        found_roles.add(record.role)
        try:
            assert_working_revision_current(active.layout, revision)
        except ConflictError as error:
            blockers.append(str(error))
        selected.append(
            AgentContextInput(
                role=record.role,
                path=revision.path,
                content_digest=revision.content_digest,
                media_type=revision.media_type,
            )
        )
    for role in required_roles:
        if role not in found_roles:
            blockers.append(f"Required input role is not registered: {role}")
    selected.sort(
        key=lambda item: (required_roles.index(item.role), item.path, item.content_digest)
    )
    return tuple(selected), tuple(blockers)


def _current_revision(
    active: ActiveInitiative,
    artifact_id: UUID,
    revision_number: int,
) -> ArtifactRevision:
    """Find one exact current revision without reading project artifact content."""

    matches: list[ArtifactRevision] = []
    for path in active.layout.artifact_revision_directory.glob("*.json"):
        revision = load_record(path, ArtifactRevision)
        if revision.artifact_id == artifact_id and revision.revision_number == revision_number:
            matches.append(revision)
    if len(matches) != 1:
        raise IntegrityError(
            f"Artifact {artifact_id} current revision {revision_number} lacks one record identity"
        )
    return matches[0]


def _active_decisions(active: ActiveInitiative) -> tuple[AgentContextDecision, ...]:
    decisions = [
        load_record(active.layout.decision_directory / f"{decision_id}.json", DecisionRecord)
        for decision_id in active.state.open_decision_ids
    ]
    decisions.sort(key=lambda item: (item.event_sequence, str(item.id)))
    return tuple(
        AgentContextDecision(
            id=item.id,
            decision_type=item.decision_type,
            question=item.question,
            chosen_outcome=item.chosen_outcome,
            rationale=item.rationale,
        )
        for item in decisions
    )


def _pause_blocker(active: ActiveInitiative) -> str:
    pause_id = active.state.active_pause_event_id
    pause_event = next(
        (event for event in read_journal(active.layout.event_journal_file) if event.id == pause_id),
        None,
    )
    reason = pause_event.metadata.get("reason") if pause_event is not None else None
    if not isinstance(reason, str) or not reason.strip():
        raise IntegrityError("Paused initiative lacks a valid governing pause reason")
    return f"Initiative paused: {reason}"


def _state_blockers(active: ActiveInitiative, step_state: StepState) -> tuple[str, ...]:
    blockers: list[str] = []
    if active.state.lifecycle_state is InitiativeLifecycleState.PAUSED:
        blockers.append(_pause_blocker(active))
    if active.state.journal_head_hash is None:
        blockers.append("Legacy M1 journal must be migrated before worker execution")
    state_messages = {
        StepState.PENDING: "Active step is pending its prerequisites",
        StepState.BLOCKED: "Active step is blocked for owner review",
        StepState.AWAITING_VERIFICATION: "Active step is awaiting FORGE verification",
        StepState.AWAITING_ACCEPTANCE: "Active step is awaiting configured-owner acceptance",
        StepState.COMPLETED: "Active step is already completed",
        StepState.SKIPPED: "Active step is skipped",
    }
    if step_state in state_messages:
        blockers.append(state_messages[step_state])
    return tuple(blockers)


def build_agent_context(layout: RepositoryLayout) -> CanonicalAgentContext:
    """Derive bounded context without scanning unrelated repository or archive paths."""

    active = load_active_initiative(layout, allow_paused=True)
    step_id = active.state.current_step_id
    if step_id is None:
        raise ConflictError("Active initiative has no current workflow step")
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise IntegrityError(f"Current workflow step {step_id!r} is missing from its lock")
    step_state = active.state.step_states[step.id]
    selected_inputs, input_blockers = _selected_inputs(active, step.required_inputs)
    blockers = (*_state_blockers(active, step_state), *input_blockers)
    permitted_actions = ()
    if (
        active.state.lifecycle_state is InitiativeLifecycleState.ACTIVE
        and step_state in _ACTIONABLE_STATES
        and not blockers
    ):
        permitted_actions = (
            "Create only declared returned files within the approved scope",
            "Report worker claims, tool metadata, and limitations without governance approval",
            "Use only the selected required-input paths listed in the active step",
        )
    relevant_constraints = tuple(
        f"Context selection rule: {item}" for item in step.context_selection_rules
    )
    expected_evidence = (
        *(f"Worker claim requirement: {item}" for item in step.claim_requirements),
        *(f"Check requirement after import: {item}" for item in step.check_requirements),
        *(
            f"Workflow evidence class after import: {item}"
            for item in active.workflow.required_evidence_classes
        ),
        *(f"Owner-only acceptance requirement: {item}" for item in step.acceptance_requirements),
        "Returned files require staged import before registration",
        "Worker claims never constitute checks, evidence, or owner acceptance",
    )
    return CanonicalAgentContext(
        objective=active.initiative.objective,
        active_step=AgentContextStep(
            id=step.id,
            state=step_state,
            purpose=step.purpose,
            instructions=step.instructions,
            required_inputs=selected_inputs,
            context_selection_rules=step.context_selection_rules,
        ),
        approved_scope=active.initiative.declared_scope_summary,
        relevant_constraints=relevant_constraints,
        relevant_decisions=_active_decisions(active),
        permitted_actions=permitted_actions,
        prohibited_actions=(
            "Record or imply owner decisions, acceptance, checks, or evidence",
            "Modify FORGE-managed paths or undeclared project files",
            "Read unrelated repository, archive, ignored, environment, or local-secret content",
            "Execute external or irreversible side effects without separate authorization",
        ),
        required_outputs=step.required_outputs,
        expected_evidence=expected_evidence,
        return_contract=AgentContextReturnContract(
            requirements=(
                "Bind source_run_or_handoff_id to the identifier supplied by FORGE",
                "Declare every returned file, worker claim, limitation, and tool metadata item",
                "Treat every returned file and claim as untrusted until staged import succeeds",
            )
        ),
        known_blockers=blockers,
    )


def _render_markdown(context: CanonicalAgentContext) -> bytes:
    def bullets(values: tuple[object, ...], empty: str) -> str:
        return "\n".join(f"- {item}" for item in values) or f"- {empty}"

    inputs = "\n".join(
        f"- `{item.role}`: `{item.path}` ({item.content_digest}, {item.media_type})"
        for item in context.active_step.required_inputs
    ) or "- None"
    decisions = "\n".join(
        f"- `{item.id}` ({item.decision_type}): {item.chosen_outcome}\n"
        f"  - Question: {item.question}\n  - Rationale: {item.rationale}"
        for item in context.relevant_decisions
    ) or "- None"
    return_requirements = bullets(context.return_contract.requirements, "None")
    document = f"""# FORGE Canonical Agent Context

## Objective

{context.objective}

## Active step

- ID: `{context.active_step.id}`
- State: `{context.active_step.state.value}`
- Purpose: {context.active_step.purpose}
- Instructions: {context.active_step.instructions}
- Context selection rules: {', '.join(context.active_step.context_selection_rules) or 'none'}

### Selected required inputs

{inputs}

## Approved scope

{context.approved_scope}

## Relevant constraints

{bullets(context.relevant_constraints, 'None')}

## Relevant decisions

{decisions}

## Permitted actions

{bullets(context.permitted_actions, 'No worker action is currently permitted')}

## Prohibited actions

{bullets(context.prohibited_actions, 'None')}

## Required outputs

{bullets(context.required_outputs, 'None')}

## Expected evidence

{bullets(context.expected_evidence, 'None')}

## Return contract

- Contract: `{context.return_contract.contract}`
- Manifest filename: `{context.return_contract.manifest_filename}`
- Schema filename: `{context.return_contract.schema_filename}`
{return_requirements}

## Known blockers

{bullets(context.known_blockers, 'None')}
"""
    return document.encode("utf-8")


def _ensure_context_directory(path: Path) -> bool:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link context directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Expected a context directory at {path}")
        return False
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create agent context directory {path}: {error}") from error
    return True


def generate_agent_context(
    layout: RepositoryLayout,
    *,
    target: AgentContextTarget = AgentContextTarget.NEUTRAL,
) -> AgentContextGenerationResult:
    """Atomically replace the two regenerable neutral current-context views."""

    if target is not AgentContextTarget.NEUTRAL:
        raise ConfigurationError(
            f"Agent context target {target.value!r} requires the deferred "
            "managed-vendor-view increment"
        )
    with repository_mutation_lock(layout, command="agent-context"):
        context = build_agent_context(layout)
        json_bytes = render_record(context)
        markdown_bytes = _render_markdown(context)
        created = _ensure_context_directory(layout.agent_context_directory)
        try:
            atomic_write_bytes(layout.current_agent_context_json_file, json_bytes)
            atomic_write_bytes(layout.current_agent_context_markdown_file, markdown_bytes)
        except Exception:
            if created:
                for path in (
                    layout.current_agent_context_markdown_file,
                    layout.current_agent_context_json_file,
                ):
                    path.unlink(missing_ok=True)
                with suppress(OSError):
                    layout.agent_context_directory.rmdir()
            raise
    return AgentContextGenerationResult(
        context=context,
        json_path=layout.current_agent_context_json_file,
        markdown_path=layout.current_agent_context_markdown_file,
    )


def load_agent_context(layout: RepositoryLayout) -> CanonicalAgentContext:
    return load_record(layout.current_agent_context_json_file, CanonicalAgentContext)
