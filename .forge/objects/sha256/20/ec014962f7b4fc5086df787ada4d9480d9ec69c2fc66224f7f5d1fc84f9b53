# Profile-Aware Facilitation — Verification Report

Initiative: `fb1e3732-334f-4bb1-9e51-40dad0e9521b`
Step: `verify-release` — required output role `verification-report`

This artifact reports check outcomes. It is not evidence, verification, or acceptance; those are
separate recorded facts. Criteria are from
`release/profile-aware-facilitation/release-requirements.md`.

## Candidate identity

| Property | Value |
|---|---|
| Wheel | `forge_governance-1.0.0-py3-none-any.whl` |
| Wheel SHA-256 | `1d76bd7e1f59d8a312ccaeceab214af8036845ef721b51d5d86fd21c37243814` |
| Source revision | `f15b939` on `feature/profile-aware-facilitation`; M8 correction `2e77c3d` |
| M8 correction wheel SHA-256 | `90e09d9d4da7244e483816e2016ce8f94d6e6ba8de73b2a953f24c605d918ae9` |
| Agent protocol | 1.4.0, `sha256:d89a51ca82221dab36eeeebfb09e88281906298d4c8e1b828b63b152c09ebc2c` |
| Bundled packs | `software-basic` 0.6.0, `research-basic` 0.4.0 |
| Installation mode | isolated venv, CPython 3.14, Windows |

The wheel ships both `forge/resources/agent-protocol-1.3.0.md` and
`forge/resources/agent-protocol-1.4.0.md`.

## Environments

- **Source suite** — repository working tree, `.venv`, full pytest/pyright/ruff.
- **Installed candidate** — the wheel above installed into a fresh venv at `C:\t\smoke\venv`
  with a throwaway project at `C:\t\smoke\project`. Criteria whose meaning depends on a real
  install were exercised here rather than in-process.

## Section A results

| # | Outcome | Evidence |
|---|---|---|
| M1 | passed | Legacy pack fixtures in `test_local_v1_l5` and `test_m5_increment_4` construct pre-L5 and pre-M5 packs with guidance cleared and reproduce their historical digests exactly. |
| M2 | passed | Installed candidate exported 53 contract schemas. `forge-contracts-1` compatibility manifest carries the `profile-aware-facilitation` baseline adding `interview-guidance-group` and `phase-guidance`. |
| M3 | passed | `test_malformed_guidance_is_rejected` covers empty label, non-symbolic `must_answer_before_create`, and unknown keys under `extra="forbid"`. |
| M4 | passed | `software-basic` 0.5.0 → 0.6.0 with digest `sha256:7ef57351…aff962`. `test_no_pack_version_is_reused_for_different_content` enforces the append-only identity table. |
| M5 | passed | `forge doctor`, `forge status`, `forge agent context` preview, and `forge pack list` run consecutively left the journal at 22 events and the active-record file count at 27, unchanged. |
| M6 | passed | Context generation is unchanged in what it selects; `test_agent_context` and `test_vendor_context` pass, and generated `current.json` gained no new file class. |
| M7 | passed | Regenerating both managed references changed only bytes inside the FORGE managed markers, confirmed by diff of `CLAUDE.md` and `AGENTS.md`. |
| M8 | passed after correction | Original verification exercised generated-context skew. Addendum below re-verifies repository-source skew on correction commit `2e77c3d` and rebuilt wheel `sha256:90e09d9d4da7244e483816e2016ce8f94d6e6ba8de73b2a953f24c605d918ae9`. |
| M9 | passed | Installed candidate reported `FORGE repository health: healthy` on a fresh `forge init`, validating `software-basic` 0.6.0 and `research-basic` 0.4.0. |
| M10 | passed | `test_agent_starter_prompts` asserts the official repository URL, `forge --version`, `forge agent protocol`, the document-first interview, task split, phase playback, and owner-gate ceremony, and that gate commands never appear as ready-to-run vectors. |
| M11 | passed | This change adds no command. The `forge doctor` protocol check is read-only per M5. Owner-only gates remain labelled owner-only in status output and protocol templates. |
| M12 | passed | pyright 1.1.411: 0 errors. ruff: clean. `tools.version_consistency`: passed. pytest: 448 passed, 9 skipped. |
| M13 | passed, as governed by decision `7cef20dd-41d9-47d5-b01c-c5127d08d272` | Protocol 1.3.0 retained byte-for-byte and asserted by `test_current_protocol_contains_every_line_of_the_superseded_protocol`; 1.4.0 added alongside; both ship in the wheel; `AGENT_PROTOCOL_VERSION` resolves to a shipped resource. The 1.0.0–1.2.0 enumeration was not evaluated because those resources have never existed in the repository source. |
| M14 | passed | Literal pre-change digests hold for all three guidance-free packs. Independently confirmed on the installed candidate: `research-basic 0.4.0 (sha256:11ce1ee84c288a210346a9c1ff61567385ee704b6adb3498ed4e77dfd2cf37e5)`, its exact pre-change value. |
| M15 | passed | `test_archived_pack_locks_still_validate_against_their_recorded_digests` compares every archived `pack.lock.json` against a recomputed digest, and `forge doctor` reports archives healthy. |
| M16 | passed | `test_current_protocol_contains_every_line_of_the_superseded_protocol` allows only the version-declaration line to differ; named 1.3.0 requirements the supplied handoff omits are separately asserted present. |

Sixteen of sixteen passed. One (M13) passed under a recorded owner decision rather than as
literally written.

## M8 correction addendum

Review after the first verification found that M8 had been tested against generated agent context
skew, while the accepted requirement named installed-CLI versus repository-source protocol skew.
Commit `2e77c3d` corrects `forge doctor` to inspect observable FORGE source declarations at
`src/forge/core/agent_protocol.py` and `release/version-contract.json`. When the installed
protocol differs from repository source, `doctor` now reports an integrity failure instead of a
healthy repository. Generated-context skew remains a separate remediable diagnostic.

Checks rerun for this addendum:

| Check | Result |
|---|---|
| Fast quality gate | passed: Ruff clean, Pyright 1.1.411 reported 0 errors, and version consistency passed |
| Focused protocol/guidance/starter tests | passed: 37 tests |
| Affected workflow/CLI tests | passed: 70 passed, 1 skipped for missing Windows symlink privilege |
| Full pytest | 449 passed, 9 skipped, 1 environmental Git failure under a long temp path; the exact failing test passed when rerun under a shorter temp path |
| Built wheel | passed: `forge_governance-1.0.0-py3-none-any.whl`, sha256 `90e09d9d4da7244e483816e2016ce8f94d6e6ba8de73b2a953f24c605d918ae9` |
| Installed-wheel import source | passed: `forge` imported from isolated wheel target path, not the editable checkout |
| Ordinary initialized project | passed: installed wheel `forge doctor` reported healthy with no repository source or generated context |
| Repository-source skew | passed: installed wheel `forge doctor` against a throwaway project declaring `AGENT_PROTOCOL_VERSION = "9.0.0"` reported `Installed CLI agent protocol 1.4.0 is older than repository source protocol 9.0.0` and did not print `FORGE repository health: healthy` |

Limitation: the installed-wheel M8 run used the rebuilt wheel installed into an isolated target
path while reusing the existing `.venv` interpreter and dependency set; it was not a fresh-venv
dependency installation. The check still exercised the wheel's `forge` package bytes rather than
the editable source checkout.

## Section B — not evaluated here

O1 through O9 are owner-observed. No check in this report evaluates them, and no
agent-recorded check can. They require an owner driving real sessions against the installed
candidate and gate `review-risk` through the friction report.

Section B is therefore **outstanding**, not passed and not failed.

## Limitations

- Nine tests skip because symlink creation requires a Windows privilege this session does not
  hold. They were not evaluated. They concern symlink rejection paths, not guidance behaviour.
- The installed-candidate checks ran on one matrix cell only: CPython 3.14, Windows, venv
  installation. Linux, macOS, other Python versions, and pipx installation were not exercised.
- No performance review was run. This change is not performance-scoped, and the macOS budget
  question is explicitly out of scope.
- M6 is evidenced by unchanged behaviour and passing context tests rather than by a new
  allowlist-drift test.
- The candidate wheel is unpublished and untagged.
