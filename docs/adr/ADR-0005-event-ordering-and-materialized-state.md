# ADR-0005 — Event Ordering and Materialized State

- **Status:** Accepted
- **Date:** 2026-07-13

## Decision

Use schema-versioned JSON Lines events with monotonic sequence numbers. The journal is the
mutation commit point and `state.json` is reconstructable. M1 validates ordering; M2 adds
canonical hash chaining, explicit recovery, locking hardening, and idempotency fault tests.

## Consequences

Multi-file atomicity is not overstated. A committed event with a lagging snapshot is detected and
recovered explicitly rather than silently normalized.

