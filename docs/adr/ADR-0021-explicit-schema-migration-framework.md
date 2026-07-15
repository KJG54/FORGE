# ADR-0021: Explicit Schema Migration Framework

**Status:** Accepted

**Milestone:** M2 Increment 10

## Context

Persisted FORGE contracts reject unsupported versions, and ADR-0011 requires incompatible changes
to travel through recorded migrations. ADR-0012 intentionally left complete M1 journals readable
but read-only until their exact bytes could be preserved and their history converted to the M2
hash-chain format with durable provenance.

## Decision

Maintain an ordered registry of explicit, directed migration definitions. A migration definition
names its source and target schema versions and storage formats; no implicit version inference or
best-effort rewrite is allowed. The first registered edge is
`legacy-m1-journal-to-m2-hash-chain-v1`, from a complete unhashed M1 event journal to the canonical
M2 SHA-256 event chain. This format migration retains schema version `1.0`.

`forge migrate` validates active state and previews the selected edge without persistent mutation.
`forge migrate --apply` requires configured-owner authority, the repository mutation lock, and a
journal-bound idempotency key. It preserves the exact source journal and digest, writes a
`MigrationRecord`, deterministically seals every existing event, adds one migration-service event,
and atomically replaces the journal. That replacement is the commit point. The derived snapshot
and idempotency receipt follow and may be resumed with the same key after interruption.

Migration records, preserved sources, events, and current sealed history are cross-validated on
every restart and are included in any later archive. Existing archives are never migrated or
modified. Unknown, mixed, malformed, truncated, oversized, or already-current sources are refused.

## Consequences

Legacy active initiatives can safely resume ordinary governed mutation without losing their
original evidence. Future incompatible schema changes have a registry, record, preservation, and
transaction pattern to extend. Migration is explicit and auditable but increases retained storage
because original bytes are deliberately kept.

This decision does not repair damaged journals, migrate immutable archives, remove stale locks,
recover unrelated transactions, or implement hybrid Git policy.
