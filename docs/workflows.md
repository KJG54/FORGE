# Packs, Initiative Creation, and Manual Runs

M1 Increment 3 adds the first domain-neutral workflow services. M1 Increment 4 supplies worker
claims, checks, and evidence through the separate services documented in
[`artifacts-and-evidence.md`](artifacts-and-evidence.md). M1 Increment 5 supplies owner acceptance,
revocation, decisions, and invalidation.
M1 Increment 7 adds successful terminal closure after every declared step is complete and currently
accepted.

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

Use read-only commands after any process restart or to inspect a closed archive:

```console
forge status
forge next
forge history
forge status --archive <initiative-id>
forge history --archive <initiative-id>
```

Both commands reload locked records, replay the complete journal, compare `state.json`, and report
integrity errors without silently repairing them.

## Explanation profiles and run cancellation

M1 supports Standard and Guided presentation. The selected profile chooses only locked pack
explanation text; transition definitions, authority, record requirements, and materialized next
actions are identical.

Run records remain immutable. `forge run list|show` derives effective `running`, `succeeded`, or
`cancelled` state from the journal. `forge run cancel` records a terminal cancellation event and
never implies step completion: safe work may return to `ready`, while the workflow's stricter
cancellation rule or external/sensitive side effects move the step to `blocked` for owner review.

## Atomic successful closure boundary

Successful closure is owner-only and derives readiness from the locked workflow, current
acceptances, exact artifact revisions, and preserved objects. M2 Increment 6 adds validated atomic
archive promotion and resumable active-state retirement. Repeating an interrupted close with the
same idempotency key completes the existing terminal transaction rather than creating a new event.
Closed archives never reopen through supported commands. Successors, migration, and unrelated
interruption recovery stay deferred.

## Atomic abandonment boundary

Abandonment is a separate owner-only terminal decision. `forge abandon` requires a reason, an
unfinished-work summary, and at least one unresolved-risk statement. It may start from active or
paused state, but never while a governed run remains active. The owner must cancel such runs first,
making their outcome explicit in history.

Abandonment does not require passed checks, completed steps, or current acceptances. Its event and
record preserve the unfinished step set and current governed artifact revisions, then use the same
validated resumable archive transaction as closure. Its manifest is terminal `abandoned`, carries
only abandonment IDs, and marks every object reference unaccepted. Abandoned archives never reopen.
Successor creation remains deferred.
