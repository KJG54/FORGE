# Project-basic lessons

## What worked

- A new bundled pack could be delivered as declarative data using existing generic loader,
  lifecycle, template, digest, and distribution mechanisms.
- Treating research as mandatory but allowing a documented no-new-research-needed result kept the
  fixed DAG honest without inventing optional branching semantics.
- Native artifact revision, invalidation, and rework correctly express created-work revision
  without adding a misleading mandatory `revise` phase.
- Guidance and documentation can make the experience more approachable while keeping authority
  and acceptance boundaries mechanically unchanged.

## What to retain

- Keep pack identity append-only and explicitly pin existing bundled pack digests.
- State clearly that templates are read-only reference resources, conversational authorization
  envelopes are revocable presentation, and evaluation findings do not auto-transition work.
- Separate structural validation from subjective dogfood observations and release authority.
- Treat a clean-worktree closure rule as a Git/FORGE handoff checkpoint: a scoped commit (and an
  owner-directed push, if wanted) preserves history before archival without becoming acceptance or
  release authority.

## Follow-up signals, not commitments

- Owner-observed dogfood may reveal whether dedicated CLI guidance rendering is worth a bounded
  successor.
- Stable full-suite or CI evidence would reduce the remaining validation-observability limitation.
- Any release candidate, tag, publication, new CLI command, or core semantic change requires a
  separate owner-authorized scope and its own governance sequence.
