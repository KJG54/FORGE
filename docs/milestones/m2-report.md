# Milestone 2 Evidence Report

**Milestone:** M2 — Integrity, Recovery, Archival, and Abandonment

**Implementation state:** complete and owner-accepted

**Owner acceptance:** accepted in the Codex task by the repository owner on 2026-07-17

**Authorized boundary:** M2 only; M3 had not begun when this gate was accepted

## Outcome

M2 makes FORGE's local governed state dependable across corruption detection, concurrent
mutations, interrupted writes, schema evolution, terminal archival, abandonment, successors, and
explicit operational recovery. Valid M2 history is canonically serialized and hash chained;
materialized state is bound to the journal head and remains reconstructable rather than
authoritative.

Every recovery path is explicit, owner-authorized, conservative, provenance-bearing, and bounded
to a mechanically provable condition. FORGE does not silently normalize integrity mismatches,
delete locks, infer missing business events, convert abandonment into success, reopen archives, or
inherit predecessor approval.

## Increment inventory

| Increment | Delivered boundary |
|---|---|
| 1 | Canonical event serialization, SHA-256 hash chaining, snapshot head binding, and legacy M1 read compatibility |
| 2 | Repository-wide cross-process mutation locking and non-destructive stale diagnostics |
| 3 | Journal-bound command idempotency, exact-event receipts, and interrupted-command detection |
| 4 | Explicit active-snapshot reconstruction with exact-byte evidence and provenance |
| 5 | Owner-authorized pause/resume and durable long-gap continuation summaries |
| 6 | Resumable atomic successful closure and hardened archive promotion |
| 7 | Distinct owner-authorized abandonment and non-success archival |
| 8 | Successor initiatives with fresh authority and explicit artifact-reuse provenance |
| 9 | Validated multi-archive status, terminal detail, lineage, and history views |
| 10 | Registered schema migration with legacy-byte preservation and interruption-safe apply |
| 11 | Hybrid Git collaboration policy with governed-state visibility and local-only exclusion |
| 12 | Conservative EOF-truncated final-journal-record recovery |
| 13 | Conservative recovery of a missing receipt for one provably complete command pattern |
| 14 | Explicit same-host stale-lock remediation with exact local evidence and mutation exclusion |

## Exit-criteria evidence

- Valid hash-chained history reconstructs and verifies materialized state.
- Content changes, removed or reordered events, sequence/hash defects, truncation, missing objects,
  archive tampering, and snapshot disagreement are detected rather than normalized.
- Repository locks and idempotency receipts prevent overlapping or duplicate transitions.
- Snapshot, final-record, command-receipt, migration, closure, abandonment, and stale-lock
  interruption boundaries are explicit and restart-safe only where their state is unambiguous.
- Closed and abandoned archives remain distinct, terminal, validated, and immutable through the
  supported command surface.
- Successors receive new identities and no inherited checks, evidence, acceptance, decisions, or
  workflow progress.
- Git remains optional transport and collaboration infrastructure rather than authoritative state.

## Validation results

The final Increment 14 validation records:

- Ruff passed.
- Strict Pyright passed with 0 errors and 0 warnings.
- Pytest passed with 173 tests and 4 expected Windows symlink-privilege skips.
- Isolated source-distribution and wheel builds passed.
- A fresh-environment installed-wheel smoke passed version/help, initialization, configuration,
  bundled-pack validation, `remediate-lock` help, and deterministic export of 44 schemas.
- The remote Windows, macOS, and Linux result for this exact closeout commit is pending its first
  push and is not claimed by this report.

## Known limitations and deferred work

- Foreign-host locks cannot be proven stale by a local process and are intentionally refused.
- Stale-lock remediation evidence contains host runtime metadata and remains local-only; a process
  with the owner's operating-system permissions can delete it, consistent with the threat model.
- Truncated-journal recovery covers only one incomplete final JSON record after a complete valid
  M2 prefix. Ambiguous or middle-history damage remains a manual incident.
- Command-receipt recovery covers registered complete active-tail patterns only; partial or
  specialized terminal transactions retain their specific recovery paths.
- Git synchronization, conflict resolution, staging, commits, and pushes remain owner-controlled.
- Agent context generation, adapters, capability approval/execution, and pack execution trust are
  M3 concerns and were not implemented in M2.

## Owner decision and stop condition

The repository owner explicitly accepted the M2 gate in the Codex task on 2026-07-17 and
authorized committing, pushing, and beginning the first bounded M3 increment.

**Stop satisfied:** M2 is complete and accepted. M3 work must follow its own approved incremental
boundary; this report does not authorize later M3 increments or M4 work.
