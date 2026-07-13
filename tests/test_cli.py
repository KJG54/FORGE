from typer.testing import CliRunner

from forge import __version__
from forge.cli.app import app

runner = CliRunner()


def test_help_runs() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "govern" in result.stdout.lower()


def test_version_runs() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_schema_export_placeholder_is_callable() -> None:
    result = runner.invoke(app, ["schema", "export"])
    assert result.exit_code == 0
    assert "Milestone 0" in result.stdout

