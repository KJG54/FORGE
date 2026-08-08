# M2 Increment 9 — Validated Archived Status and History Views

This increment completes the M2 archive-inspection presentation boundary.

Implemented:

- validated summaries for every immutable archive in canonical initiative-ID order;
- objective, terminal outcome, guarantee, lineage, and event-count discovery from normal status;
- detailed selected-archive terminal records, ownership, scope, manifest inventory, preserved
  objects, journal head, digest, and terminal-specific facts;
- source-aware archived history with filtered/total counts and visible event hash-chain identities;
- compatibility for existing event-only history callers and preliminary M1 archive labels; and
- multi-archive, successor-lineage, filter, integrity, CLI, and byte-for-byte read-only coverage.

This increment adds no persisted contract and no mutation path. It does not implement schema
migration, damaged-journal repair, stale-lock removal, unrelated transaction recovery, or hybrid
Git policy. Those remain separately bounded later work.
