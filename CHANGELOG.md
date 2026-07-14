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

### Limitations

- Closure and archive-preservation services are not yet implemented; they remain assigned to M1
  Increment 7.
- Project and distribution naming remain provisional.
