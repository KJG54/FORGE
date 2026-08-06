# Local Production-v1 L5 - Step-aware Mentoring

## Authorized scope

- add optional, default-empty per-profile explanation content to `StepDefinition`;
- prefer locked active-step guidance while retaining locked workflow-level fallback;
- author the Mentored path for the six `software-basic` steps without building a mechanical
  profile-by-step matrix;
- surface advisory guidance on initiative creation, first step encounter, and warm recap; and
- preserve old workflow-lock digests, schema-`1.0` loading, permissions, transitions, and outcomes.

## Contract and compatibility

The new step field is an additive schema-`1.0` field with an empty-map default. Pack digest
canonicalization omits that field when empty, so a valid pre-L5 pack or locked workflow retains its
historical digest after parsing. When content is present it remains exact digest-bound pack data.
Pack validation rejects step profiles that lack a workflow-level fallback.

`ActiveInitiative.explanation` remains a string for existing callers. Its new selection rule is
step content first and workflow content second; `explanation_guidance` additionally labels the
source and whether the current journal contains a prior event for that step. `forge create` shows
the first-step guidance and `forge recap` shows the current guidance as a warm-session aid. Both
surfaces explicitly label mentoring advisory and skippable.

Only the changed bundled software pack advances to `software-basic@0.5.0` and receives a new exact
digest. `research-basic@0.4.0` demonstrates fallback without content churn. The historical public
M7 compatibility artifact and both predecessor archives remain untouched.

## Governance boundary

Explanation selection reads locked pack data and the existing journal only. It writes no record,
adds no event, and cannot satisfy a requirement, choose a transition, authorize an actor, supply
evidence, verify work, or accept an outcome. First encounter is presentation context rather than a
new persisted state dimension; invoking warm recap is itself the explicit after-gap trigger.

## Validation boundary

Focused L5 acceptance covers the additive schema default, exact old-digest compatibility, old lock
loading, step precedence, workflow fallback, authored software guidance, pack validation, novelty
labeling, recap presentation, and version consistency. Repository-wide lint, typing, tests, build,
CI, and release health checks remain deferred to Local Production-v1 closeout under the owner's
validation direction.

Passing focused checks establishes only L5 implementation evidence. The encompassing Local
Production-v1 `implement` step remains in progress, and L6 and later increments remain outside this
change.
