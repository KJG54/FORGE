"""Command-line presentation for the currently authorized FORGE increment."""

from pathlib import Path
from typing import Annotated

import typer

from forge import __version__
from forge.contracts.capabilities import SideEffectClass
from forge.core.authorization import owner_actor
from forge.core.lifecycle import begin_manual_run, create_initiative
from forge.core.status import inspect_status
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
app.add_typer(schema_app, name="schema")
app.add_typer(config_app, name="config")
app.add_typer(pack_app, name="pack")


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


def main() -> None:
    """Invoke the Typer application."""
    app()
