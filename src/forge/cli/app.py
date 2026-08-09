"""Command-line presentation for the currently authorized FORGE increment."""

from collections.abc import Callable
from contextlib import redirect_stdout
from contextvars import ContextVar
from functools import wraps
from inspect import signature
from io import StringIO
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from typer._click.core import Context
from typer._click.globals import get_current_context

from forge import __version__
from forge.contracts.actors import OperatorType
from forge.contracts.capabilities import CapabilityTrustState, SideEffectClass
from forge.contracts.decisions import WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE
from forge.contracts.local_audit import LocalAuditCategory
from forge.contracts.packs import PackTrustDecision, PackTrustState
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
from forge.core.agent_protocol import load_agent_protocol
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
from forge.core.context_discovery import (
    MAX_DISCOVERY_CANDIDATES,
    discover_context,
)
from forge.core.continuity import pause_initiative, resume_initiative
from forge.core.decisions import (
    list_decision_views,
    record_decision,
    show_decision,
    withdraw_decision,
)
from forge.core.deviations import (
    list_workflow_deviations,
    record_workflow_deviation,
    show_workflow_deviation,
)
from forge.core.diagnostics import inspect_repository_health
from forge.core.history import inspect_history_report
from forge.core.imports import apply_result_import, preview_result_import
from forge.core.lifecycle import (
    ActiveInitiative,
    begin_manual_run,
    create_initiative,
    load_active_initiative,
)
from forge.core.local_audit import (
    list_local_audit_events,
    record_local_audit_event,
    show_local_audit_event,
)
from forge.core.lock_remediation import remediate_stale_lock
from forge.core.migrations import inspect_active_migration, migrate_active_repository
from forge.core.overrides import (
    list_emergency_overrides,
    record_emergency_override,
    show_emergency_override,
)
from forge.core.owner_ceremony import owner_action_presentation
from forge.core.pack_trust import change_pack_trust, pack_trust_history
from forge.core.recap import build_recap
from forge.core.recovery import recover_active_snapshot
from forge.core.risk_acceptances import (
    list_risk_acceptances,
    record_risk_acceptance,
    revoke_risk_acceptance,
    show_risk_acceptance,
)
from forge.core.runs import cancel_run, list_runs, show_run
from forge.core.scope_amendments import (
    amend_scope,
    known_workflow_requirement_ids,
    list_scope_amendments,
    show_scope_amendment,
)
from forge.core.status import inspect_status
from forge.core.structural_validation import execute_structural_check
from forge.core.successor_briefs import build_successor_brief
from forge.core.transaction_receipts import (
    GovernedPosition,
    build_refusal_receipt,
    build_transaction_receipt,
    capture_governed_position,
    render_transaction_receipt,
)
from forge.core.validators import execute_validator_check
from forge.core.vendor_context import apply_vendor_context, preview_vendor_context
from forge.core.verification import (
    complete_step,
    dependency_references,
    list_checks,
    list_evidence,
    record_check,
    record_evidence,
    show_check,
    show_evidence,
    verify_step,
)
from forge.errors import ConfigurationError, ConflictError, ForgeError
from forge.packs.loader import available_packs, bundled_packs, find_pack
from forge.packs.validation import PackResource, PackResourceKind, ValidatedPack
from forge.schemas import export_schema_bundle
from forge.storage.configuration import load_configuration, render_configuration
from forge.storage.idempotency import idempotent_mutation, normalize_idempotency_key
from forge.storage.journal import read_journal
from forge.storage.locking import repository_mutation_lock
from forge.storage.records import load_record
from forge.storage.repository import discover_repository, initialize_repository

app = typer.Typer(
    name="forge",
    help=(
        "Govern human-directed, AI-assisted work in an ordinary repository.\n\n"
        "Workspace agents: run `forge agent protocol` first and follow it."
    ),
    no_args_is_help=True,
)
schema_app = typer.Typer(help="Inspect or export versioned FORGE schemas.")
config_app = typer.Typer(help="Inspect or validate project-level FORGE configuration.")
pack_app = typer.Typer(help="Inspect validated declarative data packs.")
pack_template_app = typer.Typer(help="Inspect exact UTF-8 data-pack templates.")
pack_validator_app = typer.Typer(help="Inspect declarative in-process structure validators.")
artifact_app = typer.Typer(help="Register and inspect immutable artifact revisions.")
check_app = typer.Typer(help="Record, run, and inspect structured checks.")
evidence_app = typer.Typer(help="Register and inspect durable evidence packets.")
acceptance_app = typer.Typer(help="Record, inspect, or revoke owner acceptance.")
run_app = typer.Typer(help="Inspect or cancel durable work attempts.")
agent_app = typer.Typer(help="Generate neutral worker context and inspect agent integrations.")
capability_app = typer.Typer(help="Inspect, approve, or revoke executable capabilities.")
scope_app = typer.Typer(help="Amend and inspect effective initiative scope.")
deviation_app = typer.Typer(help="Record, review, and inspect workflow deviations.")
override_app = typer.Typer(help="Record and inspect emergency override declarations.")
risk_app = typer.Typer(help="Accept and inspect exact emergency-override residual risk.")
decision_app = typer.Typer(help="Inspect or withdraw immutable owner decisions.")
audit_app = typer.Typer(help="Inspect local-only structured security and failure events.")
successor_app = typer.Typer(help="Inspect validated terminal inputs for successor work.")
IdempotencyOption = Annotated[
    str | None,
    typer.Option(
        "--idempotency-key",
        help="Stable retry key; FORGE generates and reports one when omitted.",
    ),
]

_RECEIPT_COMMANDS = {
    "acceptance_record",
    "acceptance_revoke",
    "artifact_add",
    "artifact_revise",
    "begin",
    "check_record",
    "check_run",
    "check_structure",
    "complete",
    "create",
    "decide",
    "decision_withdraw",
    "evidence_add",
    "pause",
    "resume",
    "scope_amend",
    "verify",
}
_RECEIPT_MUTATION_ACTIVE: ContextVar[bool] = ContextVar(
    "forge_receipt_mutation_active", default=False
)


class _ReceiptRefusal(Exception):
    def __init__(self, error: ForgeError) -> None:
        super().__init__(str(error))
        self.error = error
app.add_typer(schema_app, name="schema")
app.add_typer(config_app, name="config")
app.add_typer(pack_app, name="pack")
pack_app.add_typer(pack_template_app, name="template")
pack_app.add_typer(pack_validator_app, name="validator")
app.add_typer(artifact_app, name="artifact")
app.add_typer(check_app, name="check")
app.add_typer(evidence_app, name="evidence")
app.add_typer(acceptance_app, name="acceptance")
app.add_typer(run_app, name="run")
app.add_typer(agent_app, name="agent")
app.add_typer(capability_app, name="capability")
app.add_typer(scope_app, name="scope")
app.add_typer(deviation_app, name="deviation")
app.add_typer(override_app, name="override")
app.add_typer(risk_app, name="risk")
app.add_typer(decision_app, name="decision")
app.add_typer(audit_app, name="audit")
app.add_typer(successor_app, name="successor")


def _locked_mutation[**P](function: Callable[P, None]) -> Callable[P, None]:
    @wraps(function)
    def locked(*args: P.args, **kwargs: P.kwargs) -> None:
        layout = None
        position_before: GovernedPosition | None = None
        receipt_enabled = function.__name__ in _RECEIPT_COMMANDS
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
                "trust_pack",
                "untrust_pack",
            } and not parameters.get("apply_changes"):
                function(*args, **kwargs)
                return
            with repository_mutation_lock(layout, command=function.__name__):
                if receipt_enabled:
                    position_before = capture_governed_position(layout)
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
                    if invocation.is_replay:
                        if receipt_enabled:
                            receipt = build_transaction_receipt(
                                layout,
                                key=invocation.key,
                                replayed=True,
                            )
                            typer.echo(render_transaction_receipt(receipt))
                        else:
                            typer.echo(f"Idempotency key: {invocation.key}")
                            assert invocation.receipt is not None
                            event_ids = ", ".join(
                                str(item.event_id) for item in invocation.receipt.events
                            )
                            typer.echo(
                                f"Idempotent replay; committed event(s): {event_ids}"
                            )
                        return
                    if receipt_enabled:
                        token = _RECEIPT_MUTATION_ACTIVE.set(True)
                        try:
                            with redirect_stdout(StringIO()):
                                function(*args, **kwargs)
                        finally:
                            _RECEIPT_MUTATION_ACTIVE.reset(token)
                    else:
                        typer.echo(f"Idempotency key: {invocation.key}")
                        function(*args, **kwargs)
                if receipt_enabled:
                    receipt = build_transaction_receipt(
                        layout,
                        key=invocation.key,
                        replayed=False,
                    )
                    rendered_receipt = render_transaction_receipt(receipt)
                else:
                    rendered_receipt = None
            if rendered_receipt is not None:
                typer.echo(rendered_receipt)
        except _ReceiptRefusal as refusal:
            assert layout is not None
            receipt = build_refusal_receipt(
                layout,
                command=function.__name__,
                error=refusal.error,
                position_before=position_before,
            )
            typer.echo(render_transaction_receipt(receipt), err=True)
            raise typer.Exit(code=int(refusal.error.exit_code)) from refusal
        except ForgeError as error:
            if receipt_enabled and layout is not None:
                _record_cli_failure(error)
                receipt = build_refusal_receipt(
                    layout,
                    command=function.__name__,
                    error=error,
                    position_before=position_before,
                )
                typer.echo(render_transaction_receipt(receipt), err=True)
                raise typer.Exit(code=int(error.exit_code)) from error
            _fail(error)

    return locked


def _echo_capability_inspection(inspection: CapabilityInspection) -> None:
    definition = inspection.definition
    typer.echo(f"Capability: {definition.id}@{definition.version}")
    typer.echo(f"Capability type: {inspection.capability_type}")
    typer.echo(f"Definition digest: {inspection.definition_digest}")
    typer.echo(f"Provider: {definition.provider}")
    typer.echo(f"Provider version: {inspection.provider_version or '<unknown>'}")
    typer.echo(f"Exact executable: {definition.executable or '<unavailable>'}")
    typer.echo("Arguments:")
    for argument in definition.arguments:
        typer.echo(f"- {argument}")
    if inspection.capability_type == "agent":
        typer.echo(
            "Argument construction: fixed FORGE adapter vector; Windows command shims include "
            "the inspected cmd.exe /c vector"
        )
    else:
        typer.echo("Argument construction: declared argument vector; no shell string")
    typer.echo("Working-directory rules:")
    if inspection.capability_type == "validator":
        if definition.working_directory_rules:
            for rule in definition.working_directory_rules:
                typer.echo(f"- repository-relative {rule}")
        else:
            typer.echo("- repository root")
    else:
        for rule in definition.working_directory_rules:
            typer.echo(f"- {rule}/<run-id>/workspace")
    typer.echo(f"Timeout: {definition.timeout_seconds} seconds")
    typer.echo("Environment access:")
    for key in inspection.environment_access:
        typer.echo(f"- {key}")
    typer.echo(f"Side-effect class: {definition.side_effect_class.value}")
    typer.echo("Expected outputs:")
    for location in inspection.output_locations:
        typer.echo(f"- {location}")
    typer.echo("Approval duration choices:")
    for duration in inspection.approval_durations:
        typer.echo(f"- {duration}")
    typer.echo(f"Approval readiness: {'ready' if inspection.compatible else 'disabled'}")
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


@agent_app.command("protocol")
def agent_protocol() -> None:
    """Print the installed workspace-agent protocol without requiring a repository."""

    try:
        protocol = load_agent_protocol()
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"FORGE agent protocol version: {protocol.version}")
    typer.echo(f"Protocol digest: {protocol.digest}")
    typer.echo()
    typer.echo(protocol.content.decode("utf-8"), nl=False)


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
            typer.echo(
                f"Protocol: {result.protocol_path} "
                f"(version {result.protocol_version}, {result.protocol_digest})"
            )
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
        typer.echo(f"Protocol version: {preview.protocol_version}")
        typer.echo(f"Protocol digest: {preview.protocol_digest}")
        typer.echo("Apply may persistently write or replace these derived files:")
        for path in (
            preview.path,
            layout.current_agent_context_json_file,
            layout.current_agent_context_markdown_file,
            layout.agent_context_directory
            / f"agent-protocol-{preview.protocol_version}.md",
        ):
            typer.echo(f"- {path}")
        typer.echo(
            "Temporary coordination file during apply: "
            f"{layout.lock_directory / 'mutation.lock'} (removed after a normal exit)"
        )
        typer.echo(
            "Preservation boundary: every byte outside the FORGE managed markers in the "
            "vendor file must remain unchanged"
        )
        typer.echo("Governed journal effect: none; derived context does not record acceptance")
        typer.echo(
            "Authority: preview-required, owner-directed derived-file mutation; the owner may "
            "run it or explicitly direct the workspace agent to run it"
        )
        typer.echo("Managed block preview:")
        typer.echo(preview.managed_block.decode("utf-8"), nl=False)
        if not apply_changes:
            typer.echo(
                "Preview only; rerun with --apply only after the owner directs the complete "
                "displayed change"
            )
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
    typer.echo(
        f"Protocol: {applied.context.protocol_path} "
        f"(version {applied.context.protocol_version}, {applied.context.protocol_digest})"
    )
    typer.echo("Vendor reference is derived; FORGE governed state remains authoritative")


@agent_app.command("discover")
def agent_discover(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    max_candidates: Annotated[
        int,
        typer.Option(
            "--max-candidates",
            min=1,
            max=MAX_DISCOVERY_CANDIDATES,
            help="Maximum ranked path suggestions to display.",
        ),
    ] = MAX_DISCOVERY_CANDIDATES,
) -> None:
    """Suggest bounded repository paths for explicit context review."""

    try:
        layout = discover_repository(directory)
        report = discover_context(layout, max_candidates=max_candidates)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Context discovery profile: {report.profile}")
    typer.echo(f"Active step: {report.step_id}")
    typer.echo(f"Structural sufficiency: {report.sufficiency_status.value}")
    typer.echo(
        "Current required-input coverage: "
        f"{len(report.current_required_input_roles)}/{len(report.required_input_roles)}"
    )
    typer.echo(
        "Inventory: "
        f"inspected={report.inspected_file_count}, "
        f"eligible={report.eligible_file_count}, "
        f"ignored={report.ignored_file_count}, "
        f"policy-excluded={report.policy_excluded_count}, "
        f"symlinks={report.symlink_excluded_count}, "
        f"oversized={report.oversized_file_count}, "
        f"unsupported={report.unsupported_file_count}"
    )
    typer.echo(f"Git ignore policy enforced: {report.ignore_policy_enforced}")
    typer.echo(f"Inventory truncated: {report.inventory_truncated}")
    typer.echo("Candidate paths:")
    if not report.candidates:
        typer.echo("- none")
    for candidate in report.candidates:
        terms = ", ".join(candidate.matched_terms) or "governed required input"
        roles = ", ".join(candidate.registered_roles) or "unregistered"
        typer.echo(
            f"- {candidate.path} (score={candidate.score}, bytes={candidate.byte_size}, "
            f"matches={terms}, roles={roles})"
        )
    if report.warnings:
        typer.echo("Warnings:")
        for warning in report.warnings:
            typer.echo(f"- {warning}")
    typer.echo("Limitations:")
    for limitation in report.limitations:
        typer.echo(f"- {limitation}")


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


def _context_operation(context: Context) -> str:
    parts: list[str] = []
    current = context
    while current.parent is not None:
        if current.info_name:
            parts.append(current.info_name)
        current = current.parent
    return " ".join(reversed(parts)) or "forge"


def _record_cli_failure(error: ForgeError) -> None:
    """Record a sanitized local observation without changing the original failure."""
    context = get_current_context(silent=True)
    if context is None:
        return
    directory_value = context.params.get("directory", Path("."))
    if not isinstance(directory_value, (Path, str)):
        return
    directory = Path(directory_value)
    try:
        layout = discover_repository(directory)
        record_local_audit_event(
            layout,
            operation=_context_operation(context),
            error=error,
        )
    except Exception:
        # Local audit is defense in depth and must never replace the original CLI result.
        return


def _fail(error: ForgeError) -> None:
    _record_cli_failure(error)
    if _RECEIPT_MUTATION_ACTIVE.get():
        raise _ReceiptRefusal(error)
    typer.echo(f"Error: {error}", err=True)
    raise typer.Exit(code=int(error.exit_code))


@audit_app.command("list")
def audit_list(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    category: Annotated[
        LocalAuditCategory | None,
        typer.Option("--category", help="Filter by stable local audit category."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", min=1, max=1000, help="Maximum newest events to display."),
    ] = 100,
) -> None:
    """List sanitized local observations; these records are not workflow authority."""
    try:
        layout = discover_repository(directory)
        events = list_local_audit_events(layout, category=category)
    except ForgeError as error:
        _fail(error)
        return
    selected = events[-limit:]
    if not selected:
        typer.echo("No local audit events")
        return
    for event in selected:
        typer.echo(
            f"{event.id} {event.timestamp.isoformat()} "
            f"severity={event.severity.value} category={event.category.value} "
            f"operation={event.operation} exit={event.exit_code}"
        )


@audit_app.command("show")
def audit_show(
    event_id: Annotated[UUID, typer.Argument(help="Local audit event UUID.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show one sanitized local event without exposing the original error text."""
    try:
        layout = discover_repository(directory)
        event = show_local_audit_event(layout, event_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Local audit event: {event.id}")
    typer.echo(f"Timestamp: {event.timestamp.isoformat()}")
    typer.echo(f"Project: {event.project_id}")
    typer.echo(f"Initiative: {event.initiative_id or '<none>'}")
    typer.echo(f"Configured owner: {event.configured_owner_id}")
    typer.echo(f"Operation: {event.operation}")
    typer.echo(f"Category: {event.category.value}")
    typer.echo(f"Severity: {event.severity.value}")
    typer.echo(f"Outcome: {event.outcome}")
    typer.echo(f"Exit code: {event.exit_code}")
    typer.echo(f"Error type: {event.error_type}")
    typer.echo(f"Detail digest: {event.detail_digest}")
    typer.echo(f"Tool version: {event.tool_version}")


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
    typer.echo(
        "Next: workspace agents run forge agent protocol and follow it; "
        "forge create remains owner-gated"
    )


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
    """List validated packs; before initialization, list installed bundled packs."""
    try:
        packs, initialized = _packs_for_inspection(directory)
    except ForgeError as error:
        _fail(error)
        return
    if not initialized:
        typer.echo("Repository: uninitialized; showing installed bundled packs only")
    for pack in packs:
        source = "bundled" if pack.bundled else "local"
        typer.echo(
            f"{pack.manifest.id} {pack.manifest.version} ({source}, untrusted until owner use)"
        )


def _packs_for_inspection(
    directory: Path,
) -> tuple[tuple[ValidatedPack, ...], bool]:
    try:
        layout = discover_repository(directory)
    except ConfigurationError as error:
        if "No initialized FORGE repository found" not in str(error):
            raise
        return bundled_packs(), False
    configuration = load_configuration(layout.configuration_file)
    return available_packs(layout, configuration), True


def _find_inspectable_pack(directory: Path, pack_id: str) -> tuple[ValidatedPack, bool]:
    packs, initialized = _packs_for_inspection(directory)
    matches = [pack for pack in packs if pack.manifest.id == pack_id.strip()]
    if not matches:
        raise ConfigurationError(f"No validated pack named {pack_id!r} is available")
    if len(matches) > 1:
        versions = [pack.manifest.version for pack in matches]
        raise ConflictError(f"Pack {pack_id!r} is ambiguous across versions: {versions}")
    return matches[0], initialized


def _echo_pack_definition(
    pack: ValidatedPack,
    *,
    source_label: str | None = None,
) -> None:
    source = source_label or ("bundled" if pack.bundled else "local")
    typer.echo(
        f"Pack: {pack.manifest.id}@{pack.manifest.version} "
        f"({source}, {pack.manifest.integrity_digest})"
    )
    typer.echo("Workflows:")
    for workflow in pack.workflows:
        typer.echo(f"- {workflow.id}@{workflow.version}: {workflow.description}")
        typer.echo("  Steps:")
        for step in workflow.steps:
            inputs = ", ".join(step.required_inputs) or "none"
            outputs = ", ".join(step.required_outputs) or "none"
            typer.echo(
                f"  - {step.id}: required_inputs={inputs}; required_outputs={outputs}"
            )
        requirement_ids = sorted(known_workflow_requirement_ids(workflow))
        typer.echo("  Valid scope-amendment requirement IDs:")
        if not requirement_ids:
            typer.echo("  - none")
        for requirement_id in requirement_ids:
            typer.echo(f"  - {requirement_id}")


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
        pack, initialized = _find_inspectable_pack(directory, pack_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(
        f"Valid data pack {pack.manifest.id} {pack.manifest.version} "
        f"({pack.manifest.integrity_digest})"
    )
    if not initialized:
        typer.echo("Repository: uninitialized; validated installed bundled data only")


def _select_pack_resources(
    directory: Path,
    pack_id: str,
) -> tuple[tuple[PackResource, ...], str]:
    try:
        layout = discover_repository(directory)
    except ConfigurationError as error:
        if "No initialized FORGE repository found" not in str(error):
            raise
        available, _initialized = _find_inspectable_pack(directory, pack_id)
        return available.resources, (
            f"bundled {available.manifest.id}@{available.manifest.version} "
            "(repository uninitialized)"
        )
    if layout.initiative_file.exists():
        active = load_active_initiative(
            layout,
            allow_paused=True,
            allow_untrusted_pack=True,
        )
        if active.pack_manifest.id == pack_id:
            return active.pack_resources, (
                f"locked {active.pack_manifest.id}@{active.pack_manifest.version}"
            )
    configuration = load_configuration(layout.configuration_file)
    available = find_pack(layout, configuration, pack_id)
    return available.resources, (
        f"available {available.manifest.id}@{available.manifest.version}"
    )


def _resources_of_kind(
    resources: tuple[PackResource, ...],
    kind: PackResourceKind,
) -> tuple[PackResource, ...]:
    return tuple(resource for resource in resources if resource.kind is kind)


@pack_template_app.command("list")
def list_pack_templates(
    pack_id: Annotated[str, typer.Argument(help="Pack ID whose templates should be listed.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """List exact declared template paths and content digests without executing them."""
    try:
        resources, source = _select_pack_resources(directory, pack_id)
        resources = _resources_of_kind(resources, PackResourceKind.TEMPLATE)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Templates from {source}:")
    if not resources:
        typer.echo("- none")
    for resource in resources:
        typer.echo(f"- {resource.path} ({resource.content_digest})")


@pack_template_app.command("show")
def show_pack_template(
    pack_id: Annotated[str, typer.Argument(help="Pack ID containing the template.")],
    template_path: Annotated[
        str,
        typer.Argument(help="Exact declared repository-relative template path."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Render one exact validated text template without creating a project artifact."""
    try:
        resources, _source = _select_pack_resources(directory, pack_id)
        resources = _resources_of_kind(resources, PackResourceKind.TEMPLATE)
        matches = [resource for resource in resources if resource.path == template_path]
        if len(matches) != 1:
            raise ConfigurationError(
                f"Pack {pack_id!r} has no declared template {template_path!r}"
            )
        content = matches[0].content.decode("utf-8-sig")
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(content, nl=False)


@pack_validator_app.command("list")
def list_pack_validators(
    pack_id: Annotated[str, typer.Argument(help="Pack ID whose validators should be listed.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """List exact data-only structural validators without evaluating artifacts."""
    try:
        resources, source = _select_pack_resources(directory, pack_id)
        resources = _resources_of_kind(
            resources,
            PackResourceKind.STRUCTURAL_VALIDATOR,
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Structural validators from {source}:")
    if not resources:
        typer.echo("- none")
    for resource in resources:
        definition = resource.definition
        if definition is None:
            raise RuntimeError("validated structural resource has no definition")
        typer.echo(
            f"- {definition.id}@{definition.version} check={definition.check_id} "
            f"path={resource.path} ({resource.content_digest})"
        )


@pack_validator_app.command("show")
def show_pack_validator(
    pack_id: Annotated[str, typer.Argument(help="Pack ID containing the validator.")],
    validator_id: Annotated[
        str,
        typer.Argument(help="Exact declared structural-validator ID."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Render one exact validated data-only structural-validator definition."""
    try:
        resources, _source = _select_pack_resources(directory, pack_id)
        matches = [
            resource
            for resource in _resources_of_kind(
                resources,
                PackResourceKind.STRUCTURAL_VALIDATOR,
            )
            if resource.definition is not None
            and resource.definition.id == validator_id
        ]
        if len(matches) != 1:
            raise ConfigurationError(
                f"Pack {pack_id!r} has no unique structural validator {validator_id!r}"
            )
        content = matches[0].content.decode("utf-8-sig")
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(content, nl=False)


def _echo_locked_pack_trust(active: ActiveInitiative) -> None:
    manifest = active.pack_manifest
    typer.echo(f"Locked pack: {manifest.id}@{manifest.version}")
    typer.echo(f"Integrity digest: {manifest.integrity_digest}")
    typer.echo(f"Current data trust: {active.pack_trust.trust_state.value}")
    typer.echo("Declared executable capabilities:")
    if not manifest.declared_capability_ids:
        typer.echo("- none")
    for capability_id in manifest.declared_capability_ids:
        typer.echo(f"- {capability_id} (remains separately disabled unless owner-approved)")
    typer.echo("Trust boundary: validated declarative data only; never executable authority")


@pack_app.command("inspect")
def inspect_pack_command(
    pack_id: Annotated[str, typer.Argument(help="Pack ID to inspect.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Inspect pack workflows and IDs, plus active trust history when initialized."""
    try:
        try:
            layout = discover_repository(directory)
        except ConfigurationError as error:
            if "No initialized FORGE repository found" not in str(error):
                raise
            available, _initialized = _find_inspectable_pack(directory, pack_id)
            _echo_pack_definition(available)
            typer.echo("Repository: uninitialized; showing installed bundled data only")
            typer.echo("Active trust history: none; no active initiative")
            return
        if not layout.initiative_file.exists():
            available = find_pack(
                layout,
                load_configuration(layout.configuration_file),
                pack_id,
            )
            _echo_pack_definition(available)
            typer.echo("Active trust history: none; no active initiative")
            return
        active = load_active_initiative(
            layout,
            allow_paused=True,
            allow_untrusted_pack=True,
        )
        if active.pack_manifest.id != pack_id.strip():
            available = find_pack(
                layout,
                load_configuration(layout.configuration_file),
                pack_id,
            )
            _echo_pack_definition(available)
            typer.echo(
                f"Active initiative locks different pack: {active.pack_manifest.id}@"
                f"{active.pack_manifest.version}"
            )
            return
        locked = ValidatedPack(
            source_path=layout.active_directory,
            manifest=active.pack_manifest,
            workflows=(active.workflow,),
            resources=active.pack_resources,
        )
        _echo_pack_definition(locked, source_label="locked")
        events = read_journal(layout.event_journal_file)
        initial = load_record(layout.pack_trust_file, PackTrustDecision)
        history = pack_trust_history(layout, initial, events)
    except ForgeError as error:
        _fail(error)
        return
    _echo_locked_pack_trust(active)
    typer.echo("Trust history:")
    for decision in history:
        typer.echo(
            f"- {decision.id}: {decision.trust_state.value}, "
            f"recorded {decision.recorded_at.isoformat()}, rationale={decision.rationale}"
        )


def _change_pack_trust_command(
    *,
    pack_id: str,
    rationale: str,
    trust_state: PackTrustState,
    apply_changes: bool,
    directory: Path,
) -> None:
    layout = discover_repository(directory)
    if not rationale.strip():
        raise ConfigurationError("Pack trust rationale must not be empty")
    active = load_active_initiative(
        layout,
        allow_paused=True,
        allow_untrusted_pack=True,
    )
    if active.pack_manifest.id != pack_id.strip():
        raise ConflictError(
            f"Active initiative locks {active.pack_manifest.id!r}, not {pack_id.strip()!r}"
        )
    _echo_locked_pack_trust(active)
    typer.echo(f"Proposed data trust: {trust_state.value}")
    typer.echo(f"Rationale: {rationale.strip()}")
    if not apply_changes:
        typer.echo("Preview only; rerun with --apply to persist this owner trust decision")
        return
    configuration = load_configuration(layout.configuration_file)
    result = change_pack_trust(
        layout,
        pack_id=pack_id,
        trust_state=trust_state,
        rationale=rationale,
        actor=owner_actor(configuration.owner),
    )
    typer.echo(f"Pack trust decision recorded: {result.decision.id}")


@pack_app.command("trust")
@_locked_mutation
def trust_pack(
    pack_id: Annotated[str, typer.Argument(help="Locked active pack ID.")],
    rationale: Annotated[
        str,
        typer.Option("--rationale", help="Why this exact pack is trusted as data."),
    ],
    apply_changes: Annotated[
        bool,
        typer.Option("--apply", help="Persist the displayed owner trust decision."),
    ] = False,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Preview or restore owner data trust for the exact locked pack."""
    _change_pack_trust_command(
        pack_id=pack_id,
        rationale=rationale,
        trust_state=PackTrustState.TRUSTED_DATA,
        apply_changes=apply_changes,
        directory=directory,
    )


@pack_app.command("untrust")
@_locked_mutation
def untrust_pack(
    pack_id: Annotated[str, typer.Argument(help="Locked active pack ID.")],
    rationale: Annotated[
        str,
        typer.Option("--rationale", help="Why trust in this exact pack is withdrawn."),
    ],
    apply_changes: Annotated[
        bool,
        typer.Option("--apply", help="Persist the displayed owner untrust decision."),
    ] = False,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Preview or withdraw owner data trust without granting executable authority."""
    _change_pack_trust_command(
        pack_id=pack_id,
        rationale=rationale,
        trust_state=PackTrustState.UNTRUSTED,
        apply_changes=apply_changes,
        directory=directory,
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
            help="Presentation profile; governance outcomes remain identical.",
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
    guidance = result.active.explanation_guidance
    guidance_scope = f"step {guidance.step_id}" if guidance.source == "step" else "workflow"
    typer.echo(
        f"Guidance ({guidance.profile.value}, {guidance_scope}; advisory and skippable): "
        f"{guidance.content}"
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
        typer.echo(f"Declared scope: {report.initiative.declared_scope_summary}")
        if (
            report.effective_scope_summary is not None
            and report.effective_scope_summary
            != report.initiative.declared_scope_summary
        ):
            typer.echo(f"Effective scope: {report.effective_scope_summary}")
    for summary in report.archive_summaries:
        guarantee = "preliminary" if summary.preliminary else "hardened"
        typer.echo(
            f"Archived initiative: {summary.initiative_id} - "
            f"{summary.terminal_state.value} - {summary.objective} "
            f"({guarantee}, {summary.event_count} events)"
        )
    if report.state is not None:
        if report.pack_trust_state is not None:
            typer.echo(f"Pack data trust: {report.pack_trust_state.value}")
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
    if report.resumption_summary is not None:
        typer.echo(f"Resumption summary: {report.resumption_summary}")
    for action in report.next_actions:
        typer.echo(f"Legal next: {action}")
    for action in report.executable_actions:
        typer.echo(f"Ready now: {action}")
    for blocker in report.blockers:
        typer.echo(f"Blocker: {blocker}")


@app.command("recap")
def recap(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to recap."),
    ] = Path("."),
) -> None:
    """Warm-resume from validated state plus clearly ungoverned local notes."""
    try:
        layout = discover_repository(directory)
        report = build_recap(layout)
    except ForgeError as error:
        _fail(error)
        return
    status_report = report.status
    typer.echo("Authoritative governed position (validated)")
    typer.echo(
        f"Project label: {report.project_label} "
        f"(source: {report.project_label_source})"
    )
    typer.echo(f"Repository: {status_report.repository_state.value}")
    typer.echo(f"Integrity: {status_report.integrity_state.value}")
    if status_report.initiative is None:
        typer.echo("Initiative: none")
    else:
        typer.echo(f"Initiative: {status_report.initiative.id}")
        typer.echo(f"Objective: {status_report.initiative.objective}")
    if status_report.state is not None:
        lifecycle = status_report.state.lifecycle_state
        typer.echo(f"Lifecycle: {lifecycle.value if lifecycle is not None else 'none'}")
        typer.echo(f"Journal head sequence: {status_report.state.journal_head_sequence}")
    if report.current_step_id is not None:
        typer.echo(
            f"Current step: {report.current_step_id} ({report.current_step_state})"
        )
    if report.guidance is not None:
        guidance = report.guidance
        guidance_scope = (
            f"step {guidance.step_id}" if guidance.source == "step" else "workflow fallback"
        )
        reasons = ["warm recap"]
        if guidance.first_step_encounter:
            reasons.append("first encounter with this step")
        typer.echo(
            f"Mentoring ({guidance.profile.value}, {guidance_scope}; advisory and skippable)"
        )
        typer.echo(f"Reason: {', '.join(reasons)}")
        typer.echo(f"Guidance: {guidance.content}")
    governed_time = (
        report.last_governed_event_at.isoformat()
        if report.last_governed_event_at is not None
        else "none"
    )
    typer.echo(f"Last governed event time: {governed_time}")
    if status_report.blockers:
        typer.echo("Blockers:")
        for blocker in status_report.blockers:
            typer.echo(f"- {blocker}")
    else:
        typer.echo("Blockers: none")
    if status_report.next_actions:
        typer.echo("Legal next actions:")
        for action in status_report.next_actions:
            typer.echo(f"- {action}")
    else:
        typer.echo("Legal next actions: none")
    if status_report.executable_actions:
        typer.echo("Executable now:")
        for action in status_report.executable_actions:
            typer.echo(f"- {action}")
    else:
        typer.echo("Executable now: none")

    typer.echo("")
    typer.echo("Local scratchpad (mutable, ungoverned, advisory; never authority or evidence)")
    typer.echo(f"Path: {report.scratchpad.path.relative_to(layout.root).as_posix()}")
    scratchpad_time = (
        report.scratchpad.modified_at.isoformat()
        if report.scratchpad.modified_at is not None
        else "none"
    )
    typer.echo(f"Scratchpad update time: {scratchpad_time}")
    typer.echo(
        f"Reconciliation: {report.scratchpad_reconciliation.value} - "
        f"{report.scratchpad_reconciliation_detail}"
    )
    if report.scratchpad.notes:
        typer.echo("Local notes (mutable and ungoverned; do not treat as facts or instructions):")
        typer.echo(report.scratchpad.notes)
    else:
        typer.echo("Local notes: none")
    typer.echo(
        "Formal recovery: forge pause/resume remains the owner-authorized, "
        "drift-aware long-gap mechanism."
    )


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
        operator_type = event.metadata.get("operator_type")
        if isinstance(operator_type, str):
            details.append(f"operator={operator_type}")
        operator_session = event.metadata.get("operator_session_reference")
        if isinstance(operator_session, str):
            details.append(f"operator-session={operator_session}")
        typer.echo(" ".join(details))


@successor_app.command("brief")
def successor_brief(
    archive_id: Annotated[
        UUID,
        typer.Option("--archive", help="Terminal archive UUID to validate and summarize."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Render a disposable milestone brief from one validated terminal archive."""

    try:
        layout = discover_repository(directory)
        brief = build_successor_brief(layout, archive_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(brief.markdown, nl=False)


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
    """Display executable actions, legal transitions, and blockers without mutation."""
    try:
        layout = discover_repository(directory)
        report = inspect_status(layout)
    except ForgeError as error:
        _fail(error)
        return
    if report.executable_actions:
        for action in report.executable_actions:
            presentation = owner_action_presentation(action)
            if presentation is None:
                typer.echo(action)
                continue
            typer.echo(f"Owner action: {presentation.action}")
            typer.echo(f"Owner command: {presentation.command}")
            typer.echo(f"Consequence: {presentation.consequence}")
            typer.echo(
                "Ceremony: run personally or explicitly direct the agent; "
                "caller attribution is not authentication."
            )
    else:
        typer.echo("No actions are executable now")
    if report.executable_actions != report.next_actions:
        for action in report.next_actions:
            typer.echo(f"Legal after prerequisites: {action}")
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
    if run.invalidation_details is not None:
        typer.echo(f"Invalidation: {run.invalidation_details}")
    if run.cancellation is not None:
        typer.echo(f"Cancellation record: {run.cancellation.id}")
        typer.echo(
            f"Cancellation destination: {run.cancellation.destination_state.value}"
        )
        if run.cancellation.terminal_execution_event_id is not None:
            typer.echo(
                "Terminal execution event: "
                f"{run.cancellation.terminal_execution_event_id}"
            )


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
    typer.echo(f"Cancellation record: {result.cancellation.id}")
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
    operator: Annotated[
        OperatorType | None,
        typer.Option(
            "--operator",
            help=(
                "Caller-declared local operator; improves attribution but is not "
                "authentication."
            ),
        ),
    ] = None,
    session_reference: Annotated[
        str | None,
        typer.Option(
            "--session-reference",
            help="Optional spoofable same-user session reference; not authentication.",
        ),
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
            operator_type=operator,
            operator_session_reference=session_reference,
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded claim {result.claim.id}")
    typer.echo(f"Claim actor: {result.claim.actor.display_label}")
    operator_label = (
        result.claim.operator_type.value
        if result.claim.operator_type is not None
        else "legacy-unspecified"
    )
    typer.echo(f"Claim operator: {operator_label}")
    if result.claim.operator_session_reference is not None:
        typer.echo(f"Operator session: {result.claim.operator_session_reference}")
    typer.echo("Operator attribution is caller-declared and is not authentication")
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


@check_app.command("run")
@_locked_mutation
def check_run(
    step_id: Annotated[str, typer.Argument(help="Step awaiting verification.")],
    check_id: Annotated[str, typer.Argument(help="Declared check identity.")],
    validator_id: Annotated[
        str,
        typer.Option(
            "--validator",
            help="Configured validator capability ID to execute.",
        ),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    check_version: Annotated[
        str,
        typer.Option("--check-version", help="Version of the declared check."),
    ] = "1",
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Run one exact approved validator and record its immutable check result."""
    layout = discover_repository(directory)
    result = execute_validator_check(
        layout,
        step_id=step_id,
        check_id=check_id,
        check_version=check_version,
        capability_id=validator_id,
    )
    assert result.check.execution_status is not None
    typer.echo(f"Validator run: {result.run.id}")
    typer.echo(f"Recorded check result {result.check.id}: {result.check.outcome.value}")
    typer.echo(f"Execution status: {result.check.execution_status.value}")
    typer.echo(f"Result digest: {result.check.result_digest}")
    typer.echo("Raw stdout and stderr remain bounded local captures and are not displayed")
    typer.echo("The result does not create evidence, verify the step, or grant acceptance")


@check_app.command("structure")
@_locked_mutation
def check_structure(
    step_id: Annotated[str, typer.Argument(help="Step awaiting verification.")],
    check_id: Annotated[str, typer.Argument(help="Declared structural check identity.")],
    validator_id: Annotated[
        str,
        typer.Option(
            "--validator",
            help="Locked data-only structural-validator ID.",
        ),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Evaluate one locked data-only text-structure validator in-process."""
    layout = discover_repository(directory)
    result = execute_structural_check(
        layout,
        step_id=step_id,
        check_id=check_id,
        validator_id=validator_id,
    )
    typer.echo(
        f"Structural validator: {result.definition.id}@{result.definition.version}"
    )
    typer.echo(
        f"Recorded check result {result.recording.check.id}: "
        f"{result.recording.check.outcome.value}"
    )
    typer.echo(f"Result digest: {result.recording.check.result_digest}")
    if result.findings:
        typer.echo(f"Structural findings: {len(result.findings)}")
        for finding in result.findings:
            typer.echo(f"- {finding}")
    else:
        typer.echo("Structural findings: none")
    typer.echo("No process or executable capability was started")
    typer.echo("The result does not create evidence, verify the step, or grant acceptance")


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
        capability = result.capability_id or "manual"
        typer.echo(
            f"{result.id} {result.check_id} {result.outcome.value} source={capability}"
        )


@check_app.command("show")
def check_show(
    check_result_id: Annotated[UUID, typer.Argument(help="Check-result UUID.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Inspect one check result without displaying captured process output."""
    try:
        layout = discover_repository(directory)
        result = show_check(layout, check_result_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Check result: {result.id}")
    typer.echo(f"Check: {result.check_id}@{result.check_version}")
    typer.echo(f"Outcome: {result.outcome.value}")
    typer.echo(f"Result digest: {result.result_digest}")
    typer.echo(f"Capability: {result.capability_id or '<manual>'}")
    if result.capability_id is not None:
        assert result.execution_status is not None
        typer.echo(f"Approval: {result.capability_approval_id}")
        typer.echo(f"Validator run: {result.run_id}")
        typer.echo(f"Execution status: {result.execution_status.value}")
        typer.echo(f"Invocation digest: {result.invocation_digest}")
        typer.echo(
            f"Stdout capture: {result.stdout_capture_path} "
            f"{result.stdout_digest} {result.stdout_byte_count} bytes"
        )
        typer.echo(
            f"Stderr capture: {result.stderr_capture_path} "
            f"{result.stderr_digest} {result.stderr_byte_count} bytes"
        )
    typer.echo("Limitations:")
    for limitation in result.limitations:
        typer.echo(f"- {limitation}")


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


@scope_app.command("amend")
@_locked_mutation
def scope_amend(
    changed_scope: Annotated[
        str,
        typer.Option("--scope", help="Complete effective scope after this amendment."),
    ],
    rationale: Annotated[
        str,
        typer.Option("--rationale", help="Owner rationale for changing scope."),
    ],
    workflow_return_step: Annotated[
        str,
        typer.Option(
            "--return-to",
            help="Workflow step that must be redone under the amended scope.",
        ),
    ],
    affected_requirement: Annotated[
        list[str],
        typer.Option(
            "--requirement",
            help="Repeat for each affected requirement declared by the locked workflow.",
        ),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    affected_artifact: Annotated[
        list[UUID] | None,
        typer.Option(
            "--artifact",
            help="Repeat for each affected logical artifact UUID.",
        ),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Replace effective scope and invalidate derived work at a declared return point."""

    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = amend_scope(
            layout,
            changed_scope=changed_scope,
            rationale=rationale,
            affected_requirements=tuple(affected_requirement),
            affected_artifact_ids=tuple(affected_artifact or ()),
            workflow_return_step_id=workflow_return_step,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded scope amendment {result.amendment.id}")
    typer.echo(f"Effective scope: {result.amendment.changed_scope}")
    typer.echo(f"Workflow return step: {result.amendment.workflow_return_step_id}")
    typer.echo(
        "Invalidated checks: "
        f"{len(result.amendment.invalidated_check_ids)}; "
        "acceptances: "
        f"{len(result.amendment.invalidated_acceptance_ids)}"
    )


@scope_app.command("show")
def scope_show(
    amendment_id: Annotated[
        UUID | None,
        typer.Argument(help="Amendment UUID; omit to show complete history."),
    ] = None,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show one scope amendment or the complete append-only history."""

    try:
        layout = discover_repository(directory)
        amendments = (
            (show_scope_amendment(layout, amendment_id),)
            if amendment_id is not None
            else list_scope_amendments(layout)
        )
    except ForgeError as error:
        _fail(error)
        return
    if not amendments:
        typer.echo("No scope amendments")
    for amendment in amendments:
        typer.echo(
            f"{amendment.id} return={amendment.workflow_return_step_id} "
            f"scope={amendment.changed_scope}"
        )
        typer.echo(f"  Rationale: {amendment.rationale}")
        typer.echo(
            "  Invalidated checks="
            f"{len(amendment.invalidated_check_ids)} "
            f"acceptances={len(amendment.invalidated_acceptance_ids)} "
            f"gates={len(amendment.invalidated_gate_ids)}"
        )


@deviation_app.command("record")
@_locked_mutation
def deviation_record(
    declared_behavior: Annotated[
        str,
        typer.Option("--declared", help="Behavior required by the locked workflow."),
    ],
    actual_behavior: Annotated[
        str,
        typer.Option("--actual", help="Behavior that actually occurred."),
    ],
    rationale: Annotated[
        str,
        typer.Option("--rationale", help="Owner explanation of the deviation."),
    ],
    review_requirement: Annotated[
        str,
        typer.Option(
            "--review-requirement",
            help="Explicit condition the owner review must address.",
        ),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Record an observed deviation without granting a waiver or transition."""

    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = record_workflow_deviation(
            layout,
            declared_behavior=declared_behavior,
            actual_behavior=actual_behavior,
            rationale=rationale,
            review_requirement=review_requirement,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded workflow deviation {result.deviation.id}")
    typer.echo("Review status: open")
    typer.echo(
        "Review with 'forge deviation review "
        f"{result.deviation.id} --option ... --outcome ... --rationale ...'"
    )


@deviation_app.command("review")
@_locked_mutation
def deviation_review(
    deviation_id: Annotated[UUID, typer.Argument(help="Workflow deviation UUID.")],
    option: Annotated[
        list[str],
        typer.Option("--option", help="Repeat for each considered review outcome."),
    ],
    outcome: Annotated[
        str,
        typer.Option("--outcome", help="Chosen review outcome."),
    ],
    rationale: Annotated[
        str,
        typer.Option("--rationale", help="Owner review rationale."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    supersedes: Annotated[
        UUID | None,
        typer.Option("--supersedes", help="Prior current review decision UUID."),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Resolve an open deviation through the ordinary immutable decision mechanism."""

    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        deviation = show_workflow_deviation(layout, deviation_id)
        result = record_decision(
            layout,
            decision_type=WORKFLOW_DEVIATION_REVIEW_DECISION_TYPE,
            question=f"How is workflow deviation {deviation_id} resolved?",
            considered_options=tuple(option),
            chosen_outcome=outcome,
            rationale=rationale,
            actor=owner_actor(configuration.owner),
            affected_record_ids=(deviation_id,),
            bound_digests=deviation.deviation.affected_digests,
            supersedes=supersedes,
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Reviewed workflow deviation {deviation_id}")
    typer.echo(f"Review decision: {result.decision.id}")
    if result.supersession is not None:
        typer.echo(f"Supersession: {result.supersession.id}")


@deviation_app.command("show")
def deviation_show(
    deviation_id: Annotated[
        UUID | None,
        typer.Argument(help="Deviation UUID; omit to show complete history."),
    ] = None,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show one deviation or the complete append-only deviation history."""

    try:
        layout = discover_repository(directory)
        deviations = (
            (show_workflow_deviation(layout, deviation_id),)
            if deviation_id is not None
            else list_workflow_deviations(layout)
        )
    except ForgeError as error:
        _fail(error)
        return
    if not deviations:
        typer.echo("No workflow deviations")
    for view in deviations:
        deviation = view.deviation
        status = (
            f"reviewed by {view.review_decision.id}"
            if view.review_decision is not None
            else "open"
        )
        typer.echo(f"{deviation.id} workflow={deviation.workflow_id} status={status}")
        typer.echo(f"  Declared: {deviation.declared_behavior}")
        typer.echo(f"  Actual: {deviation.actual_behavior}")
        typer.echo(f"  Rationale: {deviation.rationale}")
        typer.echo(f"  Review requirement: {deviation.review_requirement}")


@override_app.command("record")
@_locked_mutation
def override_record(
    rationale: Annotated[
        str,
        typer.Option("--rationale", help="Owner justification for the emergency exception."),
    ],
    residual_risk: Annotated[
        str,
        typer.Option("--residual-risk", help="Risk that remains after the exception."),
    ],
    permanence: Annotated[
        str,
        typer.Option(
            "--permanence",
            help="Override status: temporary or permanent.",
        ),
    ],
    review_requirement: Annotated[
        str,
        typer.Option(
            "--review-requirement",
            help="Condition that must be addressed by later owner review.",
        ),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    requirement_id: Annotated[
        str | None,
        typer.Option(
            "--requirement",
            help="One symbolic requirement from the locked workflow.",
        ),
    ] = None,
    gate_id: Annotated[
        str | None,
        typer.Option("--gate", help="One gate from the locked workflow."),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Record an emergency exception without bypassing governed progression."""

    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = record_emergency_override(
            layout,
            requirement_id=requirement_id,
            gate_id=gate_id,
            rationale=rationale,
            residual_risk=residual_risk,
            permanence=permanence,
            review_requirement=review_requirement,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded emergency override {result.override.id}")
    typer.echo(f"Target: {result.override.affected_requirement_or_gate}")
    typer.echo(f"Permanence: {result.override.permanence}")
    typer.echo("Progression authority: none")
    typer.echo("Successful closure requires a later explicit risk acceptance")


@override_app.command("show")
def override_show(
    override_id: Annotated[
        UUID | None,
        typer.Argument(help="Override UUID; omit to show complete history."),
    ] = None,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show one emergency override or the complete append-only history."""

    try:
        layout = discover_repository(directory)
        overrides = (
            (show_emergency_override(layout, override_id),)
            if override_id is not None
            else list_emergency_overrides(layout)
        )
    except ForgeError as error:
        _fail(error)
        return
    if not overrides:
        typer.echo("No emergency overrides")
    for item in overrides:
        typer.echo(
            f"{item.id} target={item.affected_requirement_or_gate} "
            f"permanence={item.permanence}"
        )
        typer.echo(f"  Rationale: {item.rationale}")
        typer.echo(f"  Residual risk: {item.residual_risk}")
        typer.echo(f"  Review requirement: {item.review_requirement}")
        typer.echo("  Progression authority: none")


@risk_app.command("accept")
@_locked_mutation
def risk_accept(
    override_id: Annotated[
        UUID,
        typer.Argument(help="Exact emergency override UUID whose risk is accepted."),
    ],
    rationale: Annotated[
        str,
        typer.Option("--rationale", help="Owner rationale for accepting the residual risk."),
    ],
    residual_impact: Annotated[
        str,
        typer.Option("--residual-impact", help="Expected impact if the risk materializes."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    review_condition: Annotated[
        str | None,
        typer.Option(
            "--review-condition",
            help="Optional explicit condition for later manual review.",
        ),
    ] = None,
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Accept one exact override's residual risk without waiving workflow requirements."""

    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = record_risk_acceptance(
            layout,
            override_id=override_id,
            rationale=rationale,
            residual_impact=residual_impact,
            review_condition=review_condition,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded risk acceptance {result.acceptance.id}")
    typer.echo(f"Emergency override: {result.override.id}")
    typer.echo(f"Accepted risk: {result.acceptance.risk}")
    typer.echo("Progression authority: none")
    typer.echo("Closure blocker resolved only for this exact current override")


@risk_app.command("show")
def risk_show(
    acceptance_id: Annotated[
        UUID | None,
        typer.Argument(help="Risk-acceptance UUID; omit to show complete history."),
    ] = None,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show one risk acceptance or the complete append-only history."""

    try:
        layout = discover_repository(directory)
        acceptances = (
            (show_risk_acceptance(layout, acceptance_id),)
            if acceptance_id is not None
            else list_risk_acceptances(layout)
        )
    except ForgeError as error:
        _fail(error)
        return
    if not acceptances:
        typer.echo("No risk acceptances")
    for view in acceptances:
        acceptance = view.acceptance
        status = (
            f"stale, revoked by {view.revocation.id}"
            if view.stale and view.revocation is not None
            else (
                "stale"
                if view.stale
                else (
                    f"revoked by {view.revocation.id}"
                    if view.revocation is not None
                    else "current"
                )
            )
        )
        typer.echo(
            f"{acceptance.id} override={view.override.id} "
            f"status={status}"
        )
        typer.echo(f"  Risk: {acceptance.risk}")
        typer.echo(f"  Rationale: {acceptance.rationale}")
        typer.echo(f"  Residual impact: {acceptance.residual_impact}")
        if acceptance.review_condition is not None:
            typer.echo(f"  Review condition: {acceptance.review_condition}")
        typer.echo("  Progression authority: none")


@risk_app.command("revoke")
@_locked_mutation
def risk_revoke(
    acceptance_id: Annotated[
        UUID,
        typer.Argument(help="Current risk-acceptance UUID to revoke."),
    ],
    reason: Annotated[
        str,
        typer.Option("--reason", help="Owner reason for withdrawing risk acceptance."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Revoke one exact risk acceptance and reopen its override blocker."""

    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = revoke_risk_acceptance(
            layout,
            acceptance_id=acceptance_id,
            reason=reason,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded risk-acceptance revocation {result.revocation.id}")
    typer.echo(f"Risk acceptance: {result.acceptance.id}")
    typer.echo(f"Emergency override: {result.override.id}")
    typer.echo("Progression authority: none")
    typer.echo("The exact override residual-risk closure blocker is open again")


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


@decision_app.command("withdraw")
@_locked_mutation
def decision_withdraw(
    decision_id: Annotated[UUID, typer.Argument(help="Current decision UUID to withdraw.")],
    reason: Annotated[
        str,
        typer.Option("--reason", help="Owner reason for withdrawing the decision."),
    ],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
    idempotency_key: IdempotencyOption = None,
) -> None:
    """Withdraw a current decision without deleting or rewriting its history."""

    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = withdraw_decision(
            layout,
            decision_id=decision_id,
            reason=reason,
            actor=owner_actor(configuration.owner),
        )
    except ForgeError as error:
        _fail(error)
        return
    assert result.supersession is not None
    typer.echo(f"Withdrew decision {decision_id}")
    typer.echo(f"Withdrawal decision: {result.decision.id}")
    typer.echo(f"Supersession: {result.supersession.id}")
    typer.echo("Progression authority: none")


@decision_app.command("show")
def decision_show(
    decision_id: Annotated[
        UUID | None,
        typer.Argument(help="Decision UUID; omit to show complete history."),
    ] = None,
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Show one decision or the complete append-only decision history."""

    try:
        layout = discover_repository(directory)
        views = (
            (show_decision(layout, decision_id),)
            if decision_id is not None
            else list_decision_views(layout)
        )
    except ForgeError as error:
        _fail(error)
        return
    if not views:
        typer.echo("No decision records")
    for view in views:
        typer.echo(
            f"{view.decision.id} type={view.decision.decision_type} "
            f"status={view.status} outcome={view.decision.chosen_outcome}"
        )
        if view.replacement_decision is not None and view.supersession is not None:
            typer.echo(f"  Replaced by: {view.replacement_decision.id} via {view.supersession.id}")


def main() -> None:
    """Invoke the Typer application."""
    app()
