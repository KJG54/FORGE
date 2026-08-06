# ADR-0004 — Source-of-Truth Hierarchy

- **Status:** Accepted
- **Date:** 2026-07-13

## Decision

Current artifact bytes, preserved historical bytes, binding digests, the validated journal,
locked rules, and materialized state have authority in that order. Summaries, indexes, handoffs,
chat, and vendor views are derived and disposable.

## Consequences

State disagreements become explicit integrity errors. A snapshot never overrides valid history.

