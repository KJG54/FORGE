# ADR-0040: Append-Only Risk-Acceptance Revocation

**Status:** Accepted

**Milestone:** M4 Increment 7

## Context

An exact `RiskAcceptance` resolves one emergency override's residual-risk closure blocker. The
FORGE constitution requires approvals and acceptance to be revoked through immutable history,
never by rewriting the original record. The owner needs to withdraw that authority when the risk
is no longer acceptable.

Revocation must not become a workflow invalidation or transition mechanism. A scope-stale
acceptance already authorizes nothing, while a current revoked acceptance should permit a later
fresh owner decision for the same unchanged override.

## Decision

Add configured-owner-only:

```text
forge risk revoke <acceptance-id> --reason <reason>
```

Reuse the public `ApprovalRevocation` contract and shared `.forge/active/revocations/` directory.
`approval_id` identifies one exact current `RiskAcceptance`. The revocation's affected records bind
the acceptance and emergency override; its affected digests begin with the canonical acceptance
digest followed by the acceptance's exact override and locked-workflow digests.

The state-neutral `risk-acceptance-revoked` event records the same relationship. It does not add
the acceptance to workflow staleness, change steps, gates, runs, claims, checks, evidence,
verification, ordinary acceptance, or lifecycle state.

Only an unrevoked, non-stale risk acceptance resolves its override's successful-closure blocker.
Revocation reopens that exact blocker. A later new acceptance may bind the same current override.
Duplicate revocation and revocation of scope-stale acceptance are refused.

Restart validation rejects unknown acceptance or override references, non-owner actors, altered
records, stale or duplicate revocations, wrong record or digest binding, missing or additional
files, forged events, or successful closure that relies on revoked authority. The command uses
ordinary locking, idempotency, conservative receipt recovery, and archive validation.

## Consequences

Residual-risk authority becomes explicitly withdrawable without weakening immutable history or
the claim → check → evidence → owner acceptance sequence. Operators can distinguish current,
revoked, and stale acceptance through read-only inspection.

This increment does not implement general decision withdrawal, emergency-override withdrawal or
expiry, automatic review-condition monitoring, workflow transitions based on overrides, incident
recovery, live cross-process cancellation, executable pack providers, provider APIs, automatic
verification or acceptance, or M5 work.
