# M4 Increment 9 — Formal Run-Cancellation Hardening

## Authorized scope

- one immutable public `RunCancellationRecord` per successful cancellation;
- exact canonical run-digest binding;
- exact locked workflow cancellation-policy and side-effect-risk binding;
- run-worker or configured-owner authorization;
- safe manual cancellation without pretending a process existed;
- adapter cancellation only after one prior hash-sealed terminal execution event;
- fail-closed refusal of live or unproven adapter execution;
- deterministic `ready` or `blocked` destination derivation;
- append-only persistence, rollback before event commit, and duplicate refusal;
- idempotent CLI replay and conservative interrupted-command recovery;
- run inspection, terminal archive preservation, and active/archive listing; and
- restart validation of records, events, ordering, actors, policies, states, and digests.

## Explicit exclusions

Live cross-process cancellation, background process supervision, operating-system process
signaling, automatic crash resume, structured local security-event reporting, incident recovery,
executable pack providers, provider APIs, hostile-code isolation, automatic verification or
acceptance, and M5 work are not implemented.

## Design evidence

[ADR-0042](../adr/ADR-0042-formal-run-cancellation.md) records the immutable cancellation record,
exact run and terminal-execution binding, authorization model, fail-closed process boundary,
workflow destination derivation, and transaction behavior.

[Workflows](../workflows.md), [Persistence](../persistence.md), and
[Adapters](../adapters.md) document the operator, storage, and managed-execution boundaries.

## Test evidence

Focused tests cover worker and owner authorization, exact immutable binding, risky-work blocking,
manual and adapter boundaries, unproven execution refusal, pre-commit rollback, duplicate refusal,
idempotent replay, conservative receipt recovery, restart tamper detection, run inspection, and
archive preservation.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 274 tests were exercised: 268 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, began and cancelled a
  manual run, and showed its formal cancellation record; and
- the installed wheel exported all 49 schemas, including `run-cancellation-record.schema.json`.

## Stop point

Stop after formal cancellation hardening. Structured security/audit events and the cumulative M4
security suite and closeout remain separate bounded work.
