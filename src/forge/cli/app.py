"""Command-line presentation for the currently authorized FORGE increment."""

from collections.abc import Callable
from functools import wraps
from inspect import signature
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer

from forge import __version__
from forge.contracts.capabilities import CapabilityTrustState, SideEffectClass
from forge.contracts.recovery import JournalRecoveryRecord
from forge.contracts.state import ExplanationProfile
from forge.contracts.verification import CheckOutcome
from forge.core.acceptance import (
    list_acceptances,
    record_acceptance,
    revoke_acceptance,
    show_acceptance,
)
from forge.core.agent_adapters import inspect_agent_adapter, prepare_agent_handoff
from forge.core.agent_context import AgentContextTarget, generate_agent_context
from forge.core.agent_runs import execute_agent_run
from forge.core.archival import abandon_initiative, close_initiative
from forge.core.artifacts import add_artifact, list_artifacts, revise_artifact, show_artifact
from forge.core.authorization import owner_actor
from forge.core.capabilities import (
    CapabilityInspection,
    approve_capability,
    inspect_capability,
    list_capabilities,
    list_capability_approvals,
    revoke_capability_approval,
)
from forge.core.command_recovery import recover_command_receipt
from forge.core.continuity import pause_initiative, resume_initiative
from forge.core.decisions import record_decision
from forge.core.diagnostics import inspect_repository_health
from forge.core.history import inspect_history_report
from forge.core.imports import apply_result_import, preview_result_import
from forge.core.lifecycle import begin_manual_run, create_initiative
from forge.core.lock_remediation import remediate_stale_lock
from forge.core.migrations import inspect_active_migration, migrate_active_repository
from forge.core.recovery import recover_active_snapshot
from forge.core.runs import cancel_run, list_runs, show_run
from forge.core.status import inspect_status
from forge.core.vendor_context import apply_vendor_context, preview_vendor_context
from forge.core.verification import (
    complete_step,
    dependency_references,
    list_checks,
    list_evidence,
    record_check,
    record_evidence,
    show_evidence,
    verify_step,
)
from forge.errors import ConfigurationError, ForgeError
from forge.packs.loader import available_packs, find_pack
from forge.schemas import export_schema_bundle
from forge.storage.configuration import load_configuration, render_configuration
from forge.storage.idempotency import idempotent_mutation, normalize_idempotency_key
from forge.storage.locking import repository_mutation_lock
from forge.storage.repository import discover_repository, initialize_repository

app = typer.Typer(
    name="forge",
    help="Govern human-directed, AI-assisted work in an ordinary repository.",
    no_args_is_help=True,
)
schema_app = typer.Typer(help="Inspect or export versioned FORGE schemas.")
config_app = typer.Typer(help="Inspect or validate project-level FORGE configuration.")
pack_app = typer.Typer(help="Inspect validated declarative data packs.")
artifact_app = typer.Typer(help="Register and inspect immutable artifact revisions.")
check_app = typer.Typer(help="Record and inspect structured manual checks.")
evidence_app = typer.Typer(help="Register and inspect durable evidence packets.")
acceptance_app = typer.Typer(help="Record, inspect, or revoke owner acceptance.")
run_app = typer.Typer(help="Inspect or cancel durable work attempts.")
agent_app = typer.Typer(help="Generate neutral worker context and inspect agent integrations.")
capability_app = typer.Typer(help="Inspect, approve, or revoke executable capabilities.")
IdempotencyOption = Annotated[
    str | None,
    typer.Option(
        "--idempotency-key",
        help="Stable retry key; FORGE generates and reports one when omitted.",
    ),
]
app.add_typer(schema_app, name="schema")
app.add_typer(config_app, name="config")
app.add_typer(pack_app, name="pack")
app.add_typer(artifact_app, name="artifact")
app.add_typer(check_app, name="check")
app.add_typer(evidence_app, name="evidence")
app.add_typer(acceptance_app, name="acceptance")
app.add_typer(run_app, name="run")
app.add_typer(agent_app, name="agent")
app.add_typer(capability_app, name="capability")


def _locked_mutation[**P](function: Callable[P, None]) -> Callable[P, None]:
    @wraps(function)
    def locked(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            bound = signature(function).bind(*args, **kwargs)
            bound.apply_defaults()
            directory = bound.arguments.get("directory", Path("."))
            if not isinstance(directory, Path):
                raise ConfigurationError("Mutation command directory must be a filesystem path")
            layout = discover_repository(directory)
            parameters = dict(bound.arguments)
            if function.__name__ in {
                "capability_approve",
                "import_result",
                "migrate",
            } and not parameters.get("apply_changes"):
                function(*args, **kwargs)
                return
            with repository_mutation_lock(layout, command=function.__name__):
                provided_key = parameters.pop("idempotency_key", None)
                parameters.pop("directory", None)
                if provided_key is not None and not isinstance(provided_key, str):
                    raise ConfigurationError("Idempotency key must be text")
                with idempotent_mutation(
                    layout,
                    command=function.__name__,
                    provided_key=provided_key,
                    parameters=parameters,
                    resume_incomplete=function.__name__
                    in {"abandon", "close", "migrate", "recover", "recover_command"},
                    allow_recoverable_active_journal=function.__name__ == "recover",
                    additional_allowed_incomplete_keys=(
                        (str(parameters["interrupted_key"]),)
                        if function.__name__ == "recover_command"
                        else ()
                    ),
                ) as invocation:
                    typer.echo(f"Idempotency key: {invocation.key}")
                    if invocation.is_replay:
                        assert invocation.receipt is not None
                        event_ids = ", ".join(
                            str(item.event_id) for item in invocation.receipt.events
                        )
                        typer.echo(f"Idempotent replay; committed event(s): {event_ids}")
                        return
                    function(*args, **kwargs)
        except ForgeError as error:
            _fail(error)

    return locked


def _echo_capability_inspection(inspection: CapabilityInspection) -> None:
    definition = inspection.definition
    typer.echo(f"Capability: {definition.id}@{definition.version}")
    typer.echo(f"Definition digest: {inspection.definition_digest}")
    typer.echo(f"Provider: {definition.provider}")
    typer.echo(f"Provider version: {inspection.provider_version or '<unknown>'}")
    typer.echo(f"Exact executable: {definition.executable or '<unavailable>'}")
    typer.echo("Arguments:")
    for argument in definition.arguments:
        typer.echo(f"- {argument}")
    typer.echo(
        "Argument construction: fixed FORGE adapter vector; Windows command shims include "
        "the inspected cmd.exe /c vector"
    )
    typer.echo("Working-directory rules:")
    for rule in definition.working_directory_rules:
        typer.echo(f"- {rule}/<run-id>/workspace")
    typer.echo("Environment access:")
    for key in inspection.environment_access:
        typer.echo(f"- {key}")
    typer.echo(f"Side-effect class: {definition.side_effect_class.value}")
    typer.echo("Output locations:")
    for location in inspection.output_locations:
        typer.echo(f"- {location}")
    typer.echo("Approval duration choices:")
    for duration in inspection.approval_durations:
        typer.echo(f"- {duration}")
    typer.echo(f"Execution readiness: {'ready' if inspection.compatible else 'disabled'}")
    typer.echo(f"Availability: {inspection.availability_detail}")


@capability_app.command("list")
def capability_list(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """List registered executable capabilities and current trust state."""
    try:
        layout = discover_repository(directory)
        inspections = list_capabilities(layout)
        approvals = list_capability_approvals(layout)
    except ForgeError as error:
        _fail(error)
        return
    for inspection in inspections:
        active = [
            item.approval.approval_scope.value
            for item in approvals
            if item.approval.capability_id == inspection.definition.id and item.active
        ]
        state = ", ".join(active) if active else CapabilityTrustState.DISABLED.value
        executable = inspection.definition.executable or "<unavailable>"
        typer.echo(
            f"{inspection.definition.id}@{inspection.definition.version}  "
            f"trust={state}  executable={executable}"
        )


@capability_app.command("inspect")
def capability_inspect(
    capability_id: Annotated[str, typer.Argument(help="Registered capability ID.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Inspect the exact executable profile and durable approval history."""
    try:
        layout = discover_repository(directory)
        inspection = inspect_capability(layout, capability_id)
        approvals = list_capability_approvals(
            layout, capability_id=inspection.definition.id
        )
    except ForgeError as error:
        _fail(error)
        return
    _echo_capability_inspection(inspection)
    typer.echo("Approval history:")
    if not approvals:
        typer.echo("- none; capability is disabled")
    for view in approvals:
        if view.revocation is not None:
            state = f"revoked by {view.revocation.id}"
        elif view.consumed:
            state = "consumed"
        elif not view.applicable:
            state = "inactive-profile-changed"
        else:
            state = "active"
        typer.echo(
            f"- {view.approval.id}: {view.approval.approval_scope.value}, {state}, "
            f"recorded {view.approval.recorded_at.isoformat()}"
        )


@capability_app.command("approve")
@_locked_mutation
def capability_approve(
    capability_id: Annotated[str, typer.Argument(help="Registered capability ID.")],
    rationale: Annotated[
        str,
        typer.Option("--rationale", help="Why this executable authority is acceptable."),
    ],
    scope: Annotated[
        CapabilityTrustState,
        typer.Option("--scope", help="Approval duration/scope."),
    ] = CapabilityTrustState.APPROVED_ONCE,
    apply_changes: Annotated[
        bool,
        typer.Option("--apply", help="Persist the displayed owner approval."),
    ] = False,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Preview or persist owner approval for one exact capability profile."""
    layout = discover_repository(directory)
    if scope is CapabilityTrustState.DISABLED:
        raise ConfigurationError("Use an approval scope that grants execution")
    if not rationale.strip():
        raise ConfigurationError("Capability approval rationale must not be empty")
    inspection = inspect_capability(layout, capability_id)
    _echo_capability_inspection(inspection)
    typer.echo(f"Selected approval duration: {scope.value}")
    typer.echo(f"Rationale: {rationale}")
    if not apply_changes:
        typer.echo("Preview only; rerun with --apply to persist this owner approval")
        return
    configuration = load_configuration(layout.configuration_file)
    result = approve_capability(
        layout,
        capability_id=capability_id,
        scope=scope,
        rationale=rationale,
        actor=owner_actor(configuration.owner),
    )
    typer.echo(f"Capability approval recorded: {result.approval.id}")


@capability_app.command("revoke")
@_locked_mutation
def capability_revoke(
    approval_id: Annotated[UUID, typer.Argument(help="Capability approval UUID.")],
    reason: Annotated[
        str,
        typer.Option("--reason", help="Why future execution is no longer authorized."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Revoke future execution while retaining immutable approval history."""
    layout = discover_repository(directory)
    configuration = load_configuration(layout.configuration_file)
    result = revoke_capability_approval(
        layout,
        approval_id=approval_id,
        reason=reason,
        actor=owner_actor(configuration.owner),
    )
    typer.echo(f"Capability approval revoked: {approval_id}")
    typer.echo(f"Revocation record: {result.revocation.id}")


@agent_app.command("context")
def agent_context(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    target: Annotated[
        AgentContextTarget,
        typer.Option(help="Context view to generate: neutral, codex, or claude."),
    ] = AgentContextTarget.NEUTRAL,
    apply_changes: Annotated[
        bool,
        typer.Option("--apply", help="Apply the displayed managed vendor-file plan."),
    ] = False,
) -> None:
    """Generate neutral context or preview/apply one managed vendor reference."""
    try:
        layout = discover_repository(directory)
        if target is AgentContextTarget.NEUTRAL:
            if apply_changes:
                raise ConfigurationError("--apply is only valid for codex or claude targets")
            result = generate_agent_context(layout, target=target)
            typer.echo(f"Generated {target.value} canonical agent context")
            typer.echo(f"JSON: {result.json_path}")
            typer.echo(f"Markdown: {result.markdown_path}")
            if result.context.known_blockers:
                typer.echo("Known blockers:")
                for blocker in result.context.known_blockers:
                    typer.echo(f"- {blocker}")
            typer.echo("Generated context is derived; FORGE governed state remains authoritative")
            return
        preview = preview_vendor_context(layout, target=target)
        typer.echo(f"Vendor target: {target.value}")
        typer.echo(f"Path: {preview.path}")
        typer.echo(f"Action: {preview.action.value}")
        typer.echo(f"Current digest: {preview.current_digest or '<missing>'}")
        typer.echo(f"Proposed digest: {preview.proposed_digest}")
        typer.echo(f"Neutral context digest: {preview.context_digest}")
        typer.echo("Managed block preview:")
        typer.echo(preview.managed_block.decode("utf-8"), nl=False)
        if not apply_changes:
            typer.echo("Preview only; rerun with --apply to confirm this vendor-file change")
            return
        applied = apply_vendor_context(
            layout,
            target=target,
            expected_current_digest=preview.current_digest,
            expected_context_digest=preview.context_digest,
        )
    except ForgeError as error:
        _fail(error)
        return
    outcome = "Updated" if applied.vendor_changed else "Already current"
    typer.echo(f"{outcome}: {applied.preview.path}")
    typer.echo(f"JSON: {applied.context.json_path}")
    typer.echo(f"Markdown: {applied.context.markdown_path}")
    typer.echo("Vendor reference is derived; FORGE governed state remains authoritative")


@agent_app.command("doctor")
def agent_doctor(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    adapter: Annotated[
        str | None,
        typer.Option("--adapter", help="Adapter ID; defaults to agents.preferred_adapter."),
    ] = None,
) -> None:
    """Inspect adapter selection and the safe manual fallback without mutation."""
    try:
        layout = discover_repository(directory)
        selection = inspect_agent_adapter(layout, requested_adapter_id=adapter)
    except ForgeError as error:
        _fail(error)
        return
    diagnostic = selection.diagnostic
    typer.echo(f"Requested adapter: {selection.requested_adapter_id}")
    requested_diagnostic = selection.requested_diagnostic
    if (
        requested_diagnostic is not None
        and requested_diagnostic.adapter_id != diagnostic.adapter_id
    ):
        requested_availability = (
            "available" if requested_diagnostic.availability.available else "unavailable"
        )
        typer.echo(f"Requested availability: {requested_availability}")
        typer.echo(f"Requested detail: {requested_diagnostic.availability.detail}")
        typer.echo(f"Requested version: {requested_diagnostic.detected_version or '<unknown>'}")
        typer.echo(
            f"Requested compatibility: {requested_diagnostic.compatibility.state.value}"
        )
        typer.echo(f"Requested authentication: {requested_diagnostic.authentication_state}")
    if selection.fallback_reason is not None:
        typer.echo(f"Fallback: {selection.fallback_reason}")
    typer.echo(f"Selected adapter: {diagnostic.adapter_id}")
    availability = "available" if diagnostic.availability.available else "unavailable"
    typer.echo(f"Availability: {availability}")
    typer.echo(f"Availability detail: {diagnostic.availability.detail}")
    typer.echo(f"Version: {diagnostic.detected_version or '<unknown>'}")
    typer.echo(f"Compatibility: {diagnostic.compatibility.state.value}")
    typer.echo(f"Compatibility detail: {diagnostic.compatibility.detail}")
    typer.echo(f"Authentication: {diagnostic.authentication_state}")
    process_start = "supported" if diagnostic.supports_process_start else "unsupported"
    cancellation = "supported" if diagnostic.supports_cancellation else "unsupported"
    output_capture = "supported" if diagnostic.supports_output_capture else "unsupported"
    typer.echo(f"Process start: {process_start}")
    typer.echo(f"Cancellation: {cancellation}")
    typer.echo(f"Output capture: {output_capture}")
    for limitation in diagnostic.limitations:
        typer.echo(f"Limitation: {limitation}")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def root(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = None,
) -> None:
    """Govern work without treating worker output as trusted project state."""


def _fail(error: ForgeError) -> None:
    typer.echo(f"Error: {error}", err=True)
    raise typer.Exit(code=int(error.exit_code))


def _assignment_map(values: list[str] | None, label: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for item in values or ():
        path, separator, value = item.partition("=")
        if not separator or not path.strip() or not value.strip():
            raise ConfigurationError(f"{label} must use TARGET=VALUE syntax: {item!r}")
        if path in assignments:
            raise ConfigurationError(f"Duplicate {label} assignment for {path!r}")
        assignments[path] = value
    return assignments


@agent_app.command("run")
@_locked_mutation
def agent_run(
    step_id: Annotated[str, typer.Argument(help="Ready workflow step ID.")],
    adapter: Annotated[
        str,
        typer.Option("--adapter", help="Explicit executable adapter: codex or claude."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    constraint: Annotated[
        list[str] | None,
        typer.Option("--constraint", help="Repeat for each bounded worker constraint."),
    ] = None,
    timeout_seconds: Annotated[
        float,
        typer.Option("--timeout", help="Bounded provider execution timeout in seconds."),
    ] = 300.0,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Execute one provider in a disposable workspace and stage its untrusted result."""
    layout = discover_repository(directory)
    result = execute_agent_run(
        layout,
        step_id=step_id,
        requested_adapter_id=adapter,
        constraints=tuple(constraint or ()),
        timeout_seconds=timeout_seconds,
    )
    typer.echo(f"Adapter run: {result.run_id}")
    typer.echo(f"Adapter: {result.selection.adapter.adapter_id}")
    typer.echo(f"Execution state: {result.state.value}")
    typer.echo(f"Exit code: {result.exit_code if result.exit_code is not None else '<none>'}")
    typer.echo(f"Local run directory: {result.run_directory}")
    if result.staged_result is not None:
        typer.echo(f"Staged result: {result.staged_result.result.id}")
        typer.echo(f"Manifest: {result.staged_result.manifest_path}")
        typer.echo("Review with forge import-result; no returned file was applied")
    else:
        typer.echo(f"Result unavailable: {result.detail}")


@app.command("init")
def initialize(
    directory: Annotated[
        Path,
        typer.Argument(help="Project repository to initialize."),
    ] = Path("."),
    owner_name: Annotated[
        str | None,
        typer.Option("--owner-name", help="Display name for the repository owner."),
    ] = None,
) -> None:
    """Initialize a repository without overwriting unrelated content."""
    if owner_name is None and not (directory / "forge.yaml").exists():
        owner_name = typer.prompt("Owner display name")
    try:
        result = initialize_repository(directory, owner_display_name=owner_name)
    except ForgeError as error:
        _fail(error)
        return
    action = "Initialized" if result.created else "Already initialized"
    typer.echo(f"{action} FORGE repository at {result.layout.root}")
    typer.echo(f"Project ID: {result.configuration.project_id}")
    typer.echo(f"Owner: {result.configuration.owner.display_name}")
    if result.gitignore_changed:
        typer.echo("Updated .gitignore with the FORGE hybrid Git policy")


@schema_app.command("export")
def export_schemas(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for generated JSON Schema files."),
    ] = Path("schemas"),
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace changed generated schema files."),
    ] = False,
) -> None:
    """Export deterministic JSON Schemas for every versioned contract."""
    try:
        paths = export_schema_bundle(output, overwrite=force)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Exported {len(paths) - 1} contract schemas to {output.resolve()}")


@config_app.command("validate")
def validate_config(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Validate the nearest project configuration without changing it."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(
        f"Valid FORGE configuration {configuration.schema_version} at "
        f"{layout.configuration_file}"
    )


@config_app.command("show")
def show_config(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Show the validated project configuration, which must contain no secrets."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(render_configuration(configuration).decode("utf-8"), nl=False)


@pack_app.command("list")
def list_packs(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """List safe-YAML packs after full conformance and digest validation."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        packs = available_packs(layout, configuration)
    except ForgeError as error:
        _fail(error)
        return
    for pack in packs:
        source = "bundled" if pack.bundled else "local"
        typer.echo(
            f"{pack.manifest.id} {pack.manifest.version} ({source}, untrusted until owner use)"
        )


@pack_app.command("validate")
def validate_pack_command(
    pack_id: Annotated[str, typer.Argument(help="Pack ID to validate.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Validate one pack as data without trusting or executing it."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        pack = find_pack(layout, configuration, pack_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(
        f"Valid data pack {pack.manifest.id} {pack.manifest.version} "
        f"({pack.manifest.integrity_digest})"
    )


@app.command("create")
@_locked_mutation
def create(
    objective: Annotated[str, typer.Argument(help="Initiative objective.")],
    scope: Annotated[str, typer.Option("--scope", help="Declared bounded scope summary.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    pack_id: Annotated[
        str,
        typer.Option("--pack", help="Validated data pack ID."),
    ] = "software-basic",
    workflow_id: Annotated[
        str | None,
        typer.Option("--workflow", help="Workflow ID within the selected pack."),
    ] = None,
    explanation: Annotated[
        ExplanationProfile | None,
        typer.Option(
            "--explanation",
            help="M1 presentation profile; governance outcomes remain identical.",
        ),
    ] = None,
    predecessor: Annotated[
        list[UUID] | None,
        typer.Option(
            "--predecessor",
            help="Archived predecessor UUID; repeat to create a multi-predecessor successor.",
        ),
    ] = None,
    trust_pack_data: Annotated[
        bool,
        typer.Option(
            "--trust-pack-data",
            help="Owner confirmation for this exact data pack; never authorizes execution.",
        ),
    ] = False,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Create one owner-authorized initiative and immutable workflow lock."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = create_initiative(
            layout,
            objective=objective,
            declared_scope_summary=scope,
            actor=owner_actor(configuration.owner),
            trust_pack_data=trust_pack_data,
            pack_id=pack_id,
            workflow_id=workflow_id,
            explanation_profile=explanation,
            predecessor_ids=tuple(predecessor or ()),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Created initiative {result.active.initiative.id}")
    for reference in result.active.initiative.predecessor_references:
        typer.echo(
            f"Predecessor: {reference.initiative_id} ({reference.archive_reference})"
        )
    typer.echo(
        f"Locked {result.active.pack_manifest.id} {result.active.pack_manifest.version} / "
        f"{result.active.workflow.id} {result.active.workflow.version}"
    )
    typer.echo(f"Next: {', '.join(result.active.state.permitted_next_actions)}")
    typer.echo(
        f"Guidance ({result.active.initiative.explanation_profile.value}): "
        f"{result.active.explanation}"
    )


@app.command("doctor")
def doctor(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to diagnose."),
    ] = Path("."),
) -> None:
    """Validate implemented boundaries without repairing or mutating them."""
    try:
        layout = discover_repository(directory)
        report = inspect_repository_health(layout)
    except ForgeError as error:
        _fail(error)
        return
    for check in report.checks:
        typer.echo(f"OK: {check}")
    for warning in report.warnings:
        typer.echo(f"Warning: {warning}")
    typer.echo("FORGE repository health: healthy")


@app.command("status")
def status(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
    archive_id: Annotated[
        UUID | None,
        typer.Option("--archive", help="Archived initiative ID to validate and inspect."),
    ] = None,
) -> None:
    """Validate and display current repository and initiative state."""
    try:
        layout = discover_repository(directory)
        report = inspect_status(layout, archive_id=archive_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Repository: {report.repository_state.value}")
    typer.echo(f"Integrity: {report.integrity_state.value}")
    if report.initiative is None:
        typer.echo("Initiative: none")
    else:
        typer.echo(f"Initiative: {report.initiative.id} — {report.initiative.objective}")
        typer.echo(f"Explanation profile: {report.initiative.explanation_profile.value}")
    for summary in report.archive_summaries:
        guarantee = "preliminary" if summary.preliminary else "hardened"
        typer.echo(
            f"Archived initiative: {summary.initiative_id} - "
            f"{summary.terminal_state.value} - {summary.objective} "
            f"({guarantee}, {summary.event_count} events)"
        )
    if report.state is not None:
        typer.echo(f"Lifecycle: {report.state.lifecycle_state}")
        for step_id, step_state in report.state.step_states.items():
            typer.echo(f"Step {step_id}: {step_state.value}")
        for run_id in report.state.active_run_ids:
            typer.echo(f"Active run: {run_id}")
        for gate_id in report.state.open_gate_ids:
            typer.echo(f"Open gate: {gate_id}")
        for decision_id in report.state.open_decision_ids:
            typer.echo(f"Open decision: {decision_id}")
        for record_id in report.state.stale_record_ids:
            typer.echo(f"Stale record: {record_id}")
    if report.archive_manifest is not None and (
        report.closure is not None or report.abandonment is not None
    ):
        terminal = report.closure or report.abandonment
        assert terminal is not None
        typer.echo(f"Archive: {terminal.archive_reference}")
        typer.echo(f"Archived at: {report.archive_manifest.created_at.isoformat()}")
        typer.echo(f"Archive digest: {report.archive_manifest.archive_digest}")
        typer.echo(f"Terminal record: {terminal.id}")
        if report.closure is not None:
            terminal_event_id = report.closure.closure_event_id
        else:
            assert report.abandonment is not None
            terminal_event_id = report.abandonment.abandonment_event_id
        typer.echo(f"Terminal event: {terminal_event_id}")
        typer.echo(
            "Terminal owner: "
            f"{terminal.owner_actor.display_label} ({terminal.owner_actor.id})"
        )
        typer.echo(f"Archive files: {len(report.archive_manifest.files)}")
        typer.echo(f"Preserved objects: {len(report.archive_manifest.object_references)}")
        typer.echo(
            "Accepted preserved objects: "
            f"{sum(item.accepted for item in report.archive_manifest.object_references)}"
        )
        if report.state is not None:
            typer.echo(f"Journal events: {report.state.journal_head_sequence}")
            typer.echo(f"Journal head hash: {report.state.journal_head_hash or 'legacy-unhashed'}")
        assert report.initiative is not None
        typer.echo(f"Declared scope: {report.initiative.declared_scope_summary}")
        if report.initiative.predecessor_references:
            for predecessor in report.initiative.predecessor_references:
                typer.echo(
                    f"Predecessor: {predecessor.initiative_id} "
                    f"({predecessor.archive_reference})"
                )
        else:
            typer.echo("Predecessors: none")
        if report.closure is not None:
            typer.echo(f"Closing summary: {report.closure.closing_summary}")
            typer.echo(f"Final acceptances: {len(report.closure.final_acceptance_ids)}")
            typer.echo(
                "Accepted artifact revisions: "
                f"{len(report.closure.accepted_artifact_revision_ids)}"
            )
        else:
            assert report.abandonment is not None
            typer.echo(f"Abandonment reason: {report.abandonment.reason}")
            typer.echo(
                f"Unfinished work: {report.abandonment.unfinished_work_summary}"
            )
            for risk in report.abandonment.unresolved_risks:
                typer.echo(f"Unresolved risk: {risk}")
            for step_id in report.abandonment.unfinished_step_ids:
                typer.echo(f"Unfinished step: {step_id}")
        if report.archive_manifest.preliminary:
            guarantee = "preliminary M1 command-level immutability"
        else:
            guarantee = (
                f"atomic M2 {report.archive_manifest.terminal_state.value} "
                "with resumable archival"
            )
        typer.echo(f"Archive guarantee: {guarantee}")
        for limitation in report.archive_manifest.limitations:
            typer.echo(f"Archive limitation: {limitation}")
    for action in report.next_actions:
        typer.echo(f"Next: {action}")
    for blocker in report.blockers:
        typer.echo(f"Blocker: {blocker}")


@app.command("migrate")
@_locked_mutation
def migrate(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    apply_changes: Annotated[
        bool,
        typer.Option(
            "--apply",
            help="Apply the displayed registered migration; omission is read-only preview.",
        ),
    ] = False,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Preview or explicitly apply the next registered active-state migration."""
    try:
        layout = discover_repository(directory)
        if not apply_changes:
            inspection = inspect_active_migration(layout)
            typer.echo(f"Initiative: {inspection.initiative_id}")
            typer.echo(f"Current format: {inspection.plan.current_format}")
            typer.echo(f"Target format: {inspection.plan.target_format}")
            typer.echo(f"Journal events: {inspection.plan.event_count}")
            if inspection.plan.definition is None:
                typer.echo("Migration required: no")
            else:
                typer.echo("Migration required: yes")
                typer.echo(f"Migration: {inspection.plan.definition.id}")
                typer.echo("Apply with: forge migrate --apply --idempotency-key <key>")
            return
        configuration = load_configuration(layout.configuration_file)
        result = migrate_active_repository(
            layout,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    action = "Resumed" if result.resumed else "Completed"
    typer.echo(f"{action} migration {result.record.migration_id}")
    typer.echo(f"Migration record: {result.record.id}")
    typer.echo(f"Migration event: {result.event.id}")
    typer.echo(f"Preserved source: {result.record.preserved_source_path}")
    typer.echo(f"Preserved digest: {result.record.preserved_source_digest}")
    typer.echo(f"Journal head hash: {result.state.journal_head_hash}")
    typer.echo("Integrity: healthy")


@app.command("recover")
@_locked_mutation
def recover(
    reason: Annotated[
        str,
        typer.Option("--reason", help="Owner reason for explicit governed-state recovery."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Explicitly recover a snapshot or unambiguously truncated final journal record."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = recover_active_snapshot(
            layout,
            actor=owner_actor(configuration.owner),
            reason=reason,
        )
    except ForgeError as error:
        _fail(error)
        return
    action = "Resumed" if result.resumed else "Completed"
    typer.echo(f"{action} recovery {result.record.id}")
    typer.echo(f"Recovery event: {result.event.id}")
    if isinstance(result.record, JournalRecoveryRecord):
        typer.echo(f"Preserved journal: {result.record.preserved_journal_path}")
        typer.echo(f"Truncated tail bytes: {result.record.truncated_tail_size}")
    if result.record.preserved_snapshot_path is not None:
        typer.echo(f"Preserved snapshot: {result.record.preserved_snapshot_path}")
    else:
        typer.echo("Preserved snapshot: none (state.json was missing)")
    typer.echo("Integrity: healthy")


@app.command("recover-command")
@_locked_mutation
def recover_command(
    interrupted_key: Annotated[
        str,
        typer.Argument(help="Idempotency key whose committed command lacks a receipt."),
    ],
    reason: Annotated[
        str,
        typer.Option("--reason", help="Owner reason for explicit command receipt recovery."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Recover a missing receipt for one provably complete active command."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = recover_command_receipt(
            layout,
            actor=owner_actor(configuration.owner),
            interrupted_key=interrupted_key,
            reason=reason,
        )
    except ForgeError as error:
        _fail(error)
        return
    action = "Resumed" if result.resumed else "Completed"
    typer.echo(f"{action} command receipt recovery {result.record.id}")
    typer.echo(f"Interrupted key: {result.record.interrupted_key}")
    typer.echo(f"Interrupted command: {result.record.interrupted_command}")
    typer.echo(f"Recovered event(s): {len(result.receipt.events)}")
    typer.echo(f"Recovery event: {result.event.id}")
    typer.echo("Integrity: healthy")


@app.command("remediate-lock")
def remediate_lock(
    reason: Annotated[
        str,
        typer.Option("--reason", help="Owner reason for removing a definitively stale lock."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Preserve and remove one same-host mutation lock whose owner is dead."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        key = normalize_idempotency_key(idempotency_key)
        typer.echo(f"Idempotency key: {key}")
        result = remediate_stale_lock(
            layout,
            project_id=configuration.project_id,
            owner_identity_id=configuration.owner.id,
            actor=owner_actor(configuration.owner),
            reason=reason,
            idempotency_key=key,
        )
    except ForgeError as error:
        _fail(error)
        return
    if result.replayed:
        action = "Idempotent replay of"
    elif result.resumed:
        action = "Resumed"
    else:
        action = "Completed"
    typer.echo(f"{action} stale-lock remediation {result.record.id}")
    typer.echo(
        f"Removed owner: pid={result.record.source_owner_pid} "
        f"host={result.record.source_owner_hostname} "
        f"command={result.record.source_owner_command!r}"
    )
    typer.echo(f"Preserved lock: {result.record.preserved_lock_path}")
    typer.echo("Governed initiative state: unchanged")


@app.command("pause")
@_locked_mutation
def pause(
    reason: Annotated[
        str,
        typer.Option("--reason", help="Owner reason for pausing governed work."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Pause active work at a safe governed boundary."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = pause_initiative(
            layout,
            actor=owner_actor(configuration.owner),
            reason=reason,
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Paused initiative {result.state.initiative_id}")
    typer.echo(f"Pause event: {result.event.id}")
    typer.echo("Next: resume")


@app.command("resume")
@_locked_mutation
def resume(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Resume a healthy paused initiative with durable context."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = resume_initiative(
            layout,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Resumed initiative {result.state.initiative_id}")
    typer.echo(f"Resume event: {result.event.id}")
    typer.echo(f"Summary: {result.summary}")
    for action in result.state.permitted_next_actions:
        typer.echo(f"Next: {action}")


@app.command("history")
def history(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
    archive_id: Annotated[
        UUID | None,
        typer.Option("--archive", help="Archived initiative ID to inspect."),
    ] = None,
    event_type: Annotated[
        str | None,
        typer.Option("--event-type", help="Exact event type filter."),
    ] = None,
    step_id: Annotated[
        str | None,
        typer.Option("--step", help="Exact workflow step filter."),
    ] = None,
    actor: Annotated[
        str | None,
        typer.Option("--actor", help="Actor ID, type, or display-label filter."),
    ] = None,
    run_id: Annotated[
        UUID | None,
        typer.Option("--run", help="Exact governed run ID filter."),
    ] = None,
) -> None:
    """Display validated active or archived event history without mutation."""
    try:
        layout = discover_repository(directory)
        report = inspect_history_report(
            layout,
            archive_id=archive_id,
            event_type=event_type,
            step_id=step_id,
            actor=actor,
            run_id=run_id,
        )
    except ForgeError as error:
        _fail(error)
        return
    source = (
        f"archive {report.initiative_id}"
        if report.archive_manifest is not None
        else f"active initiative {report.initiative_id}"
    )
    typer.echo(f"History source: {source}")
    typer.echo(f"Lifecycle: {report.lifecycle_state.value}")
    typer.echo("Integrity: healthy")
    typer.echo(f"Events: {len(report.events)} of {report.total_event_count}")
    typer.echo(f"Journal head sequence: {report.journal_head_sequence}")
    typer.echo(f"Journal head hash: {report.journal_head_hash or 'legacy-unhashed'}")
    if report.archive_manifest is not None:
        typer.echo(f"Archive digest: {report.archive_manifest.archive_digest}")
    if not report.events:
        typer.echo("No matching events")
        return
    for event in report.events:
        if event.event_hash is None:
            previous_hash = "legacy-unhashed"
        else:
            previous_hash = event.previous_event_hash or "chain-root"
        details = [
            f"{event.sequence}",
            event.timestamp.isoformat(),
            event.event_type,
            f"actor={event.actor.actor_type.value}:{event.actor.id}",
            f"id={event.id}",
            f"hash={event.event_hash or 'legacy-unhashed'}",
            f"previous={previous_hash}",
        ]
        step = event.metadata.get("step_id")
        if isinstance(step, str):
            details.append(f"step={step}")
        if event.run_id is not None:
            details.append(f"run={event.run_id}")
        typer.echo(" ".join(details))


@app.command("close")
@_locked_mutation
def close(
    summary: Annotated[
        str,
        typer.Option("--summary", help="Final owner closure decision and summary."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Close fully accepted work into an interruption-recoverable archive."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = close_initiative(
            layout,
            closing_summary=summary,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Closed initiative {result.closure.initiative_id}")
    typer.echo(f"Closure record: {result.closure.id}")
    typer.echo(f"Archive: {result.closure.archive_reference}")
    typer.echo(f"Archive digest: {result.archive.manifest.archive_digest}")
    typer.echo("Atomic M2 archive created; closure retry is interruption-safe")


@app.command("abandon")
@_locked_mutation
def abandon(
    reason: Annotated[
        str,
        typer.Option("--reason", help="Owner reason for abandoning the initiative."),
    ],
    unfinished_work: Annotated[
        str,
        typer.Option(
            "--unfinished-work",
            help="Summary of work that remains unfinished.",
        ),
    ],
    risk: Annotated[
        list[str],
        typer.Option(
            "--risk",
            help="Repeat for each unresolved risk; state 'None known' when appropriate.",
        ),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Abandon unfinished work into a distinct interruption-recoverable archive."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = abandon_initiative(
            layout,
            reason=reason,
            unfinished_work_summary=unfinished_work,
            unresolved_risks=tuple(risk),
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Abandoned initiative {result.abandonment.initiative_id}")
    typer.echo(f"Abandonment record: {result.abandonment.id}")
    typer.echo(f"Archive: {result.abandonment.archive_reference}")
    typer.echo(f"Archive digest: {result.archive.manifest.archive_digest}")
    typer.echo("Atomic M2 abandonment archive created; retry is interruption-safe")


@app.command("next")
def next_actions(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Display legal next actions and blockers without mutation."""
    try:
        layout = discover_repository(directory)
        report = inspect_status(layout)
    except ForgeError as error:
        _fail(error)
        return
    if report.next_actions:
        for action in report.next_actions:
            typer.echo(action)
    else:
        typer.echo("No legal next actions")
    for blocker in report.blockers:
        typer.echo(f"Blocker: {blocker}")


@app.command("begin")
@_locked_mutation
def begin(
    step_id: Annotated[str, typer.Argument(help="Ready workflow step ID.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    side_effect_class: Annotated[
        SideEffectClass,
        typer.Option("--side-effect", help="Declared side-effect class for this manual run."),
    ] = SideEffectClass.REPOSITORY_WRITE,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Begin an eligible manual step without claiming completion."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = begin_manual_run(
            layout,
            step_id=step_id,
            actor=owner_actor(configuration.owner),
            side_effect_class=side_effect_class,
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Started manual run {result.run.id} for step {step_id}")
    typer.echo("Run success will remain separate from checks, evidence, and owner acceptance")


@run_app.command("list")
def run_list(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """List durable run attempts with effective event-derived status."""
    try:
        layout = discover_repository(directory)
        runs = list_runs(layout)
    except ForgeError as error:
        _fail(error)
        return
    if not runs:
        typer.echo("No runs")
    for run in runs:
        typer.echo(f"{run.record.id} step={run.record.step_id} status={run.status.value}")


@run_app.command("show")
def run_show(
    run_id: Annotated[UUID, typer.Argument(help="Durable run UUID.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show immutable run metadata and its event-derived terminal state."""
    try:
        layout = discover_repository(directory)
        run = show_run(layout, run_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Run: {run.record.id}")
    typer.echo(f"Step: {run.record.step_id}")
    typer.echo(f"Status: {run.status.value}")
    typer.echo(f"Worker: {run.record.worker.actor_type.value}:{run.record.worker.id}")
    typer.echo(f"Side effects: {run.record.side_effect_class.value}")
    typer.echo(f"Input context: {run.record.input_context_digest}")
    if run.cancellation_details is not None:
        typer.echo(f"Cancellation: {run.cancellation_details}")


@run_app.command("cancel")
@_locked_mutation
def run_cancel(
    run_id: Annotated[UUID, typer.Argument(help="Active run UUID.")],
    reason: Annotated[str, typer.Option("--reason", help="Explicit cancellation reason.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Cancel active work without implying completion or acceptance."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = cancel_run(
            layout,
            run_id=run_id,
            reason=reason,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    destination = result.state.step_states[result.run.record.step_id]
    typer.echo(f"Cancelled run {run_id}")
    typer.echo(f"Step {result.run.record.step_id}: {destination.value}")
    typer.echo("Cancellation is terminal for the run and never implies step success")


@app.command("handoff")
def handoff(
    step_id: Annotated[str, typer.Argument(help="Eligible workflow step ID.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    constraint: Annotated[
        list[str] | None,
        typer.Option("--constraint", help="Repeat for each bounded worker constraint."),
    ] = None,
) -> None:
    """Generate portable neutral Markdown, JSON, and return-schema files."""
    try:
        layout = discover_repository(directory)
        prepared = prepare_agent_handoff(
            layout,
            step_id=step_id,
            constraints=tuple(constraint or ()),
            requested_adapter_id="manual",
        )
    except ForgeError as error:
        _fail(error)
        return
    result = prepared.handoff
    typer.echo(f"Adapter: {prepared.selection.adapter.adapter_id}")
    typer.echo(f"Context digest: {prepared.plan.context_digest}")
    typer.echo(f"Created handoff {result.handoff.id}")
    typer.echo(f"Directory: {result.directory}")
    typer.echo("Worker output remains untrusted and must use forge import-result")


@app.command("import-result")
@_locked_mutation
def import_result(
    manifest: Annotated[Path, typer.Argument(help="AgentResult JSON manifest path.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    apply_changes: Annotated[
        bool,
        typer.Option("--apply", help="Apply the displayed registration plan atomically."),
    ] = False,
    role: Annotated[
        list[str] | None,
        typer.Option("--role", help="TARGET=ROLE for each new artifact target."),
    ] = None,
    collision: Annotated[
        list[str] | None,
        typer.Option(
            "--collision",
            help="TARGET=revise for governed targets or TARGET=replace otherwise.",
        ),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Stage and preview an untrusted result; apply only with explicit actions."""
    try:
        layout = discover_repository(directory)
        roles = _assignment_map(role, "Role assignment")
        collisions = _assignment_map(collision, "Collision assignment")
        if apply_changes:
            configuration = load_configuration(layout.configuration_file)
            imported = apply_result_import(
                layout,
                manifest_path=manifest,
                actor=owner_actor(configuration.owner),
                role_assignments=roles,
                collision_actions=collisions,
            )
            preview = imported.preview
        else:
            imported = None
            preview = preview_result_import(
                layout,
                manifest_path=manifest,
                role_assignments=roles,
                collision_actions=collisions,
            )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Staged result: {preview.staged.result.id}")
    typer.echo(f"Source step: {preview.step_id}")
    for action in preview.actions:
        typer.echo(
            f"Action: {action.action} {action.target_path} role={action.role or 'required'} "
            f"digest={action.digest}"
        )
        for blocker in action.blockers:
            typer.echo(f"Blocker: {blocker}")
    if imported is None:
        typer.echo("Preview only; rerun with --apply after resolving every blocker")
    else:
        typer.echo(f"Imported event: {imported.event.id}")
        typer.echo(
            "Imported worker content remains subject to claims, checks, evidence, and acceptance"
        )


@artifact_app.command("add")
@_locked_mutation
def artifact_add(
    path: Annotated[str, typer.Argument(help="Repository-relative project file path.")],
    role: Annotated[str, typer.Option("--role", help="Declared workflow artifact role.")],
    title: Annotated[str, typer.Option("--title", help="Human-readable artifact title.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    media_type: Annotated[
        str,
        typer.Option("--media-type", help="Stable media type for this exact revision."),
    ] = "application/octet-stream",
    predecessor_revision: Annotated[
        UUID | None,
        typer.Option(
            "--predecessor-revision",
            help="Terminal artifact revision UUID from a declared predecessor.",
        ),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Register a logical artifact and preserve its exact first revision."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = add_artifact(
            layout,
            path=path,
            role=role,
            title=title,
            actor=owner_actor(configuration.owner),
            media_type=media_type,
            predecessor_revision_id=predecessor_revision,
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Registered artifact {result.artifact.id} revision 1")
    typer.echo(f"Revision ID: {result.revision.id}")
    typer.echo(f"Digest: {result.revision.content_digest}")
    typer.echo(f"Preserved: {result.revision.preserved_object_path}")


@artifact_app.command("revise")
@_locked_mutation
def artifact_revise(
    artifact_id: Annotated[UUID, typer.Argument(help="Logical artifact UUID.")],
    path: Annotated[str, typer.Argument(help="Repository-relative file for the new revision.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    media_type: Annotated[
        str | None,
        typer.Option("--media-type", help="Media type, or inherit the prior revision."),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Register and preserve a new immutable artifact revision."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = revise_artifact(
            layout,
            artifact_id=artifact_id,
            path=path,
            actor=owner_actor(configuration.owner),
            media_type=media_type,
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(
        f"Registered artifact {result.artifact.id} revision {result.revision.revision_number}"
    )
    typer.echo(f"Revision ID: {result.revision.id}")
    typer.echo(f"Digest: {result.revision.content_digest}")
    typer.echo(
        f"Stale dependency effects: {len(result.revision.stale_dependency_effects)}"
    )


@artifact_app.command("list")
def artifact_list(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """List current artifact revisions and working-copy drift."""
    try:
        layout = discover_repository(directory)
        views = list_artifacts(layout)
    except ForgeError as error:
        _fail(error)
        return
    if not views:
        typer.echo("No registered artifacts")
        return
    for view in views:
        match = "current" if view.working_copy_matches else "working-copy-changed"
        typer.echo(
            f"{view.artifact.id} {view.artifact.role} r{view.current_revision.revision_number} "
            f"{view.current_revision.path} {match}"
        )


@artifact_app.command("show")
def artifact_show(
    artifact_id: Annotated[UUID, typer.Argument(help="Logical artifact UUID.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show every immutable revision of one artifact."""
    try:
        layout = discover_repository(directory)
        view = show_artifact(layout, artifact_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Artifact: {view.artifact.id}")
    typer.echo(f"Role: {view.artifact.role}")
    typer.echo(f"Title: {view.artifact.title}")
    for revision in view.revisions:
        typer.echo(
            f"Revision {revision.revision_number} ({revision.id}): {revision.path} "
            f"{revision.content_digest} "
            f"{revision.byte_size} bytes preserved={revision.preserved_object_path}"
        )
        for dependent_id in dependency_references(layout, revision.id):
            typer.echo(f"  Dependency reference: {dependent_id}")
        for stale_id in revision.stale_dependency_effects:
            typer.echo(f"  Stale dependency: {stale_id}")
    typer.echo(f"Working copy matches: {str(view.working_copy_matches).lower()}")


@app.command("complete")
@_locked_mutation
def complete(
    step_id: Annotated[str, typer.Argument(help="In-progress workflow step ID.")],
    assertion: Annotated[
        str,
        typer.Option("--assertion", help="Worker assertion about the declared outputs."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    run_id: Annotated[
        UUID | None,
        typer.Option(
            "--run-id",
            help="Attribute the claim to this governed run's recorded worker.",
        ),
    ] = None,
    limitation: Annotated[
        list[str] | None,
        typer.Option("--limitation", help="Repeat for each known claim limitation."),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Record a worker claim and submit current declared outputs for checking."""
    try:
        layout = discover_repository(directory)
        if run_id is None:
            configuration = load_configuration(layout.configuration_file)
            actor = owner_actor(configuration.owner)
        else:
            run = show_run(layout, run_id)
            if run.record.step_id != step_id:
                raise ConfigurationError(
                    f"Run {run_id} belongs to step {run.record.step_id}, not {step_id}"
                )
            actor = run.record.worker
        result = complete_step(
            layout,
            step_id=step_id,
            assertion=assertion,
            actor=actor,
            limitations=tuple(limitation or ()),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded claim {result.claim.id}")
    typer.echo(f"Claim actor: {result.claim.actor.display_label}")
    typer.echo(f"Step {step_id}: {result.transition.state.step_states[step_id].value}")
    typer.echo("The claim is not a check, evidence packet, or owner acceptance")


@check_app.command("record")
@_locked_mutation
def check_record(
    step_id: Annotated[str, typer.Argument(help="Step awaiting verification.")],
    check_id: Annotated[str, typer.Argument(help="Declared check identity.")],
    invocation: Annotated[
        str,
        typer.Option("--invocation", help="Exact manual invocation or evaluation description."),
    ],
    outcome: Annotated[CheckOutcome, typer.Option("--outcome", help="Normalized outcome.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    check_version: Annotated[
        str,
        typer.Option("--check-version", help="Version of the declared check."),
    ] = "1",
    exit_status: Annotated[
        int | None,
        typer.Option("--exit-status", help="Observed process exit status, when applicable."),
    ] = None,
    limitation: Annotated[
        list[str] | None,
        typer.Option("--limitation", help="Repeat for each check limitation."),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Record a manual check without executing or trusting a capability."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = record_check(
            layout,
            step_id=step_id,
            check_id=check_id,
            check_version=check_version,
            invocation_metadata={"invocation": invocation, "mode": "manual-record"},
            outcome=outcome,
            actor=owner_actor(configuration.owner),
            exit_status=exit_status,
            limitations=tuple(limitation or ()),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded check result {result.check.id}: {result.check.outcome.value}")
    typer.echo(f"Result digest: {result.check.result_digest}")
    typer.echo("A passing check is not owner acceptance")


@check_app.command("list")
def check_list(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """List structured check results."""
    try:
        layout = discover_repository(directory)
        checks = list_checks(layout)
    except ForgeError as error:
        _fail(error)
        return
    if not checks:
        typer.echo("No check results")
    for result in checks:
        typer.echo(f"{result.id} {result.check_id} {result.outcome.value}")


@evidence_app.command("add")
@_locked_mutation
def evidence_add(
    step_id: Annotated[str, typer.Argument(help="Step awaiting verification.")],
    purpose: Annotated[str, typer.Option("--purpose", help="Evidence purpose and scope.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    artifact_revision: Annotated[
        list[UUID] | None,
        typer.Option("--artifact-revision", help="Repeat for each exact artifact revision."),
    ] = None,
    check_result: Annotated[
        list[UUID] | None,
        typer.Option("--check-result", help="Repeat for each structured check result."),
    ] = None,
    claim: Annotated[
        list[UUID] | None,
        typer.Option("--claim", help="Repeat for each worker claim."),
    ] = None,
    limitation: Annotated[
        list[str] | None,
        typer.Option("--limitation", help="Repeat for each evidence limitation."),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Register digest-bound evidence references and explicit limitations."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = record_evidence(
            layout,
            step_id=step_id,
            purpose=purpose,
            actor=owner_actor(configuration.owner),
            artifact_revision_ids=tuple(artifact_revision or ()),
            check_result_ids=tuple(check_result or ()),
            claim_ids=tuple(claim or ()),
            limitations=tuple(limitation or ()),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Registered evidence packet {result.evidence.id}")
    typer.echo(f"Packet digest: {result.evidence.packet_digest}")
    typer.echo("Evidence documents support; it does not automatically establish truth")


@evidence_app.command("list")
def evidence_list(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """List evidence packets and their explicit scope."""
    try:
        layout = discover_repository(directory)
        packets = list_evidence(layout)
    except ForgeError as error:
        _fail(error)
        return
    if not packets:
        typer.echo("No evidence packets")
    for packet in packets:
        typer.echo(f"{packet.id} {packet.purpose}")


@evidence_app.command("show")
def evidence_show(
    evidence_id: Annotated[UUID, typer.Argument(help="Evidence packet UUID.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show evidence scope, references, digest, and limitations."""
    try:
        layout = discover_repository(directory)
        packet = show_evidence(layout, evidence_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Evidence: {packet.id}")
    typer.echo(f"Purpose: {packet.purpose}")
    typer.echo(f"Digest: {packet.packet_digest}")
    for revision_id in packet.artifact_revision_ids:
        typer.echo(f"Artifact revision: {revision_id}")
    for result_id in packet.check_result_ids:
        typer.echo(f"Check result: {result_id}")
    for claim_id in packet.claim_ids:
        typer.echo(f"Claim: {claim_id}")
    for item in packet.limitations:
        typer.echo(f"Limitation: {item}")


@app.command("verify")
@_locked_mutation
def verify(
    step_id: Annotated[str, typer.Argument(help="Step awaiting verification.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Derive check/evidence conditions and advance only when both are current."""
    try:
        layout = discover_repository(directory)
        result = verify_step(layout, step_id=step_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Step {step_id}: {result.state.step_states[step_id].value}")
    typer.echo(f"Next: forge acceptance record {step_id} --scope <accepted-scope>")


@acceptance_app.command("record")
@_locked_mutation
def acceptance_record(
    step_id: Annotated[str, typer.Argument(help="Step awaiting owner acceptance.")],
    accepted_scope: Annotated[
        str,
        typer.Option("--scope", help="Exact scope the owner accepts."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    known_limitation: Annotated[
        list[str] | None,
        typer.Option("--known-limitation", help="Repeat for each accepted limitation."),
    ] = None,
    residual_risk: Annotated[
        list[str] | None,
        typer.Option("--residual-risk", help="Repeat for each residual risk."),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Record owner-only acceptance bound to exact current evidence."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = record_acceptance(
            layout,
            step_id=step_id,
            accepted_scope=accepted_scope,
            actor=owner_actor(configuration.owner),
            known_limitations=tuple(known_limitation or ()),
            residual_risks=tuple(residual_risk or ()),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded owner acceptance {result.acceptance.id}")
    typer.echo(f"Step {step_id}: {result.transition.state.step_states[step_id].value}")


@acceptance_app.command("revoke")
@_locked_mutation
def acceptance_revoke(
    acceptance_id: Annotated[UUID, typer.Argument(help="Acceptance UUID to revoke.")],
    reason: Annotated[str, typer.Option("--reason", help="Explicit revocation reason.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Revoke acceptance and invalidate its dependent progression."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = revoke_acceptance(
            layout,
            acceptance_id=acceptance_id,
            reason=reason,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Revoked acceptance {acceptance_id} with record {result.revocation.id}")


@acceptance_app.command("show")
def acceptance_show(
    acceptance_id: Annotated[
        UUID | None,
        typer.Argument(help="Acceptance UUID; omit to show complete history."),
    ] = None,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show one acceptance or the complete append-only history."""
    try:
        layout = discover_repository(directory)
        views = (
            (show_acceptance(layout, acceptance_id),)
            if acceptance_id is not None
            else list_acceptances(layout)
        )
    except ForgeError as error:
        _fail(error)
        return
    if not views:
        typer.echo("No acceptance records")
    for view in views:
        status_label = "revoked" if view.revocation else "stale" if view.stale else "current"
        typer.echo(
            f"{view.acceptance.id} step={view.step_id} status={status_label} "
            f"scope={view.acceptance.accepted_scope}"
        )
        if view.revocation is not None:
            typer.echo(f"  Revocation: {view.revocation.id} {view.revocation.reason}")


@app.command("decide")
@_locked_mutation
def decide(
    decision_type: Annotated[str, typer.Option("--type", help="Stable decision type.")],
    question: Annotated[str, typer.Option("--question", help="Question being decided.")],
    option: Annotated[
        list[str],
        typer.Option("--option", help="Repeat for each considered option."),
    ],
    outcome: Annotated[str, typer.Option("--outcome", help="Chosen outcome.")],
    rationale: Annotated[str, typer.Option("--rationale", help="Owner rationale.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    affected_record: Annotated[
        list[UUID] | None,
        typer.Option("--affected-record", help="Repeat for each affected governed record."),
    ] = None,
    bound_digest: Annotated[
        list[str] | None,
        typer.Option("--bound-digest", help="Repeat for each sha256-bound fact."),
    ] = None,
    supersedes: Annotated[
        UUID | None,
        typer.Option("--supersedes", help="Active decision UUID replaced by this decision."),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Record an owner decision, optionally superseding an active decision."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = record_decision(
            layout,
            decision_type=decision_type,
            question=question,
            considered_options=tuple(option),
            chosen_outcome=outcome,
            rationale=rationale,
            actor=owner_actor(configuration.owner),
            affected_record_ids=tuple(affected_record or ()),
            bound_digests=tuple(bound_digest or ()),
            supersedes=supersedes,
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded decision {result.decision.id}")
    if result.supersession is not None:
        typer.echo(f"Supersession: {result.supersession.id}")


def main() -> None:
    """Invoke the Typer application."""
    app()
