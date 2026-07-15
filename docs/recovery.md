# Explicit Active-State Recovery

`state.json` is a reconstructable view; the hash-chained event journal is authoritative. If
`forge status` or `forge doctor` reports that the active snapshot is missing, invalid, or does not
match replay, inspect the repository and then run:

```console
forge recover --reason "Snapshot write was interrupted" \
  --idempotency-key recover-2026-07-14
```

Choose a stable, unique key and keep the reason specific enough for a future reviewer. Only the
configured repository owner may recover.

For snapshot recovery, FORGE validates the complete canonical journal, locked initiative and
workflow, every implemented governed record, and every referenced preserved object before changing
anything. A complete legacy M1 journal remains read-only until its registered migration is applied.

When `state.json` exists, its exact original bytes are retained under
`.forge/active/recovery-snapshots/`; the corresponding immutable record is stored under
`.forge/active/recovery-records/`. FORGE then appends recovery provenance and reconstructs the
snapshot atomically. Validate the result with:

```console
forge status
forge doctor
forge history --event-type integrity-recovered
```

## Truncated final journal records

Increment 12 uses the same explicit command when—and only when—the active journal consists of a
non-empty valid M2 hash-chain prefix followed by JSON that is demonstrably truncated at
end-of-file. FORGE refuses mutation when the last record is complete but lacks its newline, is
schema-invalid, contains non-EOF malformed data, has a bad sequence or hash, follows a damaged
prefix, or belongs to legacy or archived history. Those cases are ambiguous: FORGE cannot know
which event the owner intended.

For an eligible truncation, FORGE first validates every governed record and object supported by the
valid prefix. It preserves the complete damaged journal under
`.forge/active/recovery-journals/`, including the exact tail bytes, and preserves every observed
snapshot under `.forge/active/recovery-snapshots/`. The `JournalRecoveryRecord` binds those bytes,
their digests and sizes, the last valid journal head, the owner reason, and the observed snapshot
condition.

The atomic journal replacement contains the complete valid prefix plus one owner-attributed
`journal-recovered` event. No attempted bytes are silently deleted: the complete source remains
governed evidence. Inspect the result with:

```console
forge history --event-type journal-recovered
forge doctor
```

If the command stops after reporting its idempotency key, repeat the identical command with the
same key. A committed recovery event is resumed without duplication. Do not use this command to
infer a missing event, remove a stale lock, repair an archive, or resolve another command's missing
completion receipt; those operations are outside this increment.

Resume is deliberately narrow: the current snapshot must either already match replay or still be
the exact condition and bytes observed by the committed recovery record. A different post-commit
snapshot change is refused as a new integrity incident.
