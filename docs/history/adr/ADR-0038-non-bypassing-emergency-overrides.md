# ADR-0038: Non-Bypassing Emergency Overrides

**Status:** Accepted

**Milestone:** M4 Increment 5

## Context

The public `EmergencyOverride` contract requires an affected requirement or gate, rationale,
residual risk, temporary or permanent status, review requirement, and owner actor. No supported
service persisted it.

An emergency record must not become a generic route around the constitutional
claim → check → evidence → owner acceptance sequence. The current workflow reducer intentionally
has no transition that can turn an override into a claim, passing check, evidence packet, gate
approval, acceptance, or completed step.

Risk acceptance is a separate public contract. Implementing it in the same increment would blur
the difference between declaring an emergency exception and accepting the resulting residual risk.

## Decision

Add owner-only:

```text
forge override record (--requirement <id> | --gate <id>)
  --rationale <reason> --residual-risk <risk>
  --permanence temporary|permanent
  --review-requirement <condition>
forge override show [<override-id>]
```

Exactly one target is required. Requirement IDs must exist anywhere in the locked workflow's
declared inputs, outputs, claims, checks, acceptance requirements, gates, transitions, artifact
classes, or evidence classes. Gate IDs must identify a declared locked-workflow gate. The persisted
target is qualified as `requirement:<id>` or `gate:<id>` to avoid ambiguous namespaces.

Recording creates one immutable `EmergencyOverride` under
`.forge/active/emergency-overrides/` and one state-neutral `emergency-override-recorded` event.
Both bind the exact locked workflow ID, version, and canonical digest. Permanence is restricted to
`temporary` or `permanent`.

An emergency override is explicit owner authority to record an exception, not authority for a
FORGE lifecycle transition. It cannot satisfy or fabricate any progression fact. Status reports
its unresolved residual risk. Successful closure refuses every emergency override until a later
explicit `RiskAcceptance` implementation binds and resolves that exact override. Explicit
abandonment remains available and preserves the unresolved override and stated risks.

Restart validation rejects an unknown target, ambiguous namespace, invalid permanence, non-owner
actor, wrong workflow, modified record, missing or additional record, forged digest, or successful
closure with an unresolved override. The record command uses ordinary locking, journal-bound
idempotency, conservative receipt recovery, and terminal archive validation.

## Consequences

Emergency exceptions become durable and inspectable without weakening false-completion defenses.
The system fails closed: adding an override introduces a closure blocker rather than removing one.

This increment does not implement risk acceptance, override withdrawal or expiry automation,
workflow transitions based on overrides, incident recovery, live cross-process cancellation,
executable pack providers, provider APIs, automatic verification or acceptance, or M5 work.
