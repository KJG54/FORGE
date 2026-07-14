# Explicit Active-Snapshot Recovery

`state.json` is a reconstructable view; the hash-chained event journal is authoritative. If
`forge status` or `forge doctor` reports that the active snapshot is missing, invalid, or does not
match replay, inspect the repository and then run:

```console
forge recover --reason "Snapshot write was interrupted" \
  --idempotency-key recover-2026-07-14
```

Choose a stable, unique key and keep the reason specific enough for a future reviewer. Only the
configured repository owner may recover.

Before changing anything, FORGE validates the complete canonical journal, locked initiative and
workflow, every implemented governed record, and every referenced preserved object. A damaged or
truncated journal is not a snapshot-recovery case and is refused. A complete legacy M1 journal is
also refused until a separately authorized migration exists.

When `state.json` exists, its exact original bytes are retained under
`.forge/active/recovery-snapshots/`; the corresponding immutable record is stored under
`.forge/active/recovery-records/`. FORGE then appends recovery provenance and reconstructs the
snapshot atomically. Validate the result with:

```console
forge status
forge doctor
forge history --event-type integrity-recovered
```

If the command stops after reporting its idempotency key, repeat the identical command with the
same key. A committed recovery event is resumed without duplication. Do not use this command to
edit journal history, remove a stale lock, repair an archive, or resolve another command's missing
completion receipt; those operations are outside this increment.

Resume is deliberately narrow: the current snapshot must either already match replay or still be
the exact condition and bytes observed by the committed recovery record. A different post-commit
snapshot change is refused as a new integrity incident.
