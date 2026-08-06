# ADR-0037: Owner-Reviewed Workflow Deviations

**Status:** Accepted

**Milestone:** M4 Increment 4

## Context

The public `WorkflowDeviation` contract can describe a difference between the locked workflow and
what actually occurred, but no supported service persisted or enforced that fact. Treating a
deviation as ordinary prose would allow successful closure to hide it. Treating the record itself
as an override would be worse: observation would silently become authorization.

FORGE already has immutable owner decisions, supersession, digest binding, staleness, restart
validation, idempotency, and archive preservation. Deviation review should reuse those facts rather
than introduce another mutable approval flag.

## Decision

Add owner-only:

```text
forge deviation record --declared <behavior> --actual <behavior>
  --rationale <reason> --review-requirement <condition>
forge deviation review <deviation-id> --option <choice>...
  --outcome <choice> --rationale <reason>
forge deviation show [<deviation-id>]
```

Recording creates one immutable `WorkflowDeviation` under
`.forge/active/workflow-deviations/` and one state-neutral
`workflow-deviation-recorded` event. The record binds the exact locked workflow ID, version, and
canonical digest. Declared and actual behavior must differ. The configured owner is the only
supported recording authority.

A deviation grants no transition, waiver, gate approval, acceptance, capability, scope change,
override, or risk acceptance. Recording it does not change a step or run state.

Review reuses `DecisionRecord` with the fixed type `workflow-deviation-review` and exactly one
affected deviation ID. A deviation is resolved only while that review decision is current,
non-stale, and open. A second current review is refused. Superseding or invalidating the review
without a replacement review for the same deviation reopens it.

Open deviations appear in status and block successful closure. They do not block explicit
abandonment, because abandonment is the owner-authorized terminal path for unfinished work and
unresolved risks. Both reviewed and open deviations remain immutable history and are preserved in
terminal archives.

Restart validation rejects an unknown deviation, wrong workflow, non-owner actor, modified record,
missing or additional record, forged digest, duplicate current review, or closure containing an
unresolved deviation. Idempotent record and review commands retain the existing journal-bound
command-recovery guarantees.

## Consequences

Workflow differences become durable and closure-relevant without becoming an authorization
shortcut. Review remains part of the ordinary decision and supersession model, so there is one
source of decision authority.

This increment implements workflow deviations only. Emergency overrides, risk acceptance, general
decision withdrawal, incident recovery, live cross-process cancellation, executable pack
providers, provider APIs, automatic verification or acceptance, and M5 work remain later
boundaries.
