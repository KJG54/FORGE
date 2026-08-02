# Local Production-v1 L6 - Provenance and Owner Ceremony

## Authorized scope

- distinguish the authority actor from the caller-declared local operator on new claims;
- visibly identify direct Codex, direct Claude, owner-shell, contributor, registered-adapter, and
  service operators without treating a label or session reference as authentication;
- preserve legacy claims, journal digests, active repositories, and immutable archives;
- present exact owner-gate command templates and consequences in `forge next`, transaction
  receipts, and the versioned direct-agent protocol; and
- preserve append-only rejection, invalidation, revocation, scope-change, closure, and abandonment
  paths rather than inventing a universal rework transition.

## Contract and compatibility

`Claim` gains optional `operator_type` and `operator_session_reference` fields. New claim creation
always resolves an operator type. Direct workspace agents declare `direct-codex` or
`direct-claude`; governed adapter runs resolve to `registered-adapter`; ordinary owner-shell and
contributor paths retain distinct labels. The existing actor remains the authority identity used
by authorization checks.

Legacy claims deserialize with both fields absent. Claim digest canonicalization omits the absent
operator fields for those records, preserving historical digests, while new claims bind their
operator provenance into the digest and matching journal metadata. The public schema registry
remains at 51 models and schema version `1.0` remains additive and backward compatible.

## Ceremony and threat model

The direct-agent protocol advances to `1.1.0`; the `1.0.0` resource remains installed for
historical reference. Owner-personal actions now have an exact command template and an explicit
consequence. `forge next` expands currently legal owner gates, and transaction receipts attach the
same details when the resulting state reaches one.

An owner can run a presented command personally or explicitly direct an agent to run it. That
ceremony is a collaboration boundary, not an identity proof. Operator types and session references
are caller-declared, spoofable same-user attribution and never replace owner checks.

## Validation boundary

Focused L6 validation covers legacy digest compatibility, direct-agent and adapter provenance,
receipt and history rendering, exact owner-gate presentation, versioned protocol integrity, and
the existing acceptance, revocation, invalidation, scope-amendment, closure, and abandonment
semantics most directly touched by this increment. Repository-wide CI, distribution, and complete
milestone journey validation remain deferred to Local Production-v1 closeout under the owner's
direction.

Passing focused checks establishes only L6 implementation evidence. The encompassing Local
Production-v1 `implement` step remains in progress, and L7 and later increments remain outside
this change.
