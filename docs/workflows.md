# Packs, Initiative Creation, and Manual Runs

M1 Increment 3 adds the first domain-neutral workflow services. It does not yet make worker claims,
checks, evidence, or acceptance available.

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

`forge begin <step>` starts only a `ready` step, records a durable manual `RunRecord`, and moves the
step to `in_progress`. A running process or manual effort is not a claim, check, evidence packet, or
acceptance decision.

Conditioned transitions remain blocked in this increment. In particular, a caller cannot claim
that `claim-recorded`, check, evidence, or acceptance conditions are satisfied. Increment 4 will
derive applicable conditions from governed artifact, claim, check, and evidence records.

Use read-only commands after any process restart:

```console
forge status
forge next
```

Both commands reload locked records, replay the complete journal, compare `state.json`, and report
integrity errors without silently repairing them.

## Deferred guarantees

This increment does not add artifact or evidence registration, completion claims, acceptance,
handoffs, imports, closure, hash chaining, recovery, cross-process locking, or idempotent retry.
Those remain assigned to later approved increments or M2.
