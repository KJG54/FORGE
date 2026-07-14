# Packs, Initiative Creation, and Manual Runs

M1 Increment 3 adds the first domain-neutral workflow services. M1 Increment 4 supplies worker
claims, checks, and evidence through the separate services documented in
[`artifacts-and-evidence.md`](artifacts-and-evidence.md). M1 Increment 5 supplies owner acceptance,
revocation, decisions, and invalidation.

## Declarative pack loading

FORGE discovers the bundled `software-basic` pack and repository-local pack paths configured in
`forge.yaml`. Every candidate is treated as untrusted input and must pass bounded safe-YAML parsing,
strict Pydantic contracts, workflow reachability checks, supported authority rules, file declaration
checks, and a deterministic SHA-256 digest.

Increment 3 pack digests bind the manifest and workflow definitions. Additional template,
explanation-file, and data-resource bytes are rejected until a later increment includes those exact
bytes in the lock digest. Stray files, executable suffixes, symbolic links, YAML aliases, invalid
schemas, duplicate identities, and digest mismatches are refused. Pack loading never imports or
executes pack content.

Inspecting a pack does not trust it:

```console
forge pack list
forge pack validate software-basic
```

## Owner-authorized initiative creation

One active initiative is allowed. The configured owner must explicitly confirm data-only trust for
the exact selected pack version:

```console
forge create "Deliver the approved change" \
  --scope "Only the declared local change" \
  --trust-pack-data
```

The option does not approve any executable capability. Creation writes immutable initiative,
pack-trust, pack-lock, and workflow-lock records before committing the `initiative-created` journal
event and its reconstructable snapshot. If a failure occurs before the journal commit, newly created
records are removed. If the journal commits first, it remains authoritative and any incomplete
snapshot is reported as an integrity error under the Increment 2 transaction model.

## Transitions and manual runs

The locked workflow determines step order, states, actor classes, authority requirements,
conditions, and events. Replay validates those rules again from the journal; `state.json` cannot
authorize a transition by itself.

`forge begin <step>` starts a `ready` step or explicitly reworks an `invalidated` step, records a
durable manual `RunRecord`, and moves the step to `in_progress`. A running process or manual effort
is not a claim, check, evidence packet, or acceptance decision.

Conditioned transitions cannot be asserted by a caller. FORGE derives `claim-recorded`,
`required-checks-passed`, `required-evidence-registered`, and `owner-acceptance-recorded` from
governed records.

Use read-only commands after any process restart:

```console
forge status
forge next
```

Both commands reload locked records, replay the complete journal, compare `state.json`, and report
integrity errors without silently repairing them.

## Deferred guarantees

The implemented M1 surface still excludes handoffs, imports, closure, hash chaining, recovery,
cross-process locking, and idempotent retry. Those remain assigned to later increments or M2.
