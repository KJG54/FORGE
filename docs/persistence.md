# Journal and Materialized State

M1 Increment 2 establishes the preliminary filesystem persistence boundary without claiming the
M2 guarantees that do not yet exist.

## Authority and transaction order

`events.jsonl` is the mutation commit point. Each schema-versioned event is deterministic JSON,
occupies exactly one newline-terminated record, belongs to one initiative, and has a sequence
number exactly one greater than the preceding event. M1 rejects duplicate event IDs, mixed
initiative IDs, partial records, invalid schemas, and event hashes that would falsely imply M2
hash chaining.

A governed mutation follows this order:

1. Read and validate the existing journal and snapshot.
2. Refuse the mutation when replay and `state.json` disagree.
3. Validate the candidate event as the next record.
4. Append, flush, synchronize, and reread the journal record. At this point the event is committed.
5. Replay the full journal through the caller-supplied state reducer.
6. Write `state.json` to a temporary file beside the destination.
7. Validate and synchronize the temporary snapshot, atomically replace the destination, and
   verify its exact bytes.
8. Compare the resulting snapshot with deterministic replay.

This ordering cannot make two files atomically durable as one operation. If a process stops after
the journal commit but before snapshot replacement, the journal remains authoritative and the
missing or stale snapshot is reported as `integrity_error`. FORGE does not silently normalize the
snapshot.

## Replay boundary

The storage layer owns sequence validation, replay mechanics, journal-head projection, snapshot
serialization, and comparison. It accepts a reducer function rather than interpreting workflow
events itself. The domain-neutral lifecycle reducer and authorization rules belong to M1
Increment 3.

## M2 Increment 1 integrity chain

New journals use the canonical serialization and SHA-256 chain defined by
[ADR-0012](adr/ADR-0012-canonical-event-hash-chain.md). Every read validates event content hashes,
previous-hash links, sequence and initiative identity, and complete-record termination. Replay
binds `state.json` to the exact journal-head sequence and hash.

Complete M1 journals with empty hash fields remain readable but are read-only until an explicit
later migration preserves the original bytes and records provenance. Cross-process locking,
idempotent retry, recovery, stale-lock handling, and interruption hardening remain later M2 work.

## Increment 7 archive layer

Successful closure appends an owner-authorized terminal event and writes the final snapshot before
building a complete archive in a sibling staging directory. `archive-manifest.json` covers every
archived file by exact digest and size and references the already content-addressed artifact objects.
After validation, the staged archive is promoted and `.forge/active` is retired to an empty
directory.

This ordering provides deterministic, inspectable successful closure and command-level archive
immutability. It does not make the journal, snapshot, archive promotion, and active-state retirement
one atomic transaction. An interruption is reported as an integrity error and is never silently
repaired. Hash chains, cross-process locks, idempotent close retries, and interrupted-archive
recovery remain explicit M2 work.
