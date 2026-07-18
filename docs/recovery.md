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

## Interrupted command receipts

`forge recover-command` is separate from snapshot and journal recovery. Use it only when FORGE
reports that one command has committed events without a completion receipt:

```console
forge recover-command <interrupted-key> \
  --reason "Receipt persistence stopped after command completion" \
  --idempotency-key <distinct-recovery-key>
```

FORGE does not assume that an event means the whole command completed. The target must be the only
unrelated incomplete key, its exact event group must be contiguous at the active journal tail, and
the group must match the registered complete pattern for that command. This matters for commands
such as step completion and acceptance, which each require two committed events.

Locked governance, records, preserved objects, replay, and the snapshot observation are validated
before a `CommandRecoveryRecord` and `command-recovered` event commit the owner decision. The
snapshot may be the exact current view or the exact view from immediately before the interrupted
command, reflecting the two valid outcomes of atomic replacement. The new receipt references only
the original command events; the recovery operation receives its own receipt.

Partial event groups, specialized close/abandon/migrate/recover transactions, archived targets,
multiple incomplete commands, changed receipts, and non-atomic snapshot conditions are refused.
No business event is inferred or appended, and no lock or journal byte is removed.

## Stale mutation locks

`forge doctor` reports mutation-lock ownership and whether the recorded process appears live or
stale. Never delete `.forge/local/locks/mutation.lock` manually. First confirm that the command and
process really ended, then use a stable key and record the reason:

```console
forge remediate-lock \
  --reason "Confirmed the interrupted process exited and no mutation remains active" \
  --idempotency-key stale-lock-2026-07-17
```

Remediation is deliberately stricter than the diagnostic label. The metadata must be bounded,
strictly shaped, regular, and non-symbolic; its hostname must equal the current host; and the
platform-safe process probe must prove that its PID is not live. A lock from another host remains
ambiguous and is refused, even if diagnostics call it stale because the owner cannot be probed
locally. Live, missing, malformed, symbolic, changed, or oversized locks are also refused.

A separate remediation guard excludes ordinary mutations during the operation. FORGE writes the
owner authorization first, then atomically renames the exact lock bytes into the key-scoped
`.forge/local/lock-remediations/` directory. A retry with the same key can finish that prepared
rename or validate and replay a completed operation. A different request cannot reuse the key.
`forge doctor` validates retained record/evidence pairs.

The evidence remains local-only because lock metadata contains host runtime details. No initiative
event, snapshot, journal, receipt, or archive is changed. After remediation, run `forge doctor` and
the command that was interrupted. If that command crossed a separate durable boundary, FORGE will
still require its specific recovery procedure rather than silently repairing it.
