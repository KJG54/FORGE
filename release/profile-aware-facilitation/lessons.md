# Profile-Aware Facilitation Lessons

Initiative: `fb1e3732-334f-4bb1-9e51-40dad0e9521b`
Step: `closeout`

## Governance Lessons

- Keep claim, check, evidence, FORGE verification, owner acceptance, Git commit, push, merge, and
  terminal close separate in both records and language.
- A generated context file can become stale across step transitions. `forge status` and `forge
  doctor` remain the practical state authority when context refresh has not been owner-directed.
- Direct workspace-agent claims need explicit `--operator direct-codex` or equivalent attribution;
  caller labels and same-user access remain spoofable and are not authentication.
- Owner-observed evidence should be recorded as human observation with limitations, not converted
  into an automated check.

## Verification Lessons

- M8 exposed a real review risk: testing generated-context skew was not the same as testing
  installed-CLI versus repository-source skew. Source declarations and installed resources both
  need to be checked when protocol identity matters.
- Additive schema fields can still change pack digests if default values enter the parsed model
  payload. Digest-neutral strips for empty guidance need direct tests with literal expected
  digests.
- Re-running the exact failing Windows long-temp-path test under a shorter temp path separated an
  environmental failure from a product regression.
- A factual issue inside a requirement can be handled by a recorded decision when the underlying
  verification standard is preserved and revising accepted artifacts would add churn without
  improving rigor.

## Collaboration Lessons

- Profile-aware guidance improved agent behavior, but richer presentation does not automatically
  make FORGE feel like learning by building.
- Human-facing artifacts need explicit review checkpoints before proceeding, especially plans and
  scope-shaping records.
- Approval flow should allow bounded low-risk batches, while owner-only gates remain exact,
  explicit, and separately accepted.
- Beginner-friendly work needs examples, small question batches, vision playback, and a clear
  split between review tasks and practice tasks.

## Product Lessons

- `software-basic` should be treated as a fast path for clear software implementation work, not as
  the default project companion for every domain.
- `research-basic` remains appropriate when research itself is the final deliverable, but it still
  needs richer guidance if it is expected to support teaching and project facilitation.
- FORGE needs a canonical product statement that frames it as a start-to-finish governed project
  companion for human-agent work.
- The next workflow should be experimental `project-basic`, not a redesign of every existing
  workflow at once.

## Successor Carry-Forward

The recommended successor should deliver:

1. Product vision statement for general project companionship.
2. Experimental `project-basic` workflow.
3. Interview and phase guidance for every step.
4. Basic templates for key artifacts.
5. Docs explaining when to use `project-basic`, `software-basic`, and `research-basic`.
6. Tests proving no authority drift.
7. Dogfood guide for owner-observed evaluation.

Open design question: decide whether revision belongs as an explicit workflow step or should use
existing FORGE rework/invalidation mechanics. Avoid making every successful project complete a fake
revision step.
