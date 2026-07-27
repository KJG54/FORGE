# ADR-0041: Append-Only Decision Withdrawal

**Status:** Accepted

**Milestone:** M4 Increment 8

## Context

FORGE decisions are immutable governance facts. Supersession can replace one current decision with
another, but operators also need an unambiguous way to remove a decision's current authority when
no substantive replacement is ready. Ad hoc decision types can reopen a workflow-deviation review,
but they do not prove that the replacement means withdrawal or bind the exact prior decision.

Withdrawal must preserve history, fail closed, and avoid inventing a second mutable status store or
a new approval contract. It must not become a workflow transition or restore an older decision.

## Decision

Add configured-owner-only:

```text
forge decision withdraw <decision-id> --reason <reason>
```

Reuse `DecisionRecord`, `DecisionSupersession`, and the `decision-superseded` event. The operation
creates a reserved `decision-withdrawal` replacement with fixed question, options, and outcome. Its
affected records contain the prior decision followed by that decision's affected records. Its bound
digests begin with the prior decision's canonical digest followed by the prior bindings.

Only a current decision may be withdrawn. A stale or superseded decision already lacks current
authority and is refused. A withdrawal record cannot itself be withdrawn; later governance may
record a new decision, but withdrawal never resurrects earlier authority.

Replay applies ordinary supersession: the prior decision leaves `open_decision_ids`, becomes stale,
and the withdrawal audit record becomes current. No step, gate, run, claim, check, evidence,
verification, acceptance, or lifecycle state changes. Because workflow deviations require a
current decision of the exact type `workflow-deviation-review`, withdrawing such a review
automatically reopens that deviation and its successful-closure blocker.

Restart validation recomputes the reserved semantics, exact affected records, prior-decision
digest, inherited bindings, owner identity, and supersession relationship. Read-only inspection
derives `current`, `withdrawn`, `superseded`, or `stale` status from the validated history.
Ordinary locking, idempotency, conservative command-receipt recovery, and archive preservation
apply unchanged.

## Consequences

Owners can remove obsolete decision authority through one explicit command without deleting or
rewriting evidence. The existing decision/supersession contracts remain the single persistence
model, so no new schema or mutable current-status file is introduced.

This increment does not implement broader run-cancellation hardening, live cross-process
cancellation, structured local security-event reporting, emergency-override withdrawal or expiry,
automatic review-condition monitoring, incident recovery, executable pack providers, provider
APIs, automatic verification or acceptance, or M5 work.
