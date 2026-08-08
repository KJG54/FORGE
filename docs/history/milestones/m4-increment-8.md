# M4 Increment 8 — Append-Only Decision Withdrawal

## Authorized scope

- configured-owner-only withdrawal of one current governance decision;
- reuse of immutable `DecisionRecord`, `DecisionSupersession`, and `decision-superseded` history;
- a reserved fixed-semantics `decision-withdrawal` replacement;
- exact prior-decision canonical digest plus inherited record and digest binding;
- refusal of stale, superseded, unknown, and withdrawal-record targets;
- no resurrection of earlier decisions;
- state-neutral replay with no workflow progression or invalidation authority;
- automatic reopening when the withdrawn authority was a workflow-deviation review;
- current, withdrawn, superseded, and stale read-only inspection;
- explicit-abandonment and terminal-archive preservation;
- idempotent recording plus conservative command-receipt recovery; and
- restart and cross-record validation of records, events, semantics, digests, and directories.

## Explicit exclusions

Broader run-cancellation hardening, live cross-process cancellation, structured local
security-event reporting, emergency-override withdrawal or automated expiry, automatic
review-condition monitoring, incident recovery, executable pack providers, provider APIs,
automatic verification or acceptance, and M5 work are not implemented.

## Design evidence

[ADR-0041](../adr/ADR-0041-append-only-decision-withdrawal.md) records contract reuse, reserved
semantics, exact binding, append-only authority removal, fail-closed deviation reopening, and
no-workflow-authority decisions.

[Acceptance, Decisions, and Invalidation](../acceptance-and-invalidation.md) documents the
operator workflow and derived status model.

## Test evidence

Focused tests cover owner authority, append-only persistence, exact record and digest binding,
reserved-type forgery, noncurrent and recursive-withdrawal refusal, state neutrality,
workflow-deviation reopening, idempotent CLI replay, historical inspection, restart tamper
detection, and abandonment archive preservation.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 268 tests were exercised: 262 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, recorded a decision,
  withdrew it, and reported the original as withdrawn with its exact replacement and
  supersession; and
- the installed wheel exported all 48 schemas, confirming that Increment 8 reused the existing
  public decision contracts.

## Stop point

Stop after general decision withdrawal. Broader cancellation hardening, structured security/audit
events, and the cumulative M4 security suite remain separate bounded work.
