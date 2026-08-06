# M4 Increment 7 — Append-Only Risk-Acceptance Revocation

## Authorized scope

- configured-owner-only withdrawal of one current risk acceptance;
- reuse of the public `ApprovalRevocation` contract and shared revocation persistence;
- exact acceptance, emergency-override, and canonical-digest binding;
- immutable preservation of the original acceptance and override;
- state-neutral replay with no workflow progression or invalidation authority;
- reopening of only the exact override's successful-closure blocker;
- later fresh risk acceptance for the unchanged current override;
- refusal of stale and already revoked targets;
- current, revoked, and stale read-only CLI inspection;
- explicit-abandonment and terminal-archive preservation;
- idempotent recording plus conservative command-receipt recovery; and
- restart and cross-record validation of records, events, digests, closure, and directories.

## Explicit exclusions

General decision withdrawal, emergency-override withdrawal or automated expiry, automatic
review-condition monitoring, workflow transitions based on overrides, live cross-process
cancellation, incident recovery, executable pack providers, provider APIs, automatic verification
or acceptance, and M5 work are not implemented.

## Design evidence

[ADR-0040](../adr/ADR-0040-append-only-risk-acceptance-revocation.md) records contract reuse,
exact binding, append-only history, narrow blocker reopening, fresh reacceptance, and
no-workflow-authority decisions.

[Acceptance, Decisions, and Invalidation](../acceptance-and-invalidation.md) documents the
operator workflow.

## Test evidence

Focused tests cover owner authority, append-only persistence, exact record and digest binding,
duplicate and stale refusal, state neutrality, status and closure reopening, fresh reacceptance,
idempotent CLI replay, inspection, restart tamper detection, and abandonment archive preservation.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 262 tests were exercised: 256 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, recorded an emergency
  override and risk acceptance, revoked that acceptance, reported the reopened blocker, recorded a
  fresh acceptance, and removed only that blocker again; and
- the installed wheel exported all 48 schemas, confirming that Increment 7 reused the existing
  public `ApprovalRevocation` contract.

## Stop point

Stop after exact risk-acceptance revocation. General decision withdrawal, broader cancellation
hardening, structured security/audit events, and the cumulative M4 security suite remain separate
bounded work.
