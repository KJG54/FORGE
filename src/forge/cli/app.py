"""Command-line presentation for the currently authorized FORGE increment."""

from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer

from forge import __version__
from forge.contracts.capabilities import SideEffectClass
from forge.contracts.verification import CheckOutcome
from forge.core.artifacts import add_artifact, list_artifacts, revise_artifact, show_artifact
from forge.core.authorization import owner_actor
from forge.core.lifecycle import begin_manual_run, create_initiative
from forge.core.status import inspect_status
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
from forge.errors import ForgeError
from forge.packs.loader import available_packs, find_pack
from forge.schemas import export_schema_bundle
from forge.storage.configuration import load_configuration, render_configuration
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
app.add_typer(schema_app, name="schema")
app.add_typer(config_app, name="config")
app.add_typer(pack_app, name="pack")
app.add_typer(artifact_app, name="artifact")
app.add_typer(check_app, name="check")
app.add_typer(evidence_app, name="evidence")


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
        typer.echo("Added .forge/local/ to .gitignore")


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
    trust_pack_data: Annotated[
        bool,
        typer.Option(
            "--trust-pack-data",
            help="Owner confirmation for this exact data pack; never authorizes execution.",
        ),
    ] = False,
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
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Created initiative {result.active.initiative.id}")
    typer.echo(
        f"Locked {result.active.pack_manifest.id} {result.active.pack_manifest.version} / "
        f"{result.active.workflow.id} {result.active.workflow.version}"
    )
    typer.echo(f"Next: {', '.join(result.active.state.permitted_next_actions)}")


@app.command("status")
def status(
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory to inspect."),
    ] = Path("."),
) -> None:
    """Validate and display current repository and initiative state."""
    try:
        layout = discover_repository(directory)
        report = inspect_status(layout)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Repository: {report.repository_state.value}")
    typer.echo(f"Integrity: {report.integrity_state.value}")
    if report.initiative is None:
        typer.echo("Initiative: none")
    else:
        typer.echo(f"Initiative: {report.initiative.id} — {report.initiative.objective}")
    if report.state is not None:
        typer.echo(f"Lifecycle: {report.state.lifecycle_state}")
        for step_id, step_state in report.state.step_states.items():
            typer.echo(f"Step {step_id}: {step_state.value}")
        for run_id in report.state.active_run_ids:
            typer.echo(f"Active run: {run_id}")
        for gate_id in report.state.open_gate_ids:
            typer.echo(f"Open gate: {gate_id}")
    for action in report.next_actions:
        typer.echo(f"Next: {action}")
    for blocker in report.blockers:
        typer.echo(f"Blocker: {blocker}")


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


@artifact_app.command("add")
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
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Registered artifact {result.artifact.id} revision 1")
    typer.echo(f"Revision ID: {result.revision.id}")
    typer.echo(f"Digest: {result.revision.content_digest}")
    typer.echo(f"Preserved: {result.revision.preserved_object_path}")


@artifact_app.command("revise")
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
    typer.echo("Dependency invalidation remains assigned to M1 Increment 5")


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
    typer.echo(f"Working copy matches: {str(view.working_copy_matches).lower()}")
    typer.echo("Stale dependency propagation: deferred to M1 Increment 5")


@app.command("complete")
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
    limitation: Annotated[
        list[str] | None,
        typer.Option("--limitation", help="Repeat for each known claim limitation."),
    ] = None,
) -> None:
    """Record a worker claim and submit current declared outputs for checking."""
    try:
        layout = discover_repository(directory)
        configuration = load_configuration(layout.configuration_file)
        result = complete_step(
            layout,
            step_id=step_id,
            assertion=assertion,
            actor=owner_actor(configuration.owner),
            limitations=tuple(limitation or ()),
        )
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Recorded claim {result.claim.id}")
    typer.echo(f"Step {step_id}: {result.transition.state.step_states[step_id].value}")
    typer.echo("The claim is not a check, evidence packet, or owner acceptance")


@check_app.command("record")
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
def verify(
    step_id: Annotated[str, typer.Argument(help="Step awaiting verification.")],
    directory: Annotated[
        Path,
        typer.Option("--directory", "-C", help="Repository or child directory."),
    ] = Path("."),
) -> None:
    """Derive check/evidence conditions and advance only when both are current."""
    try:
        layout = discover_repository(directory)
        result = verify_step(layout, step_id=step_id)
    except ForgeError as error:
        _fail(error)
        return
    typer.echo(f"Step {step_id}: {result.state.step_states[step_id].value}")
    typer.echo("Owner acceptance is still required and belongs to M1 Increment 5")


def main() -> None:
    """Invoke the Typer application."""
    app()
