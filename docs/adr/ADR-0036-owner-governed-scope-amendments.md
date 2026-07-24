# ADR-0036: Owner-Governed Scope Amendments

**Status:** Accepted

**Milestone:** M4 Increment 3

## Context

An initiative's creation record intentionally preserves its original declared scope. Material
scope changes therefore need a new fact rather than an edit. The public `ScopeAmendment` contract
already described affected requirements, artifacts, checks, gates, acceptances, and a workflow
return step, but no supported service could create or enforce it.

Treating an amendment as prose alone would leave already accepted work current under requirements
that no longer govern it. Allowing callers to choose individual stale records would be equally
unsafe because a partial list could retain unsupported progression.

## Decision

Add owner-only:

```text
forge scope amend --scope <complete-effective-scope> --rationale <reason>
  --return-to <step> --requirement <id> [--requirement <id> ...]
  [--artifact <logical-artifact-id> ...]
```

`--scope` is the complete effective scope after the amendment, not a patch. Affected requirement
IDs must exist in the locked workflow. Affected logical artifact IDs must be current initiative
artifacts. The declared return step must exist.

FORGE derives, rather than accepts from the caller:

- the return step and all workflow descendants;
- current claims, checks, evidence, acceptances, and dependency-bound decisions made stale;
- affected check-result and acceptance IDs;
- affected workflow gates; and
- which worked steps become `invalidated` and untouched descendants reset to `pending`.

A ready or previously worked return step becomes `invalidated`, so the owner can restart it
explicitly through the existing rework transition. A never-eligible return step remains `pending`
until its prerequisites complete; an amendment cannot expose a premature begin action. An active
governed run in the affected region blocks the amendment and must first receive its own terminal
cancellation event. Scope amendment does not silently terminate a run.

One immutable `ScopeAmendment` under `.forge/active/scope-amendments/` and one `scope-amended`
journal event bind the complete effective scope, owner, rationale, exact affected requirements and
artifacts, derived invalidation set, current affected artifact digests, and workflow return point.
The latest validated amendment supplies the approved-scope field in newly generated canonical
agent context. Earlier initiative and amendment records remain unchanged.

An amendment grants no transition condition. It cannot create a claim, passing check, evidence,
gate approval, verification transition, acceptance, capability approval, override, or risk
acceptance. Restarted work must produce all current support again.

## Consequences

Material scope change becomes explicit, reviewable, restart-safe, idempotent, recoverable, and
archive-preserved. Cross-record validation reconstructs the pre-amendment state and rejects an
unknown requirement or artifact, forged derived effect, non-owner actor, affected live run,
changed record, additional record, or event/record mismatch.

This increment implements scope amendment only. Workflow deviation, emergency override, risk
acceptance, general decision-revocation hardening, and incident recovery remain later M4 work.
