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
    assert "forge agent protocol" in result.stdout


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
    assert "Next: workspace agents run forge agent protocol and follow it" in result.stdout

    rerun = runner.invoke(app, ["init", str(tmp_path), "--owner-name", "Repository Owner"])
    assert rerun.exit_code == 0, rerun.stdout
    assert "Already initialized FORGE repository" in rerun.stdout
    assert "Next: workspace agents run forge agent protocol and follow it" in rerun.stdout

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


def test_bundled_pack_inspection_works_before_initialization(tmp_path: Path) -> None:
    listed = runner.invoke(app, ["pack", "list", "-C", str(tmp_path)])

    assert listed.exit_code == 0, listed.stdout
    assert "Repository: uninitialized" in listed.stdout
    assert "software-basic 0.5.0 (bundled" in listed.stdout

    inspected = runner.invoke(
        app,
        ["pack", "inspect", "software-basic", "-C", str(tmp_path)],
    )

    assert inspected.exit_code == 0, inspected.stdout
    assert "Pack: software-basic@0.5.0 (bundled" in inspected.stdout
    assert "- discover: required_inputs=none" in inspected.stdout
    assert "required_outputs=objective-and-constraints, requirements" in inspected.stdout
    assert "Valid scope-amendment requirement IDs:" in inspected.stdout
    assert "  - requirements" in inspected.stdout
    assert not (tmp_path / "forge.yaml").exists()
    assert not (tmp_path / ".forge").exists()


def test_pack_create_status_next_and_begin_commands(tmp_path: Path) -> None:
    initialized = runner.invoke(
        app,
        ["init", str(tmp_path), "--owner-name", "Repository Owner"],
    )
    assert initialized.exit_code == 0, initialized.stdout

    listed = runner.invoke(app, ["pack", "list", "-C", str(tmp_path)])
    assert listed.exit_code == 0, listed.stdout
    assert "software-basic 0.5.0" in listed.stdout
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
    assert "Recorded -> initiative-created" in created.stdout
    assert "legal_actions=begin:discover" in created.stdout

    next_result = runner.invoke(app, ["next", "-C", str(tmp_path)])
    assert next_result.exit_code == 0, next_result.stdout
    assert next_result.stdout.strip() == "begin:discover"

    begun = runner.invoke(app, ["begin", "discover", "-C", str(tmp_path)])
    assert begun.exit_code == 0, begun.stdout
    assert "Recorded -> step-transitioned" in begun.stdout
    assert "step=discover:in_progress" in begun.stdout
    _line_value(begun.stdout, "Started manual run ")

    status = runner.invoke(app, ["status", "-C", str(tmp_path)])
    assert status.exit_code == 0, status.stdout
    assert "Integrity: healthy" in status.stdout
    assert "Step discover: in_progress" in status.stdout
    assert "Active run:" in status.stdout
    assert "Legal next: complete:discover" in status.stdout
    assert "Ready now: artifact-add:objective-and-constraints" in status.stdout
    assert "Ready now: artifact-add:requirements" in status.stdout
    assert "cannot complete until required artifact roles" in status.stdout


def _line_value(output: str, prefix: str) -> str:
    legacy = next(
        (line.removeprefix(prefix) for line in output.splitlines() if line.startswith(prefix)),
        None,
    )
    if legacy is not None:
        return legacy
    receipt_fields = {
        "Revision ID: ": "revision_id",
        "Recorded claim ": "claim_id",
        "Recorded check result ": "check_result_id",
        "Recorded owner acceptance ": "acceptance_id",
        "Started manual run ": "run_id",
    }
    marker = f"{receipt_fields[prefix]}="
    value = output.split(marker, 1)[1]
    return value.split(";", 1)[0].split(")", 1)[0]


def test_artifact_claim_check_evidence_and_verify_commands(tmp_path: Path) -> None:
    assert (
        runner.invoke(
            app,
            ["init", str(tmp_path), "--owner-name", "Repository Owner"],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
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
        ).exit_code
        == 0
    )
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
    assert "legal_actions=verify:discover" in completed.stdout
    assert "ready_actions=check-record:discover:outputs-present" in completed.stdout
    assert "required checks pass for current artifact revisions" in completed.stdout
    claim_id = _line_value(completed.stdout, "Recorded claim ")

    status = runner.invoke(app, ["status", "-C", str(tmp_path)])
    next_result = runner.invoke(app, ["next", "-C", str(tmp_path)])
    recap = runner.invoke(app, ["recap", "-C", str(tmp_path)])
    assert "Legal next: verify:discover" in status.stdout
    assert "Ready now: check-record:discover:outputs-present" in status.stdout
    assert "check-record:discover:outputs-present" in next_result.stdout
    assert "Legal after prerequisites: verify:discover" in next_result.stdout
    assert "Executable now:\n- check-record:discover:outputs-present" in recap.stdout
    assert "Legal next actions:\n- verify:discover" in recap.stdout

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
    assert "legal_actions=verify:discover" in checked.stdout
    assert "ready_actions=evidence-add:discover" in checked.stdout
    assert "evidence binds current artifacts, passing checks, and claim" in checked.stdout
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
    assert "Recorded -> evidence-registered" in evidenced.stdout
    assert "legal_actions=verify:discover" in evidenced.stdout
    assert "ready_actions=verify:discover" in evidenced.stdout

    verified = runner.invoke(app, ["verify", "discover", "-C", str(tmp_path)])
    assert verified.exit_code == 0, verified.stdout
    assert "step=discover:awaiting_acceptance" in verified.stdout
    assert "legal_actions=acceptance-record:discover" in verified.stdout

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
    assert "acceptance-recorded" in accepted.stdout
    assert "step=plan:ready" in accepted.stdout

    shown = runner.invoke(app, ["acceptance", "show", acceptance_id, "-C", str(tmp_path)])
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
    assert "Recorded -> decision-recorded" in decided.stdout

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
