# M4 Increment 3 — Owner-Governed Scope Amendments

## Authorized scope

- append-only configured-owner scope amendment;
- complete effective-scope replacement without editing initiative creation;
- locked-workflow validation for affected requirements and return step;
- current-initiative validation for affected logical artifacts;
- derived downstream claim, check, evidence, acceptance, decision, gate, and step invalidation;
- explicit affected-run cancellation prerequisite;
- latest effective scope in regenerated canonical agent context;
- idempotent CLI mutation plus read-only history inspection;
- restart, archive, recovery-pattern, and cross-record validation; and
- renewed claim/check/evidence/acceptance requirements after restart.

## Explicit exclusions

Workflow deviation, emergency override, risk acceptance, general decision revocation, live
cross-process cancellation, executable pack providers, provider APIs, automatic crash resume,
automatic verification or acceptance, and M5 work are not implemented.

## Design evidence

[ADR-0036](../adr/ADR-0036-owner-governed-scope-amendments.md) records the complete-scope model,
derived invalidation, active-run refusal, owner authority, worker-context propagation, and
non-waiver boundary.

[Acceptance, Decisions, and Invalidation](../acceptance-and-invalidation.md) documents the operator
workflow and renewed-support requirement.

## Test evidence

Focused tests cover accepted-work staleness, return-step invalidation, untouched descendant reset,
effective agent scope, no verification or acceptance waiver, explicit rework, owner-only authority,
unknown requirement refusal, affected active-run refusal, post-cancellation amendment, idempotent
CLI replay, read-only inspection, restart validation, and record tamper detection.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 244 tests were exercised: 238 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, recorded and inspected a
  scope amendment, displayed original and effective scope with an invalidated return step, and
  exported all 48 schemas.

## Stop point

Stop after scope amendment. The other M4 governance-change contracts remain schemas only until a
later increment defines their distinct authority, expiry, review, and lifecycle effects.
