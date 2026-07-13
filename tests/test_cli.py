from pathlib import Path

from typer.testing import CliRunner

from forge import __version__
from forge.cli.app import app
from forge.contracts import CONTRACT_MODELS

runner = CliRunner()


def test_help_runs() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "govern" in result.stdout.lower()


def test_version_runs() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_schema_export_writes_versioned_contracts(tmp_path: Path) -> None:
    output = tmp_path / "schemas"
    result = runner.invoke(app, ["schema", "export", "--output", str(output)])
    assert result.exit_code == 0
    assert f"Exported {len(CONTRACT_MODELS)} contract schemas" in result.stdout
    assert (output / "index.json").is_file()


def test_init_and_config_commands(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--owner-name", "Repository Owner"])
    assert result.exit_code == 0, result.stdout
    assert "Initialized FORGE repository" in result.stdout

    validated = runner.invoke(app, ["config", "validate", "-C", str(tmp_path)])
    assert validated.exit_code == 0, validated.stdout
    assert "Valid FORGE configuration 1.0" in validated.stdout

    shown = runner.invoke(app, ["config", "show", "-C", str(tmp_path)])
    assert shown.exit_code == 0, shown.stdout
    assert "display_name: Repository Owner" in shown.stdout


def test_init_reports_conflict_without_traceback(tmp_path: Path) -> None:
    (tmp_path / ".forge").mkdir()
    (tmp_path / ".forge" / "existing").write_text("content", encoding="utf-8")
    result = runner.invoke(app, ["init", str(tmp_path), "--owner-name", "Owner"])
    assert result.exit_code == 31
    assert "Refusing to adopt" in result.stderr
    assert "Traceback" not in result.stderr
