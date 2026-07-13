"""Milestone 0 command-line scaffold."""

from typing import Annotated

import typer

from forge import __version__

app = typer.Typer(
    name="forge",
    help="Govern human-directed, AI-assisted work in an ordinary repository.",
    no_args_is_help=True,
)
schema_app = typer.Typer(help="Inspect or export versioned FORGE schemas.")
app.add_typer(schema_app, name="schema")


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
    """Expose M0 diagnostics without implementing lifecycle behavior."""


@schema_app.command("export")
def export_schemas() -> None:
    """Report schema-export availability before M1 contracts exist."""
    typer.echo("No production schemas are defined in Milestone 0.")


def main() -> None:
    """Invoke the Typer application."""
    app()

