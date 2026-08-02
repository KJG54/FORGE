# Production-v1 Compatibility

FORGE Governance freezes the compatibility boundary for the unpublished
`forge-governance==1.0.0` candidate. A development commit or local artifact reporting `1.0.0` is
not a public release; only the separately owner-approved immutable `v1.0.0` tag and matching public
artifacts establish publication.

The complete reader-facing promise is
[`release/production-v1/compatibility-statement.md`](../release/production-v1/compatibility-statement.md),
and [`release/version-contract.json`](../release/version-contract.json) is its machine-readable
consistency source.

## Semantic-version guarantee

Throughout the 1.x distribution line, FORGE preserves supported schema-`1.0` records, documented
journal reading and migration, CLI command paths and governance meaning, public contract/schema
exports, and the `forge-contracts-1` declarative-pack boundary.

- Patch releases correct defects, security, performance, documentation, and internal
  implementation without requiring new user input.
- Minor releases may add backward-compatible optional commands, inputs, models, fields, schemas,
  formats, and migrations.
- Removing or incompatibly changing an existing guaranteed boundary requires a new distribution
  major version.

Exact human-readable CLI prose and undocumented implementation modules are not stable interfaces.
Schema, journal, pack, workflow, and distribution versions remain independent.

Local Production-v1 L2 adds direct workspace-agent protocol version `1.0.0` as another independent
version domain. It is an exact packaged and regenerable Markdown resource, not a persisted public
model. The L2 implementation leaves the 51-model schema registry and valid old records and workflow
locks unchanged. Existing managed `AGENTS.md` and `CLAUDE.md` marker spans refresh in place while
preserving all owner-authored bytes outside the span.

## Contract compatibility

All independently persisted public records use `schema_version: "1.0"`. The accepted public
registry grew additively:

| Baseline | Accepted commit | Public models | Compatibility meaning |
|---|---|---:|---|
| M1 | `cd205c9` | 37 | Original schema-`1.0` records remain readable |
| M2 | `f9dee0e` | 44 | Seven recovery, migration, archival, and idempotency models added |
| M3 | `c3f3d32` | 47 | Canonical context and executable-approval models added |
| M4 | `6179f7a` | 50 | Validator, cancellation, and local-audit models added |
| M5 | `57065f0` | 51 | Structural-validator definition added |

An accepted baseline is not a package release or a promise that every intermediate commit is a
supported migration source. It is preserved evidence for the inputs now guaranteed throughout
the 1.x line.

Current code accepts the frozen earlier schema-`1.0` record shapes in
`tests/fixtures/compatibility/schema-1.0-records.json`. Additive fields use defined defaults.
Unknown fields and unsupported future schema versions remain invalid.

## Journal-format compatibility

| Format | Read | Mutate | Required action |
|---|---|---|---|
| `m1-unhashed-event-journal` | Yes, when complete and valid | No | Preview and explicitly apply `legacy-m1-journal-to-m2-hash-chain-v1` |
| `m2-sha256-event-chain` | Yes | Yes, subject to normal governance | None |

The migration retains contract schema version `1.0`. It preserves the exact M1 source bytes,
deterministically seals the existing events, appends one provenance-bearing migration event, and
atomically replaces the active journal. The configured owner must explicitly apply it. Immutable
archives are validated but never migrated.

The frozen journal fixtures are synthetic and contain no user, repository, credential, provider,
or artifact content.

## Explicit non-claims

FORGE does not claim compatibility with:

- arbitrary intermediate Git commits;
- untagged packages obtained outside the accepted milestone baselines;
- unknown, mixed, malformed, or tampered schemas or journal formats;
- incomplete history except for separately documented conservative recovery cases;
- migration or mutation of immutable archives; or
- downgrade from a current format to an earlier format.

It also does not freeze exact help, status, diagnostic, or error wording; private implementation
modules; independently installed provider CLI behavior; or cross-major compatibility without a
later explicit policy.

The machine-readable inventory is
`tests/fixtures/compatibility/manifest.json`. Any future incompatible change must update that
inventory, add preserved fixtures, define or explicitly refuse a migration path, and document the
decision before changing persisted behavior.
