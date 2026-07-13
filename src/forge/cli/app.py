"""Command-line presentation for the currently authorized FORGE increment."""

from pathlib import Path
from typing import Annotated

import typer

from forge import __version__
from forge.errors import ForgeError
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
app.add_typer(schema_app, name="schema")
app.add_typer(config_app, name="config")


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


def main() -> None:
    """Invoke the Typer application."""
    app()
