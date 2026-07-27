# ADR-0042: Formal Run Cancellation Records

**Status:** Accepted

**Milestone:** M4 Increment 9

## Context

FORGE already represented cancellation with a terminal `run-cancelled` event and derived the
workflow destination from the locked step policy and run side-effect class. That event made the
transition replayable, but it did not preserve a separately inspectable governance record binding
the exact immutable run, actor, policy, risk classification, and any terminal managed-execution
fact.

Cancellation must not claim that a separately running provider process stopped. FORGE currently
executes adapters synchronously and has no cross-process process handle or background supervisor.
It can therefore cancel a manual run, which has no FORGE-managed process, or formally close an
adapter run only after its immutable `adapter-run-executed` event proves the managed execution is
already terminal.

## Decision

Add the public immutable `RunCancellationRecord` and persist it at:

```text
.forge/active/run-cancellations/<record-id>.json
```

The record binds the exact run ID and canonical run digest, step, reason, actor, source and
destination states, locked `CancellationBehavior`, and run `SideEffectClass`. For an
adapter-attributed run, it additionally binds the preceding terminal execution event ID and
hash. The `run-cancelled` event binds the cancellation record ID and canonical digest plus the
same run and execution facts.

The run worker or configured repository owner may cancel an active run. Safe manual work returns
to `ready` unless the locked workflow requires owner review. External or sensitive work always
moves to `blocked`. Adapter-attributed work is refused unless exactly one prior hash-sealed
`adapter-run-executed` event exists. This is formal governance closure of already-terminal work,
not a request to signal or kill a live process.

The cancellation record is written before its event commit. A pre-commit failure removes only the
new record; once the event is committed, ordinary interruption recovery preserves it. Duplicate
cancellation is refused because the run is no longer active. Restart validation recomputes every
authorization, policy, state, identity, ordering, and digest relationship and rejects missing,
additional, altered, or misbound records.

Read-only run inspection exposes the cancellation record and terminal execution binding. Terminal
archives preserve the new record directory with the rest of governed history.

## Consequences

Operators gain an independently inspectable, hash-bound explanation of why cancellation was
allowed and what workflow effect it had. Managed adapter execution cannot be presented as stopped
without prior terminal evidence, while manual runs remain cancellable because FORGE never started
a process for them.

The public schema bundle grows from 48 to 49 models. This increment does not implement live
cross-process cancellation, background process control, operating-system signaling, automatic
crash recovery, structured local security-event reporting, incident recovery, provider APIs,
automatic verification or acceptance, or M5 work.
