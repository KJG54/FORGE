# Profile-Aware Facilitation — Release Requirements

Initiative: `fb1e3732-334f-4bb1-9e51-40dad0e9521b`
Pack / workflow: `forge-framework-change` 0.1.0 / `framework-change` 0.1.0
Step: `scope` — required output role `release-requirements`

This artifact declares the definition of done and the evidence expected at each step. It is a
registered project artifact, not an acceptance, a check, or evidence. Companion artifact:
`release/profile-aware-facilitation/change-scope.md` (role `change-scope`).

## Why the definition of done is split

FORGE requires human evidence to be labeled owner-observed and never fabricated by an agent.
Roughly half the supplied handoff's acceptance criteria described how the experience should
*feel* — "mentored feels like learning by building", "gathers information conversationally rather
than as a form" — while sitting in the same list as criteria a test can decide. The handoff's own
test strategy could not check any of them.

Mixing the two would let the change ship looking more proven than it is. They are therefore
separated below, with different evidence rules and different gating steps.

## Section A — Machine-verifiable

Automated checks. The agent may claim these; FORGE checks them. Evidence class: `check-evidence`.
These gate `verify-release`.

| # | Criterion |
|---|---|
| M1 | Workflow locks and pack data created before this change load with default-empty guidance, unchanged. |
| M2 | New guidance fields appear in the exported schema and in `forge-contracts-1` compatibility fixtures. |
| M3 | Malformed guidance is rejected by pack validation with a clear error. |
| M4 | `software-basic` carries a bumped minor version; no `(version, digest)` pair from any prior release is reused for different content. |
| M5 | No read-only path introduced by this change writes under `.forge/` or appends a journal event. |
| M6 | Context generation remains allowlist-based; no new file class enters generated context. |
| M7 | Codex and Claude managed references preserve owner-authored bytes outside FORGE markers, byte-for-byte. |
| M8 | `forge doctor` reports a distinct, non-healthy diagnostic when the installed CLI's protocol version is older than the repository source. |
| M9 | `forge doctor` reports healthy on a fresh `forge init` using the new packs. |
| M10 | Starter documentation contains the official repository URL, `forge --version`, `forge agent protocol`, the document-first interview, the task split, phase playback, and owner-gate ceremony. |
| M11 | Owner-only gates remain labeled owner-only; no command added or modified by this change accepts, verifies, or mutates governed state. |
| M12 | Full test suite, type checking, and lint gates pass on the exact candidate revision. |
| M13 | Protocol resources 1.0.0 through 1.3.0 are unchanged byte-for-byte; 1.4.0 is added alongside them, and `AGENT_PROTOCOL_VERSION` resolves to a resource that ships in the built distribution. |
| M14 | Every pack that supplies no guidance — `research-basic`, `forge-framework-change`, `forge-production-release` — produces a digest identical to its pre-change value. Pinned as literal expected digests in the test, not recomputed by the same code path under test. |
| M15 | The archived `pack.lock.json` integrity digests of all four existing archives still validate after the schema change; `forge doctor` reports archives healthy. |
| M16 | Protocol 1.4.0 contains every normative requirement present in 1.3.0, enforced by test rather than trusted. |

### Note on M14

The expected digests must be pinned as literals captured *before* the schema change. Recomputing
them through the same code path under test would make the test pass by construction — the exact
failure mode observed in the macOS performance-budget change this initiative excludes.

## Section B — Owner-observed

Human evidence. The agent must not fabricate these. Each requires an owner-observed record naming
the date, the agent used, the exact FORGE revision, the prompt used, what happened, and a verdict
of met / partially met / not met. Dispositions live in the `friction-report` artifact and gate
`review-risk`.

| # | Criterion |
|---|---|
| O1 | A fresh agent given one starter prompt, with no prior FORGE knowledge, routes itself to FORGE rather than an unrelated `forge` tool. |
| O2 | Before any gate, the agent performs state detection, requests existing documents, interviews, and plays back a first milestone. |
| O3 | Each workflow step is presented as a distinct phase, not blended into the previous one. |
| O4 | The task map visibly separates owner, agent, either-party, and owner-only gate work. |
| O5 | `guided` surfaced at least one tradeoff that changed an owner decision. |
| O6 | `mentored` produced a project-specific learning path and at least one useful owner practice task. |
| O7 | `minimal` remained compact; token use recorded and compared against `mentored` on the same task. |
| O8 | A capable agent that is neither Codex nor Claude participated successfully through the universal/manual prompt. |
| O9 | The interview felt like conversation rather than a form. |

### Dogfooding environment

Section B cannot be exercised from inside this repository's own initiative — the packs and
protocol under construction are not the installed ones. It requires building the candidate,
installing it into an isolated environment (precedent: `.smoke-venv`,
`.forge/local/m6-increment-8-release-validation/venv-smoke`), and running the scenarios in a
throwaway project directory outside this repository, against a recorded built revision. This is
planned work in `verify-release` and `review-risk`, not an afterthought.

## Evidence mapped to the locked workflow

**[Sourced]** `framework-change` 0.1.0 requires eight artifact classes and one evidence class,
`check-evidence`.

| Step | Required outputs | What satisfies them |
|---|---|---|
| `scope` | `change-scope`, `release-requirements` | This artifact and its companion |
| `implement` | `framework-changes` | Protocol 1.4.0, pack contract, `software-basic` guidance data, version contract, docs, tests |
| `verify-release` | `verification-report` | Results for M1–M16 on one exact candidate revision |
| `review-risk` | `friction-report`, `residual-risk-report` | O1–O9 dispositions plus classified residual risk |
| `closeout` | `release-readiness-record`, `lessons` | Readiness bound to accepted verification and risk-review outputs |

Per-step expectations recorded in canonical context for `scope`: worker claim requirement
`outputs-produced`; check requirement after import `scope-reviewed`; workflow evidence class after
import `check-evidence`; owner-only acceptance requirement `owner-acceptance`. Worker claims never
constitute checks, evidence, or owner acceptance.

## Ready for owner review when

- every criterion in Section A passes on one exact candidate revision;
- every criterion in Section B has an owner-observed record with a disposition;
- the friction report and residual-risk report classify every finding; and
- the release-readiness record binds to the accepted verification and risk-review outputs.

## Explicit non-equivalences

No item below implies any other. Each is a separately reviewable fact:

- a worker claim is not a check;
- a passing check is not registered evidence;
- registered evidence is not verification;
- verification is not owner acceptance;
- adapter or command success is not any of the above;
- a Git commit, branch, or push is not FORGE acceptance, and a FORGE record is not Git
  publication.
