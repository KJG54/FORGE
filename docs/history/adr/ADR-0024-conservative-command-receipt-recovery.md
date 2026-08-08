# ADR-0024: Conservative Interrupted-Command Receipt Recovery

**Status:** Accepted

**Milestone:** M2 Increment 13

## Context

ADR-0014 deliberately blocks mutation when journal events exist without their completion receipt.
That preserves evidence and prevents a retry from duplicating a committed effect, but it also
requires an explicit way to distinguish a completed command from a partial multi-event transaction.
Hash-valid events alone do not prove that every event intended by a command was committed.

## Decision

Add an owner-only, locked, idempotent `forge recover-command` operation. It accepts the interrupted
command's key separately from the recovery operation's own key and requires a durable owner reason.
It may reconstruct a receipt only when all of these facts are mechanically established:

- exactly one unrelated key is incomplete;
- its events are one contiguous group at the active journal tail;
- the command has a registered complete event-type pattern, including every event of a known
  multi-event command;
- the complete hash chain, locked governance, records, preserved objects, and replayed state
  validate; and
- `state.json` is either the exact pre-command view, the exact current view, or is absent before
  an initial creation event.

The recovery writes a `CommandRecoveryRecord`, appends one owner-attributed `command-recovered`
event as the commit point, refreshes the derived snapshot, and atomically writes the reconstructed
receipt bound to the exact original event references. The recovery event and receipt use distinct
idempotency keys. A same-request retry may finish the snapshot and both receipts without adding
another recovery event.

Commands with specialized multi-phase recovery, partial event patterns, archived targets, multiple
incomplete keys, existing or damaged receipts, non-tail groups, and changed snapshot observations
are refused. Recovery never invents a missing business event, repeats an effect, edits the journal,
or deletes a lock.

## Consequences

A command that completed its registered journal pattern can be made replayable without treating Git,
a snapshot, or caller memory as authoritative. Commands interrupted between required events remain
blocked rather than being falsely marked complete. Adding a future mutation command requires an
explicit event-pattern decision before generic receipt recovery can apply to it.
