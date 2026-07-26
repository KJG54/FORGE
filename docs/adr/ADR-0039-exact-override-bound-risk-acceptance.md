# ADR-0039: Exact Override-Bound Risk Acceptance

**Status:** Accepted

**Milestone:** M4 Increment 6

## Context

Emergency overrides deliberately add a successful-closure blocker and cannot waive FORGE's
claim → check → evidence → owner acceptance sequence. The existing public `RiskAcceptance`
contract needs an operational boundary that can acknowledge residual risk without becoming a
general completion or transition authority.

An acceptance must not survive a change to the requirement or gate that justified its override.
It must also remain independently reconstructable from immutable records and the journal.

## Decision

Add configured-owner-only:

```text
forge risk accept <override-id>
  --rationale <reason>
  --residual-impact <impact>
  [--review-condition <condition>]
forge risk show [<acceptance-id>]
```

One `RiskAcceptance` binds one exact current `EmergencyOverride`. It copies the override's
residual risk and binds the canonical override digest followed by the override's locked-workflow
digest. Its state-neutral `risk-accepted` event carries the same exact relationship. Only one
current, non-stale acceptance may exist per override.

Risk acceptance resolves only the successful-closure blocker introduced by that exact override.
It does not create or replace a claim, check, evidence packet, gate approval, verification,
ordinary owner acceptance, completed step, or terminal transition. Closure independently proves
that every current override has one current risk acceptance and still enforces every ordinary
workflow requirement.

A scope amendment affecting the override's qualified requirement or derived gate stales the
override and its risk acceptance together. The stale override cannot receive another acceptance;
the changed governing scope requires a new override and a new owner decision.

The optional review condition is durable text for manual governance. This increment does not claim
to monitor external conditions, expire records automatically, or revoke an acceptance.

Restart validation rejects unknown or stale override references, non-owner actors, altered risk or
digests, duplicate current acceptances, missing or additional files, forged events, invalid scope
staleness, or successful closure with unresolved current override risk. Recording uses ordinary
locking, idempotency, conservative receipt recovery, and terminal archive validation.

## Consequences

Owners can explicitly accept a bounded residual risk without weakening false-completion defenses.
The exact digest relationship and scope-coupled staleness prevent old review from governing
changed requirements.

This increment does not implement general decision withdrawal, risk-acceptance revocation,
automatic review-condition monitoring, override expiry, workflow transitions based on overrides,
incident recovery, live cross-process cancellation, executable pack providers, provider APIs,
automatic verification or acceptance, or M5 work.
