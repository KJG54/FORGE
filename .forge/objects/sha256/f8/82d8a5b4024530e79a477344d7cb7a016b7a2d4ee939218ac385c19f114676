# FORGE Release-Candidate Dogfood Scope

## Objective

Use FORGE itself to govern the remaining M6 release-candidate work through a repository-local
framework-change workflow, preserving an inspectable boundary between worker claims, checks,
evidence, owner acceptance, and final milestone acceptance.

## Authorized scope

- Add and lock the data-only `forge-framework-change` pack.
- Track FORGE configuration and governed initiative state in this repository.
- Bind this scope and the exact release requirements as the first workflow outputs.
- Use the governed workflow for the remaining M6 validation, friction review, residual-risk review,
  release-readiness assessment, and lessons.
- Preserve exact check, evidence, decision, and acceptance records as the initiative progresses.

## Constraints

- The repository owner remains the only authority for workflow acceptance, release-blocking risk
  resolution, M6 acceptance, and authorization to enter M7.
- A worker claim, passing command, CI result, merged pull request, or generated report cannot imply
  owner acceptance.
- Pack-data trust authorizes only the exact locked declarative bytes. The pack declares no
  executable capability.
- Credentials, raw captures, caches, locks, temporary environments, and other local-only data
  remain outside governed acceptance authority.
- Production publication, tagging, version `1.0.0`, signing, and package upload are outside M6.

## Compatibility and persistence

This dogfood initiative uses existing public contracts, schema version `1.0`, the current
hash-chained journal, current snapshot binding, immutable artifact revisions, and the existing local
pack boundary. It changes no runtime contract, persisted format, migration, bundled pack, or public
API.

The tracked `.forge/active/` state is intentionally live. Once every workflow step is explicitly
accepted and the repository satisfies closure rules, M6 closeout may archive it. Continued work
after archival requires a successor initiative.

## Increment 7 stop point

Increment 7 stops after the `scope` step has current artifacts, a bounded worker claim, a manual
structural review, and digest-bound evidence, leaving the step at `awaiting_acceptance`. It does not
record owner acceptance on the owner's behalf.
