# M2 Increment 1 — Canonical Integrity Chain

## Authorized scope

- strict deterministic JSON for governed event hashing;
- SHA-256 event sealing and previous-hash chaining;
- full chain validation on every journal read;
- snapshot binding to the validated journal-head sequence and hash;
- read-only recognition of complete legacy M1 journals;
- corruption and compatibility regression tests.

## Explicit exclusions

Cross-process locks, idempotency, stale-lock handling, pause/resume, recovery, migration, hardened
archive transactions, abandonment, successors, and hybrid Git policy remain later M2 work. A
damaged or legacy journal is reported and never repaired or rewritten by this increment.

## Format

The exact approved serializer and hash rules are recorded in
[ADR-0012](../adr/ADR-0012-canonical-event-hash-chain.md). New journals are hash-chained from their
first event. A legacy M1 journal may be inspected, replayed, and archived as it existed, but a
mutation receives an actionable conflict until the migration increment is authorized.
