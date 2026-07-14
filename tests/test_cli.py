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


def test_pack_create_status_next_and_begin_commands(tmp_path: Path) -> None:
    initialized = runner.invoke(
        app,
        ["init", str(tmp_path), "--owner-name", "Repository Owner"],
    )
    assert initialized.exit_code == 0, initialized.stdout

    listed = runner.invoke(app, ["pack", "list", "-C", str(tmp_path)])
    assert listed.exit_code == 0, listed.stdout
    assert "software-basic 0.1.0" in listed.stdout
    validated = runner.invoke(
        app,
        ["pack", "validate", "software-basic", "-C", str(tmp_path)],
    )
    assert validated.exit_code == 0, validated.stdout
    assert "Valid data pack software-basic" in validated.stdout

    refused = runner.invoke(
        app,
        ["create", "Objective", "--scope", "Bounded scope", "-C", str(tmp_path)],
    )
    assert refused.exit_code == 20
    assert "explicit owner confirmation" in refused.stderr

    invalid = runner.invoke(
        app,
        [
            "create",
            " ",
            "--scope",
            "Bounded scope",
            "--trust-pack-data",
            "-C",
            str(tmp_path),
        ],
    )
    assert invalid.exit_code == 10
    assert "objective must not be empty" in invalid.stderr

    created = runner.invoke(
        app,
        [
            "create",
            "Objective",
            "--scope",
            "Bounded scope",
            "--trust-pack-data",
            "-C",
            str(tmp_path),
        ],
    )
    assert created.exit_code == 0, created.stdout
    assert "Next: begin:discover" in created.stdout

    next_result = runner.invoke(app, ["next", "-C", str(tmp_path)])
    assert next_result.exit_code == 0, next_result.stdout
    assert next_result.stdout.strip() == "begin:discover"

    begun = runner.invoke(app, ["begin", "discover", "-C", str(tmp_path)])
    assert begun.exit_code == 0, begun.stdout
    assert "Started manual run" in begun.stdout
    assert "separate from checks, evidence, and owner acceptance" in begun.stdout

    status = runner.invoke(app, ["status", "-C", str(tmp_path)])
    assert status.exit_code == 0, status.stdout
    assert "Integrity: healthy" in status.stdout
    assert "Step discover: in_progress" in status.stdout
    assert "Active run:" in status.stdout
    assert "Next: complete:discover" in status.stdout
