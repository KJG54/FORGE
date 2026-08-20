# Phase 1 authority and specification lifecycle residual-risk report

## Decision boundary

This report identifies residual risk after local verification of the exact Phase 1 candidate. It
does not claim that passing checks remove these risks, authenticate the operator, authorize a
release, or prove FORGE correct outside the exercised surfaces.

## Residual risks

### RR-1 — Windows symlink attack-surface coverage was not exercised locally

Nine symlink-security tests skipped because the current Windows account cannot create symbolic
links (`WinError 1314`). Existing Linux and macOS CI may exercise these cases after publication,
but no remote result is bound to this initiative and the owner directed publication without
waiting for CI.

- Impact: a local regression in symlink escape, symbolic lock, context, import, or discovery
  handling could be missed by this Windows run.
- Current control: the affected tests remain present; the limitation is explicit in the check,
  evidence, verification report, and acceptance scope.
- Follow-up: enable Windows Developer Mode or a strict `FORGE_REQUIRE_SYMLINK_TESTS=1` mode and
  require the security subset in a later hardening phase.

### RR-2 — Remote CI is not evidence for this publication action

The local quality gate and full suite passed, but no exact commit has yet run in GitHub Actions.
The owner explicitly directed publication without waiting for CI.

- Impact: platform, packaging, or clean-checkout failures may appear after the pull request is
  opened.
- Current control: publication will identify local results accurately and will not describe CI as
  passed.
- Follow-up: inspect CI separately after publication and govern any repair as a bounded successor
  if needed.

### RR-3 — Command receipt and identifier ergonomics can cause unsafe retries

Some successful mutations returned no immediate receipt text, and artifact listing did not expose
the revision UUID required by evidence registration.

- Impact: an operator or agent may retry a completed mutation, use the wrong identifier class, or
  misreport progress.
- Current control: stable idempotency keys, healthy canonical state, `forge status`, `forge next`,
  history, and list/show commands allowed recovery in this run.
- Follow-up: treat receipt reliability and executable next-command output as high-priority subjects
  of the extensive successor review.

### RR-4 — The authority model is accepted documentation, not authenticated identity

The new governing specification clarifies applicability and change control, but it does not turn
caller-declared owner attribution into authentication or make chat authoritative.

- Impact: a same-user process can still claim an operator label; readers could overinterpret an
  acceptance receipt as identity proof.
- Current control: the protocol, CLI receipts, governing specification, and reports state this
  limitation explicitly.

### RR-5 — Historical metadata includes inferred Git introduction dates

Thirty-six immutable ADRs contain no declared date. The effective-status catalog uses their Git
introduction dates and labels the source `git-introduction`.

- Impact: consumers could mistake repository-introduction dates for original decision dates.
- Current control: date provenance is machine-readable and explained in the ADR index README and
  accepted design judgments.

### RR-6 — Publication, installation, and release-identity drift remains out of scope

The repository remains public source with an unreleased development-project posture. Existing
release/version and installation contradictions identified in the roadmap were intentionally not
changed in Phase 1.

- Impact: beginners may still misread version `1.0.0`, publication metadata, or installation paths
  as a supported release.
- Current control: the current governing specification states the unreleased posture; later
  roadmap phases retain the unresolved findings.

### RR-7 — Broader reported FORGE malfunction is unclassified

The owner reports that FORGE is not working properly and requires extensive review. Phase 1 did
not perform a line-by-line runtime audit or reproduce a complete malfunction taxonomy.

- Impact: undiscovered correctness, lifecycle, performance, usability, or integration defects may
  remain.
- Current control: Phase 1 is narrowly contained, locally validated, and preserves detailed
  friction evidence for a successor.
- Follow-up: create a separate owner-authorized audit successor after this initiative is archived
  and published.

## Overall assessment

No observed residual risk invalidates the locally checked Phase 1 documentation and validation
candidate. The most consequential open risks are unexercised symlink defenses, publication before
remote CI observation, unreliable immediate mutation receipts, and the owner's broader
unclassified malfunction report. These are accepted only within this initiative's exact closure
and publication scope; they are not declared resolved.
