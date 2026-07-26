# M4 Increment 6 — Exact Override-Bound Risk Acceptance

## Authorized scope

- configured-owner-only residual-risk acceptance;
- exact current emergency-override ID and canonical-digest binding;
- copied residual risk plus explicit rationale, residual impact, and optional review condition;
- one current, non-stale risk acceptance per override;
- state-neutral replay with no workflow progression authority;
- resolution of only the exact override's successful-closure blocker;
- scope-amendment staleness of the affected override and acceptance together;
- status and read-only CLI inspection;
- explicit-abandonment and terminal-archive preservation;
- idempotent recording plus conservative command-receipt recovery; and
- restart and cross-record validation of records, events, digests, staleness, closure, and
  directories.

## Explicit exclusions

General decision withdrawal, risk-acceptance revocation, automatic review-condition monitoring,
override withdrawal or automated expiry, workflow transitions based on overrides, live
cross-process cancellation, incident recovery, executable pack providers, provider APIs,
automatic verification or acceptance, and M5 work are not implemented.

## Design evidence

[ADR-0039](../adr/ADR-0039-exact-override-bound-risk-acceptance.md) records the exact binding,
state-neutral, narrow closure resolution, scope-coupled staleness, and no-fabricated-support
decisions.

[Acceptance, Decisions, and Invalidation](../acceptance-and-invalidation.md) documents the
operator workflow and review-condition boundary.

## Test evidence

Focused tests cover owner authority, exact binding, copied risk and digest relationships, unknown
and stale override refusal, duplicate-current refusal, exact state neutrality, status and closure
behavior, scope-coupled staleness, idempotent CLI replay, read-only inspection, restart tamper
detection, and abandonment archive preservation.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 257 tests were exercised: 251 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, recorded an emergency
  override, accepted its exact residual risk, removed only that override's status blocker, and
  inspected the current acceptance; and
- the installed wheel exported all 48 schemas, confirming that Increment 6 reused the existing
  public `RiskAcceptance` contract.

## Stop point

Stop after exact override-bound risk acceptance. The record never authorizes workflow progression.
General governance-record withdrawal or revocation remains a separate increment that must define
authority, dependency staleness, closure, and historical inspection behavior.
