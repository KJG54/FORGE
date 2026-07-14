# M2 Increment 4 — Explicit Active-Snapshot Recovery

## Authorized scope

- owner-only `forge recover` with a required reason and journal-bound idempotency key;
- recovery only from a complete, valid canonical hash-chained active journal;
- refusal of healthy snapshots, ambiguous history, damaged journals, and legacy M1 journals;
- pre-commit validation of locked governance records and referenced preserved objects;
- exact-byte preservation of an observed invalid or mismatched snapshot;
- immutable recovery record and owner-attributed `integrity-recovered` event;
- atomic deterministic reconstruction of `state.json` after the recovery event commit point;
- same-key resume without a duplicate event if snapshot or receipt persistence is interrupted;
- missing, invalid, mismatched, damaged-journal, healthy-state, and interruption regression tests.

## Explicit exclusions

This increment does not truncate or repair journal bytes, migrate legacy M1 journals, resolve
unrelated incomplete commands, recover archive promotion or active-state retirement, delete stale
locks, pause or resume initiatives, harden archive atomicity, abandon initiatives, or create
successors. Those remain separately authorized later increments.
