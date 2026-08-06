# ADR-0056: Tracked Self-Dogfood Framework-Change Workflow

**Status:** Accepted

**Milestone:** M6 Increment 7

## Context

The Production-v1 roadmap requires FORGE to govern its own release through a framework-change
workflow. A temporary synthetic rehearsal would show that generic services work, but it would not
make the remaining release work resumable, inspectable, or subject to the same owner gates offered
to users.

Using the bundled software workflow is possible, but its generic output roles do not make release
validation, friction, residual risk, and readiness explicit. Automating the complete workflow would
be worse: a tool performing the work cannot truthfully manufacture configured-owner acceptance or
resolve its own release-blocking risks.

## Decision

Initialize the FORGE source repository itself and track its live governance state.

- A repository-local, data-only `forge-framework-change` pack declares five release-specific steps.
- The pack declares no executable capabilities and gains only exact locked-data trust.
- `forge.yaml`, governed `.forge/` state, the source pack, and release artifacts are versioned.
- `.forge/local/` remains ignored and outside governed acceptance authority.
- Clean Git state is required before successful closure.
- Increment 7 advances the first step through claim, check, evidence, and verification, then stops
  at `awaiting_acceptance`.
- Only a later explicit configured-owner decision may accept that scope.
- The same initiative carries the remaining M6 implementation, validation, friction, risk,
  readiness, and lessons evidence into closeout.

## Consequences

M6 release work now exercises real discovery, configuration, local-pack validation, pack locking,
data trust, journal replay, snapshots, preserved objects, artifact records, claims, checks,
evidence, derived context, owner blockers, and hybrid Git policy in the FORGE repository.

The tracked state is intentionally mutable through supported commands until terminal archival.
Changes to accepted artifacts create new revisions and may invalidate downstream authority. Future
tests and documentation must inspect semantic invariants rather than freeze random UUIDs or
timestamps.

The initiative cannot progress past its first owner gate without an explicit owner decision. This
is useful evidence that dogfooding preserves authority, but it means Increment 8 begins only after
that decision.

## Rejected alternatives

- **Temporary dogfood fixture only.** This would not govern or preserve the real release work.
- **Use `software-basic` unchanged.** It would work mechanically but obscure release-specific
  validation, friction, residual risk, and readiness outputs.
- **Complete and accept every step automatically.** This would collapse worker claims, checks,
  evidence, and owner acceptance into a scripted fiction.
- **Store dogfood records outside Git.** That would undermine review, resumption, and archive
  evidence while duplicating the ignored local-data boundary.
