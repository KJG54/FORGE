# ADR-0054: Reproducible Supply-Chain and Secret Review

**Status:** Accepted

**Milestone:** M6 Increment 5

## Context

Release-candidate hardening requires dependency, license, vulnerability, and secret review.
Dependency declarations use bounded ranges, advisory data changes over time, installed closures
vary by environment, legacy Python package metadata can name licenses ambiguously, and secret
scanners intentionally flag synthetic credential-rejection fixtures.

A one-time prose review would not be repeatable at closeout. Adding scanners to runtime
dependencies would expand the product supply chain merely to inspect it.

## Decision

FORGE uses a strict machine-readable review policy and a repository-local shell-free harness.

- The policy duplicates the exact direct dependency strings intentionally and fails when
  `pyproject.toml` drifts without review.
- License review covers installed build, runtime, and development closures.
- SPDX expressions and unambiguous legacy metadata are accepted only through an explicit
  allowlist.
- Ambiguous legacy licenses require package/version-specific license-file paths and SHA-256
  digests.
- Vulnerability review audits exact installed runtime versions without dependency re-resolution.
- Gitleaks scans both full Git history and a bounded current review snapshot with complete
  redaction.
- Secret exceptions must be exact historical fingerprints; path-wide and rule-wide suppression is
  forbidden.
- External scanners remain separately installed release tools, not FORGE dependencies.

## Consequences

The same review can run locally and later in clean cross-platform closeout environments. Reports
distinguish observed environment facts from future guarantees and contain no matched secret values.
Policy drift, missing tools, ambiguous licenses, findings, or overly broad suppressions fail closed.

Advisory and secret scanners remain fallible third-party checks. A passing review does not prove
future vulnerability absence, legal compliance, secret absence, semantic correctness, owner
acceptance, or release acceptance.

## Rejected alternatives

- **Commit a single scanner transcript.** It becomes stale and does not prove how findings or
  license ambiguity were handled.
- **Add scanners to runtime dependencies.** Review tooling is not required for normal FORGE use and
  would unnecessarily expand the installed product.
- **Ignore the complete synthetic-fixture file or rule.** A broad exclusion could hide a future
  real secret in the same path or from the same detector.
- **Resolve latest dependencies during every audit.** That would review a potentially different
  closure from the environment actually under release review.
