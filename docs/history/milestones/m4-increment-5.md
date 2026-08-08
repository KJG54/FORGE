# M4 Increment 5 — Non-Bypassing Emergency Overrides

## Authorized scope

- owner-only append-only emergency override declarations;
- exactly one locked-workflow requirement or gate target;
- qualified `requirement:<id>` and `gate:<id>` persistence;
- explicit rationale, residual risk, temporary/permanent status, and review requirement;
- exact locked-workflow ID, version, and digest binding;
- state-neutral replay with no claim, check, evidence, gate, acceptance, or transition authority;
- status and read-only CLI inspection;
- successful-closure refusal while residual override risk remains unresolved;
- explicit-abandonment and terminal-archive preservation;
- idempotent recording plus conservative command-receipt recovery; and
- restart and cross-record validation of records, events, targets, closure, and directories.

## Explicit exclusions

Risk acceptance, override withdrawal or automated expiry, workflow transitions based on overrides,
general decision withdrawal, live cross-process cancellation, incident recovery, executable pack
providers, provider APIs, automatic verification or acceptance, and M5 work are not implemented.

## Design evidence

[ADR-0038](../adr/ADR-0038-non-bypassing-emergency-overrides.md) records the exact-target,
state-neutral, no-fabricated-support, fail-closed closure, and later-risk-acceptance decisions.

[Acceptance, Decisions, and Invalidation](../acceptance-and-invalidation.md) documents the
operator workflow.

## Test evidence

Focused tests cover owner authority, exactly-one-target enforcement, unknown requirement and gate
refusal, permanence constraints, exact state neutrality, status reporting, closure refusal,
idempotent CLI replay, read-only inspection, restart tamper detection, and abandonment archive
preservation.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 252 tests were exercised: 246 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, recorded and inspected
  an emergency override, reported its residual-risk blocker, and refused successful closure; and
- the installed wheel exported all 48 schemas, confirming that Increment 5 reused the existing
  public `EmergencyOverride` contract.

## Stop point

Stop after emergency override declaration. An override never authorizes progression. Risk
acceptance remains a separate schema until the next increment defines exact binding, review,
closure, supersession, and invalidation behavior.
