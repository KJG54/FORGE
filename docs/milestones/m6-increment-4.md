# M6 Increment 4 — Complete Audience Documentation

## Authorized scope

- add one navigable documentation index;
- complete task-oriented user, pack-author, adapter-author, architecture, security,
  troubleshooting, and recovery routes;
- reuse existing feature references as canonical detail rather than duplicating specifications;
- describe supported commands, authority, persistence, failure, trust, and explicit non-claims;
- add focused inventory and local-link conformance tests; and
- record the documentation-information-architecture decision.

## Explicit exclusions

Runtime behavior, public contracts, persisted formats, migrations, pack bytes, adapter
registration, authority, executable capabilities, package metadata, dependency/supply-chain
review, vulnerability scanning, performance budgets, dogfooding, CI configuration, full
installation-matrix execution, fresh-user observation, release publication, and M7 work are not
implemented.

Per owner direction, the complete test suite, builds, distribution installation, cross-platform
execution, and remote CI remain deferred until M6 closeout. Increment 4 uses only focused
documentation conformance and static quality checks.

## Documentation boundary

The new guides are routes and operational explanations. Accepted ADRs, strict contracts, locked
records, the journal, and existing feature references retain their source-of-truth order. A guide
cannot create a command, compatibility commitment, authority, recovery path, or release claim.

The adapter-author guide explicitly documents the current in-tree contribution boundary; FORGE
does not claim dynamic third-party adapter discovery or a stable plugin ABI. The security guide
does not claim hostile-code isolation or complete secret detection. Pack validation does not grant
data trust or executable authority.

## Design evidence

[ADR-0053](../adr/ADR-0053-audience-oriented-documentation-map.md) records the audience-oriented
navigation decision and the rejection of duplicated specifications or a new documentation
toolchain.

## Validation evidence

- focused audience inventory, local-link, authority/security wording, and stable-exit-code coverage:
  4 passed;
- every local link in the README, security policy, documentation index, and seven required
  audience routes resolves;
- focused Ruff coverage for the Increment 4 test module: clean;
- focused strict Pyright coverage for the Increment 4 test module: 0 errors and 0 warnings; and
- `git diff --check`: clean.

The complete pytest suite, distribution rebuild, installed-wheel documentation review,
cross-platform execution, remote CI, and human fresh-user walkthrough are intentionally deferred
to M6 closeout.

## Stop point

Stop after the documentation index, seven required audience routes, focused conformance tests,
reader-facing README links, ADR, and Increment 4 evidence record. Do not begin supply-chain review,
performance measurement, dogfooding, release-candidate risk reporting, CI closeout, or Increment 5
without a separate owner decision.
