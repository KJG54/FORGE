# Milestone 4 Evidence Report

**Milestone:** M4 — Governance Hardening and Security Closeout

**Implementation state:** complete and owner-accepted

**Owner acceptance:** accepted in the Codex task by the repository owner on 2026-07-27

**Authorized boundary:** M4 only; M5 has not begun

## Outcome

M4 preserves the separation between assertion, observation, evidence, verification, acceptance,
and exceptional governance while adding narrowly authorized local execution. Validators are
declared in tracked owner configuration, disabled by default, approved against an exact profile,
and supervised without a shell or inherited credential environment. Their results remain checks,
not truth, evidence, verification, acceptance, or workflow authority.

Material scope change, deviations, emergency overrides, risk acceptance, revocation, decision
withdrawal, cancellation, and local failure auditing are explicit immutable facts with fail-closed
replay. None fabricates missing workflow support or converts trusted pack data into executable
authority.

## Increment inventory

| Increment | Delivered boundary |
|---|---|
| 1 | Declarative disabled-by-default local validator capabilities |
| 2 | Supervised no-shell validator execution and immutable check capture |
| 3 | Owner-governed complete-scope amendment and derived invalidation |
| 4 | State-neutral workflow deviations and current owner review |
| 5 | Non-bypassing exact emergency override records |
| 6 | Exact override-bound residual-risk acceptance |
| 7 | Append-only risk-acceptance revocation |
| 8 | Append-only general decision withdrawal |
| 9 | Exact, terminal-proof-bound formal run cancellation |
| 10 | Sanitized structured local security and failure auditing |
| 11 | Cumulative adversarial acceptance, claim-integrity hardening, and closeout |

## Exit-criteria assessment

| Exit criterion | Result | Evidence |
|---|---|---|
| Seeded false completion cannot reach acceptance | satisfied | The cumulative suite proves a claim and failed check remain below verification; focused lifecycle tests require current revisions, passing declared checks, evidence, verification, and owner acceptance |
| Trusted-data packs cannot execute code without separate capability approval | satisfied | The closeout validator remains disabled in a trusted initiative until exact owner approval; pack-capability tests prove declared pack IDs do not register executable validators |
| Revoked acceptance and superseded decisions stop authorizing progression | satisfied | The cumulative suite invalidates downstream readiness after acceptance revocation and reopens a deviation after its review is withdrawn; focused replay tests cover restart and archive behavior |
| Malicious packs, hostile imports, command injection, path escape, and forged claims are blocked | satisfied | The closeout suite refuses each class; dedicated pack, import, path, adapter-claim, schema, secret, symlink, digest, and record-tamper tests provide deeper variants |
| Security documentation requires external isolation for same-user malicious processes | satisfied | `SECURITY.md`, the constitution, adapter guidance, and validator guidance explicitly deny a hostile-code sandbox claim and direct owners to external isolation |

## Architecture and authority evidence

| Boundary | M4 implementation | Evidence |
|---|---|---|
| Validator declaration | Strict tracked executable plus ordered arguments; no command-string field | schema and declaration validation |
| Executable authority | Exact owner approval, bounded scope, one-time consumption, revocation, and profile-drift refusal | capability and validator tests |
| Process supervision | `shell=False`, allowlisted environment, declared working directory and timeout, bounded local capture | pass/fail/timeout/overflow/environment and literal-argument tests |
| Verification | Validator output becomes one immutable revision-bound `CheckResult` only | lifecycle-neutral validator tests |
| Governance change | Scope amendment derives staleness; deviations, overrides, and risk facts grant no progression | amendment, deviation, override, risk, and closeout tests |
| Authority removal | Acceptance revocation, risk revocation, and decision supersession are append-only and fail closed | acceptance, risk, decision, deviation, restart, and archive tests |
| Cancellation | Manual cancellation is exact; adapter cancellation requires a prior terminal hash-sealed execution event | cancellation hardening tests |
| Audit | Sanitized local failure events are inspectable but outside journal and acceptance authority | local audit and doctor tests |
| Claim integrity | New claim events bind the full canonical record digest plus exact revision digests | closeout forgery and restart validation |

## Validation results

The final Increment 11 validation records:

- Ruff passed with no findings.
- Strict Pyright passed with 0 errors and 0 warnings.
- Pytest exercised all 283 tests: 277 passed and 6 Windows symlink-privilege cases were skipped.
- Isolated source-distribution and wheel builds passed.
- A clean environment installed the wheel, loaded the packaged CLI, and reported `0.1.0a0`.
- The installed-wheel CLI initialized a repository, created an initiative, refused premature
  acceptance with conflict exit 31, listed the resulting sanitized audit event, and passed doctor.
- The installed wheel exported all 50 public schemas.
- Remote Windows, macOS, and Linux results for this exact uncommitted closeout are not claimed.

## Known limitations and deferred work

- FORGE is not a hostile-code sandbox. A same-user process can read or alter files available to
  that operating-system identity; hostile tools require external process, container, virtual
  machine, or multi-user isolation.
- Secret screening remains heuristic defense in depth.
- Validator exit status is structural evidence, not semantic or factual truth.
- Provider APIs, executable pack providers, background execution, automatic crash resume, and
  cross-process live cancellation remain unimplemented.
- Evidence, verification, acceptance, and exceptional governance remain explicit owner-directed
  actions; FORGE does not automate them.
- Local validator captures and local audit events are Git-ignored diagnostics, not governed truth.
- Pre-closeout claim events remain readable under their original actor, run, step, revision, and
  transition bindings; new events additionally bind the full canonical claim digest.
- Naming, distribution metadata, and support policy remain pre-alpha and provisional.

## Owner decision and stop condition

The repository owner formally accepted the completed M4 milestone and authorized publication in
the Codex task on 2026-07-27.

**Stop satisfied:** M4 is complete and accepted. M5 work must follow its own explicit incremental
boundary; this report does not silently authorize unspecified M5 behavior.
