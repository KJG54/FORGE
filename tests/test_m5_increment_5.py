from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts.actors import Actor
from forge.contracts.state import InitiativeLifecycleState
from forge.contracts.verification import CheckOutcome
from forge.core.artifacts import ArtifactMutationResult, add_artifact, revise_artifact
from forge.core.authorization import owner_actor
from forge.core.continuity import (
    build_resumption_summary,
    pause_initiative,
    resume_initiative,
)
from forge.core.decisions import record_decision
from forge.core.lifecycle import (
    ActiveInitiative,
    begin_manual_run,
    create_initiative,
    load_active_initiative,
)
from forge.core.status import inspect_status
from forge.core.verification import complete_step, record_check, record_evidence
from forge.errors import ConflictError, IntegrityError
from forge.storage.canonical import canonical_json_digest
from forge.storage.repository import RepositoryLayout, initialize_repository

runner = CliRunner()


@dataclass(frozen=True)
class GovernedFixture:
    layout: RepositoryLayout
    actor: Actor
    active: ActiveInitiative
    artifacts: tuple[ArtifactMutationResult, ...]
    decision_id: UUID
    evidence_id: UUID
    evidence_digest: str


def _governed_fixture(root: Path) -> GovernedFixture:
    initialized = initialize_repository(root, owner_display_name="Continuity Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Resume one governed software initiative",
        declared_scope_summary="Canonical long-gap summary coverage",
        actor=actor,
        trust_pack_data=True,
    )
    artifacts: list[ArtifactMutationResult] = []
    for filename, role, title in (
        ("objective.md", "objective-and-constraints", "Objective and constraints"),
        ("requirements.md", "requirements", "Requirements"),
    ):
        (root / filename).write_text(f"# {title}\n\nExact governed content.\n", encoding="utf-8")
        artifacts.append(
            add_artifact(
                initialized.layout,
                path=filename,
                role=role,
                title=title,
                actor=actor,
                media_type="text/markdown",
            )
        )
    decision = record_decision(
        initialized.layout,
        decision_type="implementation-choice",
        question="Which bounded implementation should continue?",
        considered_options=("Option A", "Option B"),
        chosen_outcome="Option A",
        rationale="It preserves the accepted scope",
        actor=actor,
    )
    begin_manual_run(initialized.layout, step_id="discover", actor=actor)
    completion = complete_step(
        initialized.layout,
        step_id="discover",
        assertion="Discovery outputs are registered",
        actor=actor,
        limitations=("Owner review remains required",),
    )
    check = record_check(
        initialized.layout,
        step_id="discover",
        check_id="outputs-present",
        check_version="1",
        invocation_metadata={"method": "manual inspection"},
        outcome=CheckOutcome.PASSED,
        actor=actor,
        limitations=("This check does not accept the work",),
    )
    evidence = record_evidence(
        initialized.layout,
        step_id="discover",
        purpose="Support the exact discovery claim",
        actor=actor,
        artifact_revision_ids=tuple(item.revision.id for item in artifacts),
        check_result_ids=(check.check.id,),
        claim_ids=(completion.claim.id,),
        limitations=("Evidence remains subject to owner acceptance",),
    )
    return GovernedFixture(
        initialized.layout,
        actor,
        load_active_initiative(initialized.layout),
        tuple(artifacts),
        decision.decision.id,
        evidence.evidence.id,
        evidence.evidence.packet_digest,
    )


def test_paused_status_and_resume_share_hash_bound_canonical_summary(
    tmp_path: Path,
) -> None:
    fixture = _governed_fixture(tmp_path)
    paused = pause_initiative(
        fixture.layout,
        actor=fixture.actor,
        reason="Return after a simulated long gap",
    )

    summary = build_resumption_summary(fixture.layout)
    report = inspect_status(fixture.layout)
    assert report.resumption_summary == summary
    assert "Resuming objective: Resume one governed software initiative." in summary
    assert "Approved scope: Canonical long-gap summary coverage." in summary
    assert "Pause reason: Return after a simulated long gap." in summary
    assert "Current position: discover (awaiting_verification)" in summary
    assert "discover=awaiting_verification" in summary
    assert str(fixture.decision_id) in summary
    assert "implementation-choice" in summary
    assert "Option A" in summary
    for artifact in fixture.artifacts:
        assert str(artifact.artifact.id) in summary
        assert str(artifact.revision.id) in summary
        assert artifact.revision.path in summary
        assert artifact.revision.content_digest in summary
    assert str(fixture.evidence_id) in summary
    assert fixture.evidence_digest in summary
    assert "Next legal actions: verify:discover." in summary

    status = runner.invoke(app, ["status", "-C", str(tmp_path)])
    assert status.exit_code == 0, status.stderr
    assert f"Resumption summary: {summary}" in status.stdout

    resumed = resume_initiative(fixture.layout, actor=fixture.actor)
    assert resumed.summary == summary
    assert resumed.state.lifecycle_state is InitiativeLifecycleState.ACTIVE
    expected_digest = canonical_json_digest({"summary": summary})
    assert resumed.event.metadata["resumption_summary_profile"] == "canonical-records-v1"
    assert resumed.event.metadata["resumption_summary_digest"] == expected_digest
    assert expected_digest in resumed.event.affected_digests
    assert paused.event.id in resumed.event.affected_record_ids
    assert fixture.decision_id in resumed.event.affected_record_ids
    assert fixture.evidence_id in resumed.event.affected_record_ids
    assert load_active_initiative(fixture.layout).state == resumed.state


def test_summary_uses_current_artifact_revision_and_excludes_stale_evidence(
    tmp_path: Path,
) -> None:
    fixture = _governed_fixture(tmp_path)
    artifact = fixture.artifacts[0]
    (tmp_path / artifact.revision.path).write_text(
        "# Revised objective\n\nNew exact governed content.\n",
        encoding="utf-8",
    )
    revised = revise_artifact(
        fixture.layout,
        artifact_id=artifact.artifact.id,
        path=artifact.revision.path,
        actor=fixture.actor,
        media_type="text/markdown",
    )
    pause_initiative(
        fixture.layout,
        actor=fixture.actor,
        reason="Review the revised current artifact",
    )

    summary = build_resumption_summary(fixture.layout)
    assert str(revised.revision.id) in summary
    assert revised.revision.content_digest in summary
    assert str(artifact.revision.id) not in summary
    assert str(fixture.evidence_id) not in summary
    assert "Current evidence:\n- none" in summary
    assert "discover=invalidated" in summary


def test_canonical_resume_binding_detects_summary_tampering_and_allows_legacy_events(
    tmp_path: Path,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Compatibility Owner")
    actor = owner_actor(initialized.configuration.owner)
    created = create_initiative(
        initialized.layout,
        objective="Check resume-event compatibility",
        declared_scope_summary="Canonical and legacy resume event replay",
        actor=actor,
        trust_pack_data=True,
    )
    paused = pause_initiative(
        initialized.layout,
        actor=actor,
        reason="Compatibility test",
    )
    resumed = resume_initiative(initialized.layout, actor=actor)

    tampered = resumed.event.model_copy(
        update={
            "metadata": {
                **resumed.event.metadata,
                "resumption_summary": f"{resumed.summary} Changed after digesting.",
            }
        }
    )
    with pytest.raises(IntegrityError, match="canonical resumption summary"):
        created.active.reducer(paused.state, tampered)

    legacy_metadata = dict(resumed.event.metadata)
    del legacy_metadata["resumption_summary_profile"]
    del legacy_metadata["resumption_summary_digest"]
    legacy = resumed.event.model_copy(update={"metadata": legacy_metadata})
    legacy_state = created.active.reducer(paused.state, legacy)
    assert legacy_state.lifecycle_state is InitiativeLifecycleState.ACTIVE

    with pytest.raises(ConflictError, match="requires a paused initiative"):
        build_resumption_summary(initialized.layout)
