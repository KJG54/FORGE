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
    assert "software-basic 0.2.0" in listed.stdout
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


def _line_value(output: str, prefix: str) -> str:
    return next(
        line.removeprefix(prefix)
        for line in output.splitlines()
        if line.startswith(prefix)
    )


def test_artifact_claim_check_evidence_and_verify_commands(tmp_path: Path) -> None:
    assert runner.invoke(
        app,
        ["init", str(tmp_path), "--owner-name", "Repository Owner"],
    ).exit_code == 0
    assert runner.invoke(
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
    ).exit_code == 0
    assert runner.invoke(app, ["begin", "discover", "-C", str(tmp_path)]).exit_code == 0
    (tmp_path / "objective.md").write_text("Objective", encoding="utf-8")
    (tmp_path / "requirements.md").write_text("Requirements", encoding="utf-8")

    objective = runner.invoke(
        app,
        [
            "artifact",
            "add",
            "objective.md",
            "--role",
            "objective-and-constraints",
            "--title",
            "Objective",
            "-C",
            str(tmp_path),
        ],
    )
    requirements = runner.invoke(
        app,
        [
            "artifact",
            "add",
            "requirements.md",
            "--role",
            "requirements",
            "--title",
            "Requirements",
            "-C",
            str(tmp_path),
        ],
    )
    assert objective.exit_code == 0, objective.stdout
    assert requirements.exit_code == 0, requirements.stdout
    revision_ids = (
        _line_value(objective.stdout, "Revision ID: "),
        _line_value(requirements.stdout, "Revision ID: "),
    )

    invalid_claim = runner.invoke(
        app,
        ["complete", "discover", "--assertion", " ", "-C", str(tmp_path)],
    )
    assert invalid_claim.exit_code == 10
    assert "Claim assertion must not be empty" in invalid_claim.stderr
    assert "Traceback" not in invalid_claim.stderr

    completed = runner.invoke(
        app,
        [
            "complete",
            "discover",
            "--assertion",
            "Discovery outputs produced",
            "-C",
            str(tmp_path),
        ],
    )
    assert completed.exit_code == 0, completed.stdout
    claim_id = _line_value(completed.stdout, "Recorded claim ")

    checked = runner.invoke(
        app,
        [
            "check",
            "record",
            "discover",
            "outputs-present",
            "--invocation",
            "manual file review",
            "--outcome",
            "passed",
            "--exit-status",
            "0",
            "-C",
            str(tmp_path),
        ],
    )
    assert checked.exit_code == 0, checked.stdout
    check_id = _line_value(checked.stdout, "Recorded check result ").split(":", 1)[0]

    evidenced = runner.invoke(
        app,
        [
            "evidence",
            "add",
            "discover",
            "--purpose",
            "Support the output check",
            "--artifact-revision",
            revision_ids[0],
            "--artifact-revision",
            revision_ids[1],
            "--check-result",
            check_id,
            "--claim",
            claim_id,
            "--limitation",
            "Owner acceptance remains required",
            "-C",
            str(tmp_path),
        ],
    )
    assert evidenced.exit_code == 0, evidenced.stdout
    assert "does not automatically establish truth" in evidenced.stdout

    verified = runner.invoke(app, ["verify", "discover", "-C", str(tmp_path)])
    assert verified.exit_code == 0, verified.stdout
    assert "Step discover: awaiting_acceptance" in verified.stdout
    assert "forge acceptance record discover" in verified.stdout

    accepted = runner.invoke(
        app,
        [
            "acceptance",
            "record",
            "discover",
            "--scope",
            "Discovery outputs",
            "--known-limitation",
            "Presence check only",
            "-C",
            str(tmp_path),
        ],
    )
    assert accepted.exit_code == 0, accepted.stdout
    acceptance_id = _line_value(accepted.stdout, "Recorded owner acceptance ")
    assert "Step discover: completed" in accepted.stdout

    shown = runner.invoke(
        app, ["acceptance", "show", acceptance_id, "-C", str(tmp_path)]
    )
    assert shown.exit_code == 0, shown.stdout
    assert "status=current" in shown.stdout

    decided = runner.invoke(
        app,
        [
            "decide",
            "--type",
            "scope-choice",
            "--question",
            "Proceed?",
            "--option",
            "Yes",
            "--option",
            "No",
            "--outcome",
            "Yes",
            "--rationale",
            "Evidence is sufficient",
            "-C",
            str(tmp_path),
        ],
    )
    assert decided.exit_code == 0, decided.stdout
    assert "Recorded decision" in decided.stdout

    revoked = runner.invoke(
        app,
        [
            "acceptance",
            "revoke",
            acceptance_id,
            "--reason",
            "Requirements changed",
            "-C",
            str(tmp_path),
        ],
    )
    assert revoked.exit_code == 0, revoked.stdout
    status = runner.invoke(app, ["status", "-C", str(tmp_path)])
    assert status.exit_code == 0, status.stdout
    assert "Step discover: invalidated" in status.stdout
    assert f"Stale record: {acceptance_id}" in status.stdout
