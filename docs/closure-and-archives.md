# Preliminary Closure and Archive Inspection

M1 Increment 7 implements successful closure only. It proves owner authority, lifecycle
termination, exact accepted-byte references, inspectable archive contents, and immutability through
supported commands. It does not implement abandonment, successors, hash chains, concurrent-writer
protection, idempotent retry, or interrupted-closure recovery; those were assigned to M2.
M2 Increments 1 through 3 now supply hash chains, locking, and completed-command idempotency, while
archive recovery, abandonment, and successors remain deferred.

## Closure gate

`forge close --summary <text>` is owner-only. Before recording closure, FORGE requires:

- every locked workflow step to be `completed`;
- a current, non-revoked, non-stale owner acceptance for every step;
- no active governed runs;
- every current artifact working file to match its registered revision;
- every current artifact revision and preserved object to pass restart validation;
- a non-empty final owner closure summary; and
- a clean Git worktree when `behavior.require_clean_git_for_close` is enabled.

The core remains domain-neutral. Review, lessons, and closure materials are required because the
locked pack declares them as outputs of governed steps, not because the closure service contains
software-specific role names.

```console
forge close --summary "All governed outputs are accepted for this initiative"
```

The resulting `ClosureRecord` is the final owner decision. The `initiative-closed` event binds it
to the current artifact revisions and final acceptance records. Replay produces the terminal
`closed` lifecycle state and rejects later events.

## Archive contents and exact bytes

Successful closure copies the complete validated active record into:

```text
.forge/archive/<initiative-id>/
```

The archive includes the final journal and snapshot, initiative identity, locked pack and workflow,
all governed records, closure record, and `archive-manifest.json`. The manifest inventories every
archived file by path, byte count, and SHA-256 digest. It also lists every current artifact revision,
its content-addressed object path, and whether the final acceptances bind that revision.

Preserved objects remain deduplicated under `.forge/objects/sha256/`. Archive inspection verifies
those exact bytes independently of mutable project files, so editing a working file after closure
does not rewrite accepted history.

## Read-only inspection

`forge status` lists archived initiative IDs when no initiative is active. Select one archive to
validate its manifest, governed records, terminal snapshot, journal, and preserved objects:

```console
forge status --archive <initiative-id>
forge history --archive <initiative-id>
forge history --archive <initiative-id> --event-type initiative-closed
```

`forge history` also supports exact step, actor, and run filters. These commands never mutate the
archive. Normal lifecycle commands address `.forge/active` only, and the terminal reducer refuses
events after closure. Direct `forge create` is blocked once an archive exists because predecessor
provenance requires the successor flow assigned to M2.

## Preliminary M1 limitation

Increment 7 deliberately does not claim atomic multi-file archival or recovery. The journal event
remains the governance commit point; the archive is then built in a staging directory and promoted
before active state is retired. If that later phase is interrupted, `forge status` reports an
integrity error and supported mutations remain disabled. FORGE does not silently repair, retry, or
remove the terminal record. M2 Increments 1 through 3 add hash chaining, locks, and idempotency;
interruption recovery and fully hardened atomic closure remain later work.
