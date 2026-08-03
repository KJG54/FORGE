from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import ActorType, OperatorType
from forge.contracts.artifacts import ArtifactRevision
from forge.contracts.verification import (
    CheckOutcome,
    Claim,
    claim_digest_payload,
)
from forge.core.agent_protocol import load_agent_protocol
from forge.core.artifacts import add_artifact
from forge.core.authorization import owner_actor
from forge.core.lifecycle import begin_manual_run, create_initiative
from forge.core.owner_ceremony import owner_action_presentation
from forge.core.verification import complete_step, record_check, record_evidence, verify_step
from forge.storage.journal import read_journal
from forge.storage.objects import canonical_json_digest
from forge.storage.records import load_record
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _in_progress(
    tmp_path: Path,
) -> tuple[InitializationResult, tuple[ArtifactRevision, ...]]:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Deliver governed discovery outputs",
        declared_scope_summary="Discovery only",
        actor=actor,
        trust_pack_data=True,
    )
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    revisions: list[ArtifactRevision] = []
    for filename, role in (
        ("objective.md", "objective-and-constraints"),
        ("requirements.md", "requirements"),
    ):
        (tmp_path / filename).write_text(role, encoding="utf-8")
        result = add_artifact(
            initialized.layout,
            path=filename,
            role=role,
            title=role,
            actor=actor,
        )
        revisions.append(result.revision)
    return initialized, tuple(revisions)


def test_direct_agent_claim_separates_authority_operator_and_session(
    tmp_path: Path,
) -> None:
    initialized, _ = _in_progress(tmp_path)

    completed = runner.invoke(
        app,
        [
            "complete",
            "discover",
            "--assertion",
            "Discovery outputs are ready",
            "--operator",
            "direct-codex",
            "--session-reference",
            "codex-task-l6",
            "-C",
            str(tmp_path),
        ],
    )

    assert completed.exit_code == 0, completed.output
    assert "actor_type=owner" in completed.stdout
    assert "operator_type=direct-codex" in completed.stdout
    assert "operator_attribution=caller-declared-not-authentication" in completed.stdout
    assert 'operator_session_reference="codex-task-l6"' in completed.stdout
    claim_event = next(
        event
        for event in read_journal(initialized.layout.event_journal_file)
        if event.event_type == "claim-recorded"
    )
    claim_id = claim_event.metadata["claim_id"]
    claim = load_record(initialized.layout.claim_directory / f"{claim_id}.json", Claim)
    assert claim.actor.actor_type is ActorType.OWNER
    assert claim.operator_type is OperatorType.DIRECT_CODEX
    assert claim.operator_session_reference == "codex-task-l6"

    history = runner.invoke(app, ["history", "-C", str(tmp_path)])
    assert history.exit_code == 0, history.output
    assert "actor=owner:" in history.stdout
    assert "operator=direct-codex" in history.stdout
    assert "operator-session=codex-task-l6" in history.stdout


def test_new_claim_defaults_to_owner_shell_and_legacy_digest_shape_is_stable(
    tmp_path: Path,
) -> None:
    initialized, _ = _in_progress(tmp_path)
    actor = owner_actor(initialized.configuration.owner)
    completed = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Owner-shell completion",
        actor=actor,
    )

    assert completed.claim.actor.actor_type is ActorType.OWNER
    assert completed.claim.operator_type is OperatorType.OWNER_SHELL
    stored = load_record(
        initialized.layout.claim_directory / f"{completed.claim.id}.json",
        Claim,
    )
    assert stored.operator_type is OperatorType.OWNER_SHELL

    legacy_payload = completed.claim.model_dump(mode="json")
    legacy_payload.pop("operator_type")
    legacy_payload.pop("operator_session_reference")
    legacy_claim = Claim.model_validate(legacy_payload)

    assert legacy_claim.operator_type is None
    assert legacy_claim.operator_session_reference is None
    assert claim_digest_payload(legacy_claim) == legacy_payload
    assert canonical_json_digest(claim_digest_payload(legacy_claim)) == canonical_json_digest(
        legacy_payload
    )


def test_owner_gate_is_exact_in_next_and_receipt(tmp_path: Path) -> None:
    initialized, revisions = _in_progress(tmp_path)
    actor = owner_actor(initialized.configuration.owner)
    claim = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Discovery outputs are ready",
        actor=actor,
        operator_type=OperatorType.DIRECT_CLAUDE,
    )
    check = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"invocation": "manual review"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
        exit_status=0,
    )
    record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Bind exact discovery support",
        actor=actor,
        artifact_revision_ids=tuple(revision.id for revision in revisions),
        check_result_ids=(check.check.id,),
        claim_ids=(claim.claim.id,),
    )
    verify_step(initialized.layout, step_id="discover")

    next_result = runner.invoke(app, ["next", "-C", str(tmp_path)])

    assert next_result.exit_code == 0, next_result.output
    assert "Owner action: acceptance-record:discover" in next_result.stdout
    assert (
        'Owner command: forge acceptance record discover --scope "<exact-accepted-scope>"'
        in next_result.stdout
    )
    assert "exact current revisions, checks, evidence" in next_result.stdout
    assert "caller attribution is not authentication" in next_result.stdout


def test_protocol_and_runtime_templates_cover_consequential_owner_paths() -> None:
    protocol = load_agent_protocol().content.decode("utf-8")
    for command in (
        "forge init <repository> --owner-name <display-name>",
        "forge pack trust <pack-id>",
        "forge acceptance revoke <acceptance-uuid>",
        "--operator direct-codex",
        "--operator direct-claude",
        "forge pause --reason",
        "forge resume",
        "forge decide --type",
        "forge scope amend --scope",
        "forge deviation review <deviation-uuid>",
        "forge capability approve <capability-id>",
        "forge risk accept <override-uuid>",
        "forge recover --reason",
        "forge migrate --apply",
        "forge close --summary",
        "forge abandon --reason",
    ):
        assert command in protocol
    assert "Caller attribution is not authentication" in protocol
    assert "governed artifact revision and recursive" in protocol
    assert "owner scope amendment with an explicit return step" in protocol
    assert "append-only disposition" in protocol

    for action in (
        "create",
        "create-successor",
        "acceptance-record:discover",
        "pack-trust:software-basic",
        "deviation-review:00000000-0000-0000-0000-000000000001",
        "risk-accept:00000000-0000-0000-0000-000000000002",
        "resume",
        "migrate",
        "close",
        "abandon",
    ):
        presentation = owner_action_presentation(action)
        assert presentation is not None
        assert presentation.command.startswith("forge ")
        assert presentation.consequence
    assert owner_action_presentation("begin:discover") is None
