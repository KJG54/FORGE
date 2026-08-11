# Profile-Aware Facilitation — Framework Changes

Initiative: `fb1e3732-334f-4bb1-9e51-40dad0e9521b`
Step: `implement` — required output role `framework-changes`
Branch: `feature/profile-aware-facilitation`

This artifact declares what the implementation changed. It is a registered project
artifact, not a check, evidence, verification, or acceptance. Nothing here has been
verified; `verify-release` evaluates the criteria in
`release/profile-aware-facilitation/release-requirements.md` against one exact revision.

## Commits

| Commit | Change |
|---|---|
| `1e1ef4d` | Guidance contract fields and digest neutrality |
| `4b02f5e` | Agent protocol 1.4.0 as a strict superset of 1.3.0 |
| `63f3f59` | `software-basic` 0.6.0 interview and phase guidance |
| `697aa24` | Agent protocol skew detection in `forge doctor` |
| `1deb9f9` | Starter prompts aligned with 1.4.0; no-active-initiative first contact |
| `2614479` | Guidance, phase, and direct-workspace-use documentation |
| `458de34` | Superseded protocol copy removal; managed references regenerated |

## Contract changes

`InterviewGuidanceGroup` (workflow scope) and `PhaseGuidance` (step scope) are additive,
default-empty fields on the pack workflow contract. `interview_guidance` groups
pre-initiative questions with an optional `must_answer_before_create` list.
`phase_guidance` carries a label, owner tasks, agent tasks, either-party tasks,
`owner_only_gates`, and a done signal.

Both are presentation. `owner_only_gates` restates gates that already exist so an agent can
name them in a task map; it creates no gate, satisfies none, waives no check, and alters no
acceptance. A test asserts guidance leaves `acceptance_requirements`, `allowed_transitions`,
and transition authority unchanged.

Both models are registered in `CONTRACT_MODELS`, following the `Gate` precedent for nested
workflow models. The public model count moved 51 → 53 in `release/version-contract.json`,
`release/installation-matrix.json`, the frozen contract test, and the `forge-contracts-1`
compatibility manifest as a baseline labelled `profile-aware-facilitation`.

## Digest neutrality

`calculate_pack_digest()` hashes the parsed workflow model, not the source YAML, so a
default-valued field enters the payload and changes every pack digest. Verified before the
strip existed: `forge-framework-change` 0.1.0 moved from `sha256:6e9ab5f0…3b68f4` to
`sha256:edcd0600…1b2a79`, and `6e9ab5f0…` is the value pinned in the archived
`pack.lock.json` of archives `26c0c628` and `ace6c2c9`. Unguarded, the change would have
invalidated existing archived locks.

Both fields are therefore stripped from the digest payload when empty, following the pattern
already established for step-level `explanation_content`. Packs supplying no guidance keep
their exact prior digests.

## Protocol 1.4.0

Generated from the exact 1.3.0 bytes so every prior line survives verbatim; only the version
declaration differs. Added: FORGE identification against unrelated `forge` tools, protocol
version-skew reconciliation, the four-profile collaboration and learning table, small
question batches with examples for open-ended beginner questions, must-answer-now separated
from acceptable uncertainty, phase openings and closings, and a four-way collaboration task
map.

Two statements are normative and enforced as required fragments in `load_agent_protocol()`:
profiles never change authority, required inputs, checks, evidence, acceptance, or any owner
gate; and a task map is presentation that never redefines authority.

1.3.0 remains shipped via `SUPERSEDED_AGENT_PROTOCOL_VERSIONS`. Tests assert every 1.3.0 line
except the version declaration survives in 1.4.0, and that named 1.3.0 requirements the
supplied handoff omits — durable project home, `forge pack inspect` pre-flight, preview-
required context apply, the run-cancellation rule, and the scope-amendment pre-flight — are
still present.

## Pack data

`software-basic` 0.5.0 → 0.6.0 with a recomputed digest
(`sha256:7ef57351d571bf78fedbb115466b0f0b351addd4970909ef92e845fbc4aff962`), carrying
interview guidance for vision, first milestone, risks and constraints, and learning path,
plus phase guidance for all six steps. `research-basic` is untouched and keeps
`sha256:11ce1ee8…cf37e5`.

An append-only table records every published `(pack, version, digest)` identity so a version
can never denote two different contents.

## Skew detection

`forge doctor` compares the protocol the installed CLI provides against the copy the
generated agent context carries, distinguishing three states: no generated context, matching,
and skew. The scope criterion named the repository source as the comparison target, which
only exists inside the FORGE source tree; comparing against the generated context detects the
same defect in any project and is the failure that motivated the criterion.

The check found a real defect on first use: regeneration wrote the new protocol copy and left
the superseded one beside it, and the warning's own remedy could not fix what applying had
created. Regeneration now removes superseded copies and the preview declares those removals,
keeping the displayed persistent write set complete.

## Starter prompts and documentation

The starter prompts were imported from the supplied asset at `b77ba8a` and re-checked against
1.4.0. Four current requirements were absent and were added: report version skew, establish
the durable project home, inspect packs read-only before proposing one, and treat
agent-context regeneration as preview-first owner-directed maintenance.

The initialized-but-no-active-initiative state is now handled where it previously misled a
fresh agent: the generated managed block states that `.forge/active/` paths exist only while
an initiative is active and that their absence is ordinary rather than damage, and the
existing-project prompt gains that branch.

Documentation covers the guidance fields, phase vocabulary, the digest and version-bump rule,
and the distinction between direct workspace use and registered adapter support. A fourth
conversational walkthrough shows a guided phase opening and closing for a beginner.

Managed Codex and Claude references were regenerated at 1.4.0 with bytes outside the FORGE
managed markers unchanged.

## Known limitations

- **M13 is partially inapplicable as written.** It requires protocol resources "1.0.0 through
  1.3.0" to be unchanged byte-for-byte, but only 1.3.0 has ever existed in the repository
  source; 1.0.0 through 1.2.0 survive only in archives. The criterion's intent is implemented
  — 1.3.0 is retained, asserted unchanged, and 1.4.0 is added alongside it. This needs a
  recorded limitation or a scope amendment at `verify-release`.
- Section B of the release requirements (O1–O9) is untouched by this step. It is owner-observed
  and cannot be satisfied by any agent-recorded check.
- Nine tests skip on this machine because symlink creation needs a Windows privilege the
  session does not hold. They are environmental, not defects.
- `research-basic` guidance data and the read-only CLI helpers remain deferred to the
  successor, per the accepted scope.
