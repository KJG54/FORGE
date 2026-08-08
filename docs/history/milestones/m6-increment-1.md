# M6 Increment 1 — Pre-v1 Compatibility and Migration Baseline

## Authorized scope

- inventory every owner-accepted M1–M5 public contract baseline;
- distinguish accepted development baselines from tagged or publicly distributed releases;
- identify every supported contract schema version and event-journal storage format;
- freeze synthetic compatibility-critical schema-`1.0` record fixtures;
- freeze complete legacy M1 and current M2 event-journal fixtures;
- prove cumulative public-model retention across accepted milestones;
- prove additive legacy-record loading and unsupported-future-version refusal;
- bind the machine-readable inventory to the exact migration registry;
- prove byte-for-byte deterministic M1-to-M2 journal conversion; and
- document compatibility claims, exclusions, and the rule for future incompatible changes.

## Explicit exclusions

New or changed public contracts, schema versions, journal formats, migration edges, CLI commands,
authority rules, persistence paths, recovery procedures, package versions, installation matrices,
examples, completed documentation sets, supply-chain review, performance budgets, dogfooding,
release publication, and M7 work are not implemented.

Per the owner's direction, GitHub Actions configuration, expanded CI matrices, remote CI
inspection, and remote CI evidence are deferred until M6 closeout.

## Compatibility decision

All accepted independently persisted public records use schema version `1.0`. The accepted public
registry grew additively:

| Baseline | Commit | Public models |
|---|---|---:|
| M1 | `cd205c9` | 37 |
| M2 | `f9dee0e` | 44 |
| M3 | `c3f3d32` | 47 |
| M4 | `6179f7a` | 50 |
| M5 | `57065f0` | 51 |

These commits are owner-accepted development evidence, not tagged or publicly distributed pre-v1
package releases. FORGE promises compatibility with the documented schema and storage formats,
not every intermediate commit.

The complete M1 unhashed journal remains the only registered legacy source format. It is readable
but mutation-blocked until the configured owner explicitly applies
`legacy-m1-journal-to-m2-hash-chain-v1`. The M2 SHA-256 hash chain is the current read/write
format. Both use contract schema version `1.0`.

## Authority, persistence, failure, and security semantics

Increment 1 adds only documentation, synthetic fixtures, and tests. It creates no runtime
authority or persisted project record. The existing migration remains preview-first,
owner-authorized, provenance-preserving, atomic at journal replacement, and resumable after its
commit point. Archives remain immutable.

Unknown fields and future schema versions remain invalid. Unknown, mixed, malformed, truncated, or
tampered journal formats receive no compatibility claim and retain their existing fail-closed or
separately documented conservative recovery behavior.

Fixtures use fixed synthetic UUIDs and synthetic descriptions. They contain no owner, repository,
credential, provider, environment, artifact, or project content.

## Design evidence

[ADR-0050](../adr/ADR-0050-pre-v1-compatibility-baseline.md) records the accepted-baseline
definition, contract/storage separation, fixture policy, compatibility claims, and explicit
non-claims. [`compatibility.md`](../compatibility.md) is the reader-facing policy, and
`tests/fixtures/compatibility/manifest.json` is the executable inventory.

## Validation evidence

- focused frozen-fixture and registered-migration coverage: 11 passed;
- contract, M5 conformance, compatibility, and migration coverage: 24 passed;
- complete local suite: 315 passed with 7 expected Windows privilege-based symlink skips and no
  failures;
- Ruff: clean;
- strict Pyright: 0 errors and 0 warnings;
- `git diff --check`: clean;
- Hatchling 1.31.0 built the source distribution and wheel outside the source tree;
- source-archive inspection found 291 entries, all 8 required Increment 1 documentation, test, and
  fixture paths, and no local pytest, smoke, build, or M6 validation scratch paths; and
- a fresh Python 3.14 environment installed the exact wheel and loaded FORGE from `site-packages`,
  reported `0.1.0a0`, validated all 5 frozen legacy record fixtures, distinguished the frozen M1
  and M2 journals, and exported 51 public schemas plus `index.json` (52 files total).

Remote CI is intentionally deferred until M6 closeout by owner direction.

## Stop point

Stop after the compatibility inventory, frozen fixtures, executable schema/migration tests,
documentation, and local built-package evidence. Do not expand CI, add a schema or migration,
claim public semantic-version stability, publish a package, or begin M6 Increment 2 without a
separate owner decision.
