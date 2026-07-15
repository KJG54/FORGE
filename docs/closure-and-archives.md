# Atomic Closure and Archive Inspection

M2 Increment 6 upgrades successful closure from the preliminary M1 process to a resumable,
interruption-safe transaction. It does not implement abandonment, successor initiatives, schema
migration, stale-lock removal, or generic recovery for unrelated commands.

## Closure gate

`forge close --summary <text> --idempotency-key <key>` is owner-only. Before its governance commit,
FORGE requires every workflow step to be completed and currently accepted, no active governed run,
exact current working bytes, valid preserved objects, a non-empty final owner summary, healthy
integrity, and a clean Git worktree when configured.

The final `initiative-closed` event is the governance commit point. It binds the `ClosureRecord`,
current artifact revisions, final acceptances, archive destination, and the command idempotency
identity. Replay moves the initiative to terminal `closed`; later events remain invalid.

## Resumable transaction

After the closure event and terminal snapshot are durable, FORGE performs four recoverable phases:

1. copy terminal active state into a same-filesystem, deterministically named staging directory;
2. build and validate a non-preliminary `archive-manifest.json` over every archived file and
   preserved object reference;
3. atomically promote staging to `.forge/archive/<initiative-id>/`; and
4. atomically rename terminal `.forge/active`, recreate an empty active directory, validate the
   retired tree against the archive, and remove the retired copy.

The archive is validated before terminal active state is retired. The terminal journal, hardened
archive, deterministic staging name, and deterministic retired name make every post-commit phase
observable and reconstructable. FORGE does not roll back a committed closure event.

If a phase is interrupted, `forge status` reports an integrity blocker. Repeat the exact close
request with the same idempotency key:

```console
forge close --summary "All governed outputs are accepted" \
  --idempotency-key close-release-1
```

The retry validates the committed owner decision, rebuilds incomplete staging when needed,
reuses an already valid promoted archive, finishes active-state retirement, and only then writes
the idempotency completion receipt. It never appends a duplicate closure event.

## Archive contents and inspection

The archive contains the complete terminal journal and snapshot, initiative and locked workflow
identity, governed records, closure record, and manifest. Manifest entries bind each file by path,
byte count, and SHA-256 digest. Object references continue to verify exact accepted bytes under
`.forge/objects/sha256/` independently of mutable project files.

```console
forge status --archive <initiative-id>
forge history --archive <initiative-id>
forge history --archive <initiative-id> --event-type initiative-closed
```

New manifests report `preliminary: false` and no preliminary limitations. Existing preliminary M1
archives remain readable as their original guarantee; this increment does not rewrite them.

Closed archives cannot reopen. Continued work still requires the separately authorized successor
initiative increment.
