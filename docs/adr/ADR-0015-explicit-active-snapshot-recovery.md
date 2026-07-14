# ADR-0015 — Explicit Active-Snapshot Recovery

- **Status:** Accepted
- **Date:** 2026-07-14

## Decision

FORGE provides an owner-only `forge recover` command for an active initiative whose derived
`state.json` is missing, invalid, or inconsistent with deterministic replay. Recovery is allowed
only when the complete authoritative journal is a valid canonical hash chain and all governed
records and referenced content-addressed objects validate.

An existing snapshot is preserved byte-for-byte with its SHA-256 digest before recovery commits.
FORGE writes a schema-versioned recovery record, then appends an owner-attributed
`integrity-recovered` event. That journal append is the recovery commit point. Only after the event
is durable does FORGE atomically reconstruct `state.json` from the full journal.

The recovery event is state-neutral and records the original journal head, observed snapshot
condition, preservation reference, owner reason, and exact recovery-record digest. If execution
stops after this event commits, the same idempotency key and request may finish the snapshot and
completion receipt without appending a second recovery event. Resume is refused if the snapshot
has changed to bytes or a condition not captured by that event.

## Consequences

Recovery is explicit, attributable, inspectable, and conservative. It never treats a derived
snapshot as authority and never silently discards journal history. Missing, truncated, malformed,
legacy, mixed, or hash-invalid journals are refused without mutation. Missing governed records or
preserved objects are also refused before the recovery event.

This decision does not authorize journal truncation or byte repair, generic interrupted-command
resolution, archive retirement recovery, stale-lock deletion, pause/resume, migration,
abandonment, or successor initiatives.
