# ADR-0012 — Canonical Event Hash Chain

- **Status:** Accepted
- **Date:** 2026-07-14

## Decision

M2 journals use a strict FORGE canonical JSON profile: Pydantic JSON-mode values, UTF-8 without a
byte-order mark, lexicographically sorted object keys, compact separators, no insignificant
whitespace, and rejection of non-finite numbers or values outside the JSON data model.

Each new event is sealed by FORGE with SHA-256 in `sha256:<lowercase-hex>` form. The digest covers
the canonical JSON representation of every event field except the self-referential `event_hash`.
It therefore includes `previous_event_hash`, which is `null` for the first event and exactly the
prior event's digest thereafter.

Complete M1 journals with both hash fields empty remain readable. They are read-only until the
later authorized M2 migration increment can preserve the original bytes and record migration
provenance. Increment 1 never silently rewrites history.

## Consequences

Changed content, removed or reordered events, sequence errors, invalid links, mixed legacy/chained
records, and truncated final records fail validation. New snapshots bind to both the journal-head
sequence and digest. This increment does not add locking, recovery, or migration.
