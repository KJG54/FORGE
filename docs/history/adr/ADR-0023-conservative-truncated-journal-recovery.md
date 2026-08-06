# ADR-0023: Conservative Truncated Final-Record Recovery

**Status:** Accepted

**Milestone:** M2 Increment 12

## Context

The M2 hash chain detects incomplete final records, but Increment 4 deliberately limited
`forge recover` to derived snapshots backed by a completely valid journal. A process interruption
can leave bytes for a new final JSON Lines record after a fully synchronized valid prefix. Silently
dropping those bytes would erase evidence; treating every malformed record as truncation could
rewrite ambiguous or deliberately corrupted history.

## Decision

Extend the owner-only, locked, idempotent `forge recover` command with one journal case: a non-empty
final record whose JSON syntax is demonstrably truncated at end-of-file after a non-empty, complete,
fully valid M2 hash-chain prefix. Complete records missing only their newline, schema-invalid JSON,
malformed non-EOF data, blank records, invalid hashes or sequence links, legacy journals, and damage
without a complete prefix are ambiguous and remain immutable.

Before replacement, FORGE validates locked governance, every record and referenced object supported
by the valid prefix. It preserves the exact damaged journal, the exact truncated tail identity, and
every observed snapshot byte under governed recovery directories. A new `JournalRecoveryRecord`
binds those bytes, the last valid head, the owner reason, and snapshot condition.

FORGE constructs the valid prefix plus one owner-attributed `journal-recovered` event and validates
the complete candidate chain before atomically replacing `events.jsonl`. That replacement is the
commit point. Snapshot reconstruction and the idempotency receipt follow and can be resumed with
the same key without another recovery event. Preserved evidence is validated on every restart and
travels into any later archive.

Immutable archive journals are never repaired. The command does not infer or reconstruct a missing
valid event, recover another command's completion receipt, remove a lock, or repair middle-history
corruption.

## Consequences

An interrupted append can be recovered without hiding its bytes or weakening the hash chain.
Recovery remains intentionally narrow: some genuine truncations are refused when their cause is not
mechanically distinguishable from corruption. Owners retain the evidence and must resolve those
cases outside automatic FORGE mutation.

The new recovery record is an additive versioned contract and schema export. Existing snapshot
recovery records and events remain unchanged and fully readable.
