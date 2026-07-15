# Changelog

All notable changes will be documented here. FORGE follows milestone evidence before public
semantic-version commitments begin at v1.0.0.

## [Unreleased]

### Added

- Milestone 0 constitutional, legal, packaging, tooling, testing, and CI foundation.
- Strict schema-versioned M1 canonical contracts and deterministic JSON Schema export.
- Project configuration validation, owner identity bootstrap, and repository discovery.
- Non-destructive `forge init` with safe `.gitignore` merging and repository-bound path checks.
- `forge config show|validate` and stable error categories for the implemented command surface.
- Ordered event journals, deterministic replay, atomic snapshots, and mismatch detection.
- Data-only pack validation, immutable pack/workflow locks, initiative creation, manual runs,
  workflow authority checks, status, and next-action reporting.
- Immutable artifact revisions with content-addressed preservation, drift detection, heuristic
  secret screening, worker claims, manual check results, evidence packets, dependency references,
  and record-backed verification transitions.
- Owner-only acceptance and revocation, append-only decisions and supersession, recursive
  dependency staleness, downstream workflow invalidation, and restart-safe rework transitions.
- Provider-neutral manual handoff bundles and two-phase untrusted result import with bounded
  staging, inventory/path/symlink/secret safeguards, previews, explicit collision actions,
  content-addressed preservation, and single-event artifact registration.
- Owner-only successful closure with complete-workflow and current-acceptance gates, exact-byte
  archive manifests, preserved-object verification, read-only archived status and history, and
  terminal command-level immutability.
- M1 end-to-end acceptance with a restarted-process software walkthrough, a data-only synthetic
  community-research workflow, repository diagnostics, Standard/Guided presentation, and immutable
  event-derived run inspection and cancellation.
- M2 canonical UTF-8 event serialization, SHA-256 previous-hash chaining, snapshot head binding,
  corruption detection, and explicit read-only compatibility for legacy M1 journals.
- M2 repository-wide cross-process mutation locking with bounded owner metadata, live contention
  refusal, platform-safe process liveness checks, stale-lock diagnostics, and ownership-verified
  release.
- M2 journal-bound mutation idempotency with generated or caller-provided keys, canonical request
  binding, exact-event completion receipts, duplicate-free retry, and interruption detection.
- M2 owner-authorized active-snapshot recovery with exact-byte evidence preservation, complete
  journal and governed-record validation, recovery provenance, atomic reconstruction, and
  duplicate-free resume after recovery-event commitment.
- M2 owner-authorized pause and resume with resumable-state digests, active-run refusal,
  inspection-only paused behavior, restart-safe lifecycle restoration, and durable resumption
  summaries.
- M2 resumable successful closure with hardened archive manifests, deterministic staging, atomic
  promotion, archive-before-retirement validation, interruption diagnostics, and duplicate-free
  same-idempotency-key completion.
- M2 owner-authorized abandonment with required reason, unfinished-work and unresolved-risk
  records, explicit active-run refusal, active-or-paused entry, distinct non-success manifests,
  exact governed-history preservation, and resumable atomic archival.

### Limitations

- Existing M1 archives retain their preliminary guarantee; successor initiatives remain deferred,
  and active-snapshot recovery does not repair damaged journals or unrelated interrupted mutations.
- Project and distribution naming remain provisional.
