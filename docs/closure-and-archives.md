# Atomic Terminal Decisions and Archive Inspection

M2 Increments 6 and 7 provide distinct resumable, interruption-safe archive transactions for
successful closure and owner-authorized abandonment. They do not implement successor initiatives,
schema migration, stale-lock removal, or generic recovery for unrelated commands.

## Closure gate

`forge close --summary <text> --idempotency-key <key>` is owner-only. Before its governance commit,
FORGE requires every workflow step to be completed and currently accepted, no active governed run,
exact current working bytes, valid preserved objects, a non-empty final owner summary, healthy
integrity, and a clean Git worktree when configured.

The final `initiative-closed` event is the governance commit point. It binds the `ClosureRecord`,
current artifact revisions, final acceptances, archive destination, and command identity. Replay
moves the initiative to terminal `closed`; later events remain invalid.

## Abandonment decision

`forge abandon --reason <text> --unfinished-work <text> --risk <text>` is owner-only and accepts a
healthy active or paused initiative. At least one risk statement is required; repeat `--risk` for
multiple risks or explicitly state `None known`. Every governed run must already be inactive, so
the owner uses `forge run cancel` before abandonment when necessary.

Unlike closure, abandonment does not require completed workflow steps, successful checks, current
acceptance, exact mutable working bytes, or clean Git. It preserves the valid governed journal,
records, and registered artifact bytes as they stand. The `initiative-abandoned` event is its
governance commit point and can never be presented as closure success.

## Resumable transaction

After either terminal event and snapshot are durable, FORGE performs four recoverable phases:

1. copy terminal active state into a same-filesystem, deterministically named staging directory;
2. build and validate a non-preliminary manifest over every file and preserved object reference;
3. atomically promote staging to `.forge/archive/<initiative-id>/`; and
4. atomically rename terminal `.forge/active`, recreate an empty active directory, validate the
   retired tree against the archive, and remove the retired copy.

The archive is validated before terminal active state is retired. The journal, hardened archive,
deterministic staging name, and terminal-specific retired name make each post-commit phase
observable and reconstructable. FORGE never rolls back a committed terminal event.

If a phase is interrupted, repeat the exact request with the same idempotency key:

```console
forge close --summary "All governed outputs are accepted" \
  --idempotency-key close-release-1

forge abandon --reason "Stop this initiative" --unfinished-work "Remaining work" \
  --risk "No accepted outcome exists" --idempotency-key abandon-release-1
```

The retry validates the committed owner decision, rebuilds incomplete staging when needed, reuses
only an exactly matching promoted archive, finishes retirement, and only then writes the completion
receipt. It never appends a duplicate terminal event.

## Archive contents and inspection

The archive contains the complete terminal journal and snapshot, initiative and locked workflow,
governed records, one terminal record, and a manifest. Manifest entries bind each file by path,
byte count, and SHA-256 digest. Object references verify governed bytes under
`.forge/objects/sha256/` independently of mutable project files. Closed references identify
accepted bytes; abandoned references are deliberately unaccepted.

```console
forge status --archive <initiative-id>
forge history --archive <initiative-id>
forge history --archive <initiative-id> --event-type initiative-closed
forge history --archive <initiative-id> --event-type initiative-abandoned
```

New manifests report `preliminary: false` with no preliminary limitations. Existing M1 closure
archives remain readable with their original guarantee. Closed and abandoned archives cannot
reopen; continued work uses `forge create --predecessor <archive-id>` to create a fresh successor.
