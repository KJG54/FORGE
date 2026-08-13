"""Pack-identity guarantees for the additive profile-aware guidance fields.

`calculate_pack_digest` hashes the parsed workflow model rather than the source
YAML bytes, so any additive field with a default still enters the digest payload
and would silently change the digest of every existing pack. The established
remedy is the empty-strip already applied to step-level `explanation_content`.

The expected digests below were captured from the repository BEFORE the guidance
fields existed. They are pinned as literals on purpose: recomputing them through
the same code path under test would make these assertions pass by construction.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from forge.contracts.workflows import InterviewGuidanceGroup, PhaseGuidance
from forge.packs.loader import load_pack
from forge.packs.validation import calculate_pack_digest

ROOT = Path(__file__).resolve().parents[1]

# Every (pack, version) identity ever published, with the digest it denotes. A version
# may never be reused for different content, so entries are append-only: to change a
# pack's content, add a new version rather than editing an existing row.
PUBLISHED_PACK_IDENTITIES = {
    ("project-basic", "0.1.0"): (
        "sha256:e9856041643c889e96ba67458176534c3fa86d69254724f1b137c1106303d1d9"
    ),
    ("software-basic", "0.5.0"): (
        "sha256:b0975cc901a91a5674eec03c33f6c1ea67ba9cc7e5eed604be71ad6f02bb5ac5"
    ),
    ("software-basic", "0.6.0"): (
        "sha256:7ef57351d571bf78fedbb115466b0f0b351addd4970909ef92e845fbc4aff962"
    ),
    ("research-basic", "0.4.0"): (
        "sha256:11ce1ee84c288a210346a9c1ff61567385ee704b6adb3498ed4e77dfd2cf37e5"
    ),
    ("forge-framework-change", "0.1.0"): (
        "sha256:6e9ab5f0cdc8e67757b3fcd8cc710936149ca8f4df3a6c81d3fc0be29e3b68f4"
    ),
    ("forge-production-release", "0.1.0"): (
        "sha256:fb23e9b8fb7692db9c277168175c18090f940b9f0a425bb27c80a1013afda497"
    ),
}

PACK_SOURCES = {
    "project-basic": "src/forge/packs/bundled/project-basic",
    "software-basic": "src/forge/packs/bundled/software-basic",
    "research-basic": "src/forge/packs/bundled/research-basic",
    "forge-framework-change": "packs/forge-framework-change",
    "forge-production-release": "packs/forge-production-release",
}

# Packs that supply no guidance. Their digests must never move.
FROZEN_PACK_DIGESTS = {
    "src/forge/packs/bundled/research-basic": (
        "0.4.0",
        "sha256:11ce1ee84c288a210346a9c1ff61567385ee704b6adb3498ed4e77dfd2cf37e5",
    ),
    "packs/forge-framework-change": (
        "0.1.0",
        "sha256:6e9ab5f0cdc8e67757b3fcd8cc710936149ca8f4df3a6c81d3fc0be29e3b68f4",
    ),
    "packs/forge-production-release": (
        "0.1.0",
        "sha256:fb23e9b8fb7692db9c277168175c18090f940b9f0a425bb27c80a1013afda497",
    ),
}


def test_packs_without_guidance_keep_their_pre_change_digests() -> None:
    for relative_path, (version, expected_digest) in FROZEN_PACK_DIGESTS.items():
        pack = load_pack(ROOT / relative_path)

        assert pack.manifest.version == version, relative_path
        calculated = calculate_pack_digest(pack.manifest, pack.workflows, pack.resources)

        assert calculated == expected_digest, (
            f"{relative_path} digest moved. An additive guidance field most likely "
            f"entered the digest payload without an empty-strip in "
            f"calculate_pack_digest."
        )
        assert calculated == pack.manifest.integrity_digest, relative_path


def test_archived_pack_locks_still_validate_against_their_recorded_digests() -> None:
    lock_paths = sorted((ROOT / ".forge" / "archive").glob("*/pack.lock.json"))

    assert lock_paths, "expected at least one archived pack lock to guard"
    guarded = 0

    for lock_path in lock_paths:
        locked = json.loads(lock_path.read_text(encoding="utf-8"))
        recorded_digest = locked["integrity_digest"]
        pack_id = locked["id"]

        source = next(
            (
                candidate
                for candidate in (
                    ROOT / "packs" / pack_id,
                    ROOT / "src" / "forge" / "packs" / "bundled" / pack_id,
                )
                if candidate.is_dir()
            ),
            None,
        )
        if source is None:
            continue

        pack = load_pack(source)
        if pack.manifest.version != locked["version"]:
            continue

        calculated = calculate_pack_digest(pack.manifest, pack.workflows, pack.resources)
        guarded += 1

        assert calculated == recorded_digest, (
            f"{lock_path} pins {recorded_digest} for {pack_id} "
            f"{locked['version']}, but the current source calculates "
            f"{calculated}. Archived locks would stop validating."
        )

    assert guarded, "no archived lock was actually compared; the guard would be vacuous"


def _sample_phase_guidance() -> PhaseGuidance:
    return PhaseGuidance(
        label="Define the first milestone",
        owner_tasks=("Decide the intended users and the first useful outcome.",),
        agent_tasks=("Turn owner answers into a bounded proposal.",),
        either_tasks=("Gather examples, notes, or reference links.",),
        owner_only_gates=("Authorize the exact initiative-creation command.",),
        done_signal="The owner confirms the playback and open questions are answered or accepted.",
    )


def _sample_interview_guidance() -> InterviewGuidanceGroup:
    return InterviewGuidanceGroup(
        purpose="Understand the human goal, intended users, and learning goals.",
        questions=(
            "What are you trying to build or learn?",
            "Who is this for?",
        ),
        must_answer_before_create=("intended-users",),
    )


def test_supplied_guidance_participates_in_the_digest_and_round_trips() -> None:
    # research-basic supplies no guidance, so it isolates the effect of adding some.
    pack = load_pack(ROOT / "src" / "forge" / "packs" / "bundled" / "research-basic")
    workflow = pack.workflow()
    baseline = calculate_pack_digest(pack.manifest, pack.workflows, pack.resources)

    guided_workflow = workflow.model_copy(
        update={
            "steps": (
                workflow.steps[0].model_copy(
                    update={"phase_guidance": _sample_phase_guidance()}
                ),
                *workflow.steps[1:],
            ),
            "interview_guidance": {"vision": _sample_interview_guidance()},
        }
    )

    guided_digest = calculate_pack_digest(
        pack.manifest, (guided_workflow,), pack.resources
    )

    # The strip must not make guidance inert: supplied content has to move the digest,
    # otherwise two materially different packs would share one identity.
    assert guided_digest != baseline

    first_step = guided_workflow.steps[0]
    assert first_step.phase_guidance is not None
    assert first_step.phase_guidance.label == "Define the first milestone"
    assert first_step.phase_guidance.owner_only_gates == (
        "Authorize the exact initiative-creation command.",
    )
    assert guided_workflow.steps[1].phase_guidance is None
    assert guided_workflow.interview_guidance["vision"].must_answer_before_create == (
        "intended-users",
    )


def test_phase_guidance_and_step_guidance_move_the_digest_independently() -> None:
    pack = load_pack(ROOT / "src" / "forge" / "packs" / "bundled" / "research-basic")
    workflow = pack.workflow()

    step_only = workflow.model_copy(
        update={
            "steps": (
                workflow.steps[0].model_copy(
                    update={"phase_guidance": _sample_phase_guidance()}
                ),
                *workflow.steps[1:],
            )
        }
    )
    workflow_only = workflow.model_copy(
        update={"interview_guidance": {"vision": _sample_interview_guidance()}}
    )

    digests = {
        calculate_pack_digest(pack.manifest, (step_only,), pack.resources),
        calculate_pack_digest(pack.manifest, (workflow_only,), pack.resources),
        calculate_pack_digest(pack.manifest, pack.workflows, pack.resources),
    }

    assert len(digests) == 3, "each guidance scope must be independently distinguishable"


def test_malformed_guidance_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PhaseGuidance(label="")

    with pytest.raises(ValidationError):
        InterviewGuidanceGroup(
            purpose="Understand the goal.",
            must_answer_before_create=("Not An Id",),
        )

    # Validated from a mapping so the deliberately unknown key is a runtime concern
    # rather than a static one; the contract forbids extra fields.
    with pytest.raises(ValidationError):
        PhaseGuidance.model_validate({"label": "Valid label", "unexpected_field": "x"})


def test_no_pack_version_is_reused_for_different_content() -> None:
    for pack_id, source in PACK_SOURCES.items():
        pack = load_pack(ROOT / source)
        version = pack.manifest.version
        identity = (pack_id, version)

        assert identity in PUBLISHED_PACK_IDENTITIES, (
            f"{pack_id} is now at {version}, which has no recorded identity. Add the new "
            f"(version, digest) row rather than editing an existing one."
        )
        calculated = calculate_pack_digest(pack.manifest, pack.workflows, pack.resources)

        assert calculated == PUBLISHED_PACK_IDENTITIES[identity], (
            f"{pack_id} {version} previously denoted "
            f"{PUBLISHED_PACK_IDENTITIES[identity]} but now calculates {calculated}. "
            f"A published version must never denote different content; bump the version."
        )


def test_project_basic_guidance_is_complete_and_presentation_only() -> None:
    pack = load_pack(ROOT / "src" / "forge" / "packs" / "bundled" / "project-basic")
    workflow = pack.workflow()

    assert set(workflow.explanation_content) == {
        "minimal",
        "standard",
        "guided",
        "mentored",
    }
    assert len(workflow.interview_guidance) == 4
    assert all(step.phase_guidance is not None for step in workflow.steps)
    assert [step.id for step in workflow.steps] == [
        "intake",
        "research",
        "plan",
        "create",
        "evaluate",
        "review",
        "close",
    ]
    assert workflow.steps[3].required_outputs == ("created-work",)
    assert workflow.steps[4].required_inputs == ("created-work", "acceptance-criteria")
    assert all(
        step.allowed_transitions == ("begin", "rework", "submit", "verify", "accept")
        and step.acceptance_requirements == ("owner-acceptance",)
        for step in workflow.steps
    )

def test_software_basic_supplies_guidance_for_every_step_and_coverage_area() -> None:
    pack = load_pack(ROOT / "src" / "forge" / "packs" / "bundled" / "software-basic")
    workflow = pack.workflow()

    assert set(workflow.interview_guidance) == {
        "vision",
        "first_milestone",
        "risks_and_constraints",
        "learning_path",
    }
    assert workflow.interview_guidance["vision"].must_answer_before_create == (
        "intended-users",
        "first-useful-outcome",
    )

    for step in workflow.steps:
        guidance = step.phase_guidance
        assert guidance is not None, f"step {step.id} has no phase guidance"
        assert guidance.label, step.id
        assert guidance.done_signal, step.id
        assert guidance.owner_tasks, step.id
        assert guidance.agent_tasks, step.id
        # Every step in this workflow ends in owner acceptance, so each phase must name
        # at least one owner-only gate or the task map would understate authority.
        assert guidance.owner_only_gates, step.id


def test_guidance_does_not_alter_workflow_authority() -> None:
    """Guidance is presentation. It must not change any governed step property."""
    pack = load_pack(ROOT / "src" / "forge" / "packs" / "bundled" / "software-basic")
    workflow = pack.workflow()

    for step in workflow.steps:
        assert step.acceptance_requirements == ("owner-acceptance",), step.id
        assert step.allowed_transitions == (
            "begin",
            "rework",
            "submit",
            "verify",
            "accept",
        ), step.id

    accept = next(item for item in workflow.transitions if item.id == "accept")
    assert accept.authority_requirement == "owner"
    verify = next(item for item in workflow.transitions if item.id == "verify")
    assert verify.authority_requirement == "forge-cli"
