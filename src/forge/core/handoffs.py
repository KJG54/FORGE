"""Portable provider-neutral manual handoff generation."""

from __future__ import annotations

import json
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from forge.contracts.agents import AgentHandoff, AgentResult
from forge.contracts.state import StepState
from forge.core.lifecycle import load_active_initiative
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.records import load_record, render_record
from forge.storage.repository import RepositoryLayout


@dataclass(frozen=True)
class HandoffResult:
    handoff: AgentHandoff
    directory: Path
    json_path: Path
    markdown_path: Path
    result_schema_path: Path


def _require_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{label} must not be empty")
    return normalized


def _ensure_safe_directory(path: Path, created: list[Path]) -> None:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ConflictError(f"Expected a directory at {path}")
        return
    try:
        path.mkdir()
    except OSError as error:
        raise IntegrityError(f"Cannot create handoff directory {path}: {error}") from error
    created.append(path)


def _render_markdown(handoff: AgentHandoff) -> bytes:
    constraints = "\n".join(f"- {item}" for item in handoff.constraints) or "- None declared"
    decisions = (
        "\n".join(f"- `{item}`" for item in handoff.relevant_decision_ids)
        or "- No open decisions"
    )
    permitted = "\n".join(f"- {item}" for item in handoff.permitted_actions)
    prohibited = "\n".join(f"- {item}" for item in handoff.prohibited_actions)
    outputs = "\n".join(f"- `{item}`" for item in handoff.required_outputs)
    verification = "\n".join(
        f"- {item}" for item in handoff.verification_expectations
    )
    document = f"""# FORGE Manual Handoff

Handoff ID: `{handoff.id}`

Initiative ID: `{handoff.initiative_id}`

Active step: `{handoff.step_id}`

## Objective

{handoff.objective}

## Approved scope

{handoff.approved_scope}

## Constraints

{constraints}

## Relevant open decisions

{decisions}

## Permitted actions

{permitted}

## Prohibited actions

{prohibited}

## Required outputs

{outputs}

## Return contract

Return an `AgentResult` JSON document conforming to `{handoff.return_manifest_schema}`. Returned
files and worker claims remain untrusted. They cannot approve scope, checks, evidence, or owner
acceptance and must pass FORGE staged import before registration.

## Verification expectations

{verification}
"""
    return document.encode("utf-8")


def create_handoff(
    layout: RepositoryLayout,
    *,
    step_id: str,
    constraints: tuple[str, ...] = (),
) -> HandoffResult:
    """Create disposable neutral assignment files under ``.forge/local``."""

    active = load_active_initiative(layout)
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise ConflictError(f"Unknown workflow step {step_id!r}")
    state = active.state.step_states[step_id]
    if state not in {StepState.READY, StepState.IN_PROGRESS, StepState.INVALIDATED}:
        raise ConflictError(
            f"Step {step_id} cannot produce a handoff from state {state.value}"
        )
    normalized_constraints = tuple(
        _require_text("Handoff constraint", item) for item in constraints
    )
    handoff_id = uuid4()
    handoff = AgentHandoff(
        id=handoff_id,
        initiative_id=active.initiative.id,
        step_id=step.id,
        objective=active.initiative.objective,
        approved_scope=active.initiative.declared_scope_summary,
        constraints=normalized_constraints,
        relevant_decision_ids=active.state.open_decision_ids,
        permitted_actions=(
            "Create only the declared returned files within the approved scope",
            "Report worker claims, tool metadata, and limitations without governance approval",
        ),
        prohibited_actions=(
            "Record or imply owner decisions, acceptance, checks, or evidence",
            "Modify FORGE-managed paths or undeclared project files",
            "Execute external or irreversible side effects without separate authorization",
        ),
        required_outputs=step.required_outputs,
        return_manifest_schema="agent-result.schema.json",
        verification_expectations=(
            *(f"Declared check required after import: {item}" for item in step.check_requirements),
            "Imported files require a new worker claim and evidence",
            "Configured owner acceptance remains a separate final decision",
        ),
    )
    directory = layout.handoff_directory / str(handoff_id)
    json_path = directory / "handoff.json"
    markdown_path = directory / "handoff.md"
    schema_path = directory / handoff.return_manifest_schema
    created: list[Path] = []
    try:
        _ensure_safe_directory(layout.handoff_directory, created)
        _ensure_safe_directory(directory, created)
        atomic_write_bytes(json_path, render_record(handoff))
        atomic_write_bytes(markdown_path, _render_markdown(handoff))
        schema = json.dumps(
            AgentResult.model_json_schema(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8") + b"\n"
        atomic_write_bytes(schema_path, schema)
    except Exception:
        for path in (schema_path, markdown_path, json_path):
            path.unlink(missing_ok=True)
        for path in reversed(created):
            with suppress(OSError):
                path.rmdir()
        raise
    return HandoffResult(handoff, directory, json_path, markdown_path, schema_path)


def load_handoff(layout: RepositoryLayout, handoff_id: UUID) -> AgentHandoff:
    path = layout.handoff_directory / str(handoff_id) / "handoff.json"
    return load_record(path, AgentHandoff)
