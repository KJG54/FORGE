# Explicit Schema Migration

FORGE rejects unsupported future schemas and never rewrites persisted state merely because a newer
tool opened the repository. Use the read-only preview first:

```console
forge migrate
```

For a complete legacy M1 active journal, the preview reports
`legacy-m1-journal-to-m2-hash-chain-v1`. Apply that exact registered edge explicitly:

```console
forge migrate --apply --idempotency-key migrate-legacy-journal
forge status
forge history --event-type schema-migrated
```

The configured owner authorizes the operation. FORGE validates the active initiative, snapshot,
governed records, objects, predecessor archives, and complete legacy journal before changing
authority-bearing bytes. It saves the exact original journal under
`.forge/active/migration-sources/` and its immutable record under
`.forge/active/migration-records/`.

The atomic journal replacement contains the same events with deterministic M2 hash links followed
by one `schema-migrated` event. The event is attributed to FORGE's stable migration service and
binds the owner, registered edge, source digest, preservation path, and migration record. The
snapshot is reconstructed only from that committed history.

If execution stops after the atomic journal replacement, repeat the identical command and
idempotency key. FORGE validates the committed migration and preserved source, rebuilds the
snapshot, and completes the receipt without adding another migration event. Do not use migration
for truncated, malformed, mixed, or tampered journals; those conditions are refused without
mutation. Archived initiatives remain immutable.

## Supported pre-v1 sources

M6 Increment 1 records the complete supported schema and storage-format inventory in
[`compatibility.md`](compatibility.md). All accepted records use contract schema version `1.0`.
The complete M1 unhashed journal is the only registered legacy source format, and the M2 SHA-256
event chain is the only current target format. Accepted milestone commits are evidence baselines,
not a promise to migrate arbitrary intermediate commits or unknown journal shapes.

Synthetic frozen fixtures prove the exact deterministic edge without containing owner, project,
credential, provider, or artifact data. Unknown, mixed, malformed, truncated, or tampered inputs
retain their existing refusal or separately documented conservative recovery behavior.
