# M2 Increment 10 — Explicit Schema Migration Framework

This increment implements the registered migration framework and its first required migration.

Implemented:

- deterministic directed migration definitions with explicit source and target formats;
- read-only migration planning and an explicit owner-authorized `--apply` boundary;
- exact legacy-journal byte preservation, digest binding, and `MigrationRecord` provenance;
- deterministic legacy-event sealing and one migration-service governance event;
- atomic journal replacement as the migration commit point;
- same-idempotency-key snapshot and receipt resume after post-commit interruption;
- restart validation across records, source bytes, events, current history, and later archives;
- current-format, unknown/corrupt source, tampering, owner authority, multi-archive immutability,
  CLI, retry, schema export, and continued-mutation coverage.

This increment migrates only valid active legacy M1 journals. It does not repair damaged journals,
rewrite immutable archives, remove stale locks, recover unrelated transactions, or implement
hybrid Git policy.
