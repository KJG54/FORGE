# M4 Increment 4 — Owner-Reviewed Workflow Deviations

## Authorized scope

- owner-only append-only recording of observed workflow deviations;
- exact locked-workflow ID, version, and digest binding;
- explicit declared behavior, actual behavior, rationale, and review requirement;
- state-neutral recording with no waiver or lifecycle authority;
- review through one current immutable `workflow-deviation-review` decision;
- reopening when that review is superseded or becomes stale without a replacement review;
- status and read-only CLI inspection;
- successful-closure refusal while any deviation remains open;
- terminal archive preservation, including explicit abandonment with unresolved history;
- idempotent record and review commands plus conservative receipt recovery; and
- restart and cross-record validation of records, events, reviews, closure, and directories.

## Explicit exclusions

Emergency overrides, risk acceptance, general decision withdrawal, automatic step invalidation,
live cross-process cancellation, incident recovery, executable pack providers, provider APIs,
automatic verification or acceptance, and M5 work are not implemented.

## Design evidence

[ADR-0037](../adr/ADR-0037-owner-reviewed-workflow-deviations.md) records the observation-versus-
authority boundary, ordinary-decision review model, supersession behavior, closure rule, and
abandonment distinction.

[Acceptance, Decisions, and Invalidation](../acceptance-and-invalidation.md) documents the
operator workflow.

## Test evidence

Focused tests cover owner authority, exact state neutrality, non-deviation refusal, open status and
next-action reporting, closure refusal, immutable review, duplicate-review refusal, review
supersession and reopening, idempotent CLI replay, read-only inspection, restart tamper detection,
and terminal archive preservation.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 248 tests were exercised: 242 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, recorded, reviewed, and
  inspected a workflow deviation with journal-bound idempotency; and
- the installed wheel exported all 48 schemas, confirming that Increment 4 reused existing public
  contracts without a schema-count change.

## Stop point

Stop after workflow deviations. A deviation and its review never waive workflow requirements.
Emergency override and risk acceptance remain separate schemas until later increments define their
authority, expiry, review, invalidation, and closure effects.
