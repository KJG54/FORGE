# Canonical Transaction Receipts

FORGE renders one concise receipt after each supported high-frequency governed mutation. The
receipt is a validated view of the durable journal transaction and resulting state; it is not a
new persisted record or an additional source of authority.

```text
Recorded -> <committed event facts>; transaction=<command>:<key> [sequence <start>-<end>; events <ids>]
Means    -> repository=<state>; integrity=healthy; ...; blockers=<facts>; legal_actions=<actions>
```

`Recorded` identifies the exact journal sequence range and every event ID committed by the atomic
command. A multi-event command still receives one receipt. Use `forge history` and the applicable
`show` command when event- or record-level detail is needed.

`Means` is derived only after FORGE validates the replayed repository state. It reports the
resulting lifecycle position, current blockers, and legal actions. It does not assert that a worker
claim is true, that a check establishes evidence, or that the owner accepted the result.

## Replay and refusal

An idempotent replay names the original command transaction, repeats its original exact event
range and IDs, and states `zero new events`. It does not append another event.

A refused command has no `Recorded` line because FORGE did not establish a committed transaction.
Its single `Means` line says `validated no new governed events` only when healthy state before and
after the attempt proves the governed position is identical. If that proof is unavailable, the
receipt says the governed commit state is not asserted and directs the operator to diagnostics and
history.

An unsuccessful governed outcome can still be a successful commit. For example, recording a
failed check emits `Recorded` because the failed outcome is itself an authoritative journal fact.

## Migrated commands

L3 applies the canonical renderer to these high-frequency mutation paths:

- initiative creation, begin, complete, verify, pause, and resume;
- artifact add and revise;
- manual, structural, and executable check recording;
- evidence registration;
- acceptance record and revoke;
- decision record and withdraw; and
- scope amendment.

Other mutation commands retain their existing output until intentionally migrated. They do not
emit a second `Recorded`/`Means` dialect. Read-only inspection commands, including `status`,
`history`, and record-specific `show` commands, retain their detailed output.

## Authority and compatibility

The persisted completion receipt under `.forge/idempotency/` remains the durable binding between
one request and its exact event hashes. The CLI transaction receipt is reconstructed from that
validated completion receipt, the referenced journal events, and replayed status. L3 adds no
public model, schema, journal event, migration, workflow-lock field, pack field, or archive field.

Agents may quote FORGE's `Recorded` and `Means` lines verbatim. Any separate interpretation or plan
should be labeled `Read` or `Next` and remains fallible agent output.
