# M6 Increment 5 — Supply-Chain and Secret Review

## Authorized scope

- bind exact build, runtime, and development dependency declarations into a strict review policy;
- inventory installed dependency closures and review every discovered license;
- require explicit SPDX allowlisting and exact file-digest evidence for ambiguous legacy metadata;
- audit exact installed runtime versions against a real advisory service;
- scan complete Git history and the bounded current review snapshot for secrets with full redaction;
- permit only one exact historical synthetic-fixture fingerprint;
- emit a secret-free machine-readable result; and
- document interpretation, limitations, and release-blocking behavior.

## Explicit exclusions

Runtime dependencies, public contracts, persistence, migrations, packs, adapters, authority,
package version, dependency upgrades, automatic remediation, credential rotation, CI
configuration, performance budgets, dogfooding, release signing, publication, and M7 work are not
implemented.

The complete test suite, distribution rebuild, clean-wheel review, cross-platform repetition,
expanded installation matrix, and remote CI remain deferred to M6 closeout by owner direction.

## Security and failure boundary

The harness uses fixed argument vectors and `shell=False`. It passes exact pinned installed runtime
versions to `pip-audit`, requires fully redacted Gitleaks reports, copies only bounded Git-visible
files into temporary scan storage, and deletes temporary reports and snapshots.

It fails closed for policy drift, unknown fields, missing dependencies, unreviewed or changed
licenses, unsupported tool versions, advisory findings, secret findings, broad exceptions,
irregular paths, inventory limits, malformed scanner output, or scanner failure.

The one ignored historical finding is a synthetic API-key test fixture, bound by exact
commit/path/rule/line fingerprint. No path-wide or rule-wide exception is accepted.

## Design evidence

[ADR-0054](../adr/ADR-0054-reproducible-supply-chain-and-secret-review.md) records the
machine-readable policy, exact-installed-version audit, external-tool, license-override, redaction,
and secret-exception decisions.

## Validation evidence

- focused strict-policy, dependency-scope, installed-license, missing-package, unknown-field, exact
  secret-exception, broad-exception-refusal, and existing secret-screening coverage: 7 passed;
- the Windows CPython 3.14 environment contained 26 reviewed packages across build, runtime, and
  development closures, all with allowed license expressions;
- exact file SHA-256 evidence resolved the otherwise ambiguous legacy BSD metadata for
  `colorama` 0.4.6 and `nodeenv` 1.10.0;
- PyPA `pip-audit` 2.10.1 queried PyPI advisory data for all 14 exact installed runtime packages
  without dependency re-resolution and reported zero known vulnerabilities;
- Gitleaks 8.30.1 scanned the complete 63-commit Git history with full redaction and reported no
  unreviewed finding;
- the same Gitleaks review scanned a bounded current snapshot containing 342 Git-visible files and
  reported no finding;
- the only exception was the exact commit/path/rule/line fingerprint for the historical synthetic
  API-key rejection fixture;
- focused Ruff coverage for the harness and Increment 5 tests: clean;
- focused strict Pyright coverage for the harness and Increment 5 tests: 0 errors and 0 warnings;
  and
- `git diff --check`: clean.

The result will remain point-in-time local evidence. Clean-wheel, cross-platform, and exact
release-review-commit evidence remain M6 closeout requirements.

## Stop point

Stop after the policy, review harness, narrow historical exception, focused tests, documentation,
ADR, and local observed review. Do not upgrade dependencies automatically, add CI, begin
performance measurement, dogfood release work, produce the residual-risk report, or begin
Increment 6 without a separate owner decision.
