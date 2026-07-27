import json
from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.local_audit import (
    LocalAuditCategory,
    LocalAuditEvent,
    LocalAuditSeverity,
)
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative
from forge.core.local_audit import (
    list_local_audit_events,
    record_local_audit_event,
    show_local_audit_event,
)
from forge.errors import AuthorizationError, IntegrityError, SecurityError, TransitionError
from forge.storage.canonical import sha256_digest
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> InitializationResult:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    create_initiative(
        initialized.layout,
        objective="Exercise structured local auditing",
        declared_scope_summary="Record sanitized CLI failures without workflow authority",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
    )
    return initialized


def test_cli_security_refusal_records_sanitized_local_event(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    journal_before = initialized.layout.event_journal_file.read_bytes()
    unsafe_path = "../outside-secret-name.txt"

    refused = runner.invoke(
        app,
        [
            "artifact",
            "add",
            unsafe_path,
            "--role",
            "requirements",
            "--title",
            "Unsafe traversal",
            "-C",
            str(tmp_path),
        ],
    )

    assert refused.exit_code == 40, refused.output
    assert "Unsafe repository path" in refused.output
    events = list_local_audit_events(initialized.layout)
    assert len(events) == 1
    event = events[0]
    assert event.project_id == initialized.configuration.project_id
    assert event.initiative_id is not None
    assert event.configured_owner_id == initialized.configuration.owner.id
    assert event.operation == "artifact add"
    assert event.category is LocalAuditCategory.SECURITY
    assert event.severity is LocalAuditSeverity.ERROR
    assert event.outcome == "refused"
    assert event.exit_code == 40
    assert event.error_type == "SecurityError"
    displayed_error = next(
        line.removeprefix("Error: ")
        for line in refused.output.splitlines()
        if line.startswith("Error: ")
    )
    assert event.detail_digest == sha256_digest(displayed_error.encode())
    stored = (
        initialized.layout.local_audit_event_directory / f"{event.id}.json"
    ).read_text(encoding="utf-8")
    assert unsafe_path not in stored
    assert "Unsafe repository path" not in stored
    assert initialized.layout.event_journal_file.read_bytes() == journal_before

    listed = runner.invoke(app, ["audit", "list", "-C", str(tmp_path)])
    assert listed.exit_code == 0, listed.output
    assert str(event.id) in listed.output
    assert "category=security" in listed.output
    shown = runner.invoke(
        app,
        ["audit", "show", str(event.id), "-C", str(tmp_path)],
    )
    assert shown.exit_code == 0, shown.output
    assert f"Detail digest: {event.detail_digest}" in shown.output
    assert unsafe_path not in shown.output
    doctor = runner.invoke(app, ["doctor", "-C", str(tmp_path)])
    assert doctor.exit_code == 0, doctor.output
    assert "local audit events (1)" in doctor.output


def test_local_audit_categories_filter_and_records_are_immutable(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    authorization = record_local_audit_event(
        initialized.layout,
        operation="acceptance record",
        error=AuthorizationError("Actor cannot record owner acceptance"),
    )
    transition = record_local_audit_event(
        initialized.layout,
        operation="complete",
        error=TransitionError("Claim cannot bypass required checks"),
    )

    selected = list_local_audit_events(
        initialized.layout,
        category=LocalAuditCategory.AUTHORIZATION,
    )
    assert selected == (authorization,)
    assert show_local_audit_event(initialized.layout, transition.id) == transition
    assert authorization.severity is LocalAuditSeverity.WARNING
    assert transition.severity is LocalAuditSeverity.NOTICE

    path = initialized.layout.local_audit_event_directory / f"{authorization.id}.json"
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        path.open("xb").close()
    assert path.read_bytes() == original


def test_local_audit_inventory_tamper_is_diagnostic_not_governance(
    tmp_path: Path,
) -> None:
    initialized = _initiative(tmp_path)
    event = record_local_audit_event(
        initialized.layout,
        operation="status",
        error=IntegrityError("State snapshot did not match replay"),
    )
    path = initialized.layout.local_audit_event_directory / f"{event.id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["detail_digest"] = "not-a-digest"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(IntegrityError, match="Invalid local audit event"):
        list_local_audit_events(initialized.layout)
    active_journal = initialized.layout.event_journal_file.read_bytes()
    failed = runner.invoke(app, ["audit", "list", "-C", str(tmp_path)])
    assert failed.exit_code == 30, failed.output
    assert "Invalid local audit event" in failed.output
    assert initialized.layout.event_journal_file.read_bytes() == active_journal


def test_local_audit_failure_never_masks_original_cli_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _initiative(tmp_path)

    def fail_audit(*_args: object, **_kwargs: object) -> LocalAuditEvent:
        raise SecurityError("simulated unavailable local audit storage")

    monkeypatch.setattr("forge.cli.app.record_local_audit_event", fail_audit)
    unknown = uuid4()
    result = runner.invoke(
        app,
        ["run", "show", str(unknown), "-C", str(tmp_path)],
    )
    assert result.exit_code == 31, result.output
    assert f"Unknown run {unknown}" in result.output
