# Pre-v1 Compatibility

FORGE has no tagged or publicly distributed pre-v1 release. Its compatibility evidence comes from
the owner-accepted M1 through M5 baselines published on the main branch.

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
supported migration source. Public semantic-version guarantees begin at `1.0.0`.

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

The machine-readable inventory is
`tests/fixtures/compatibility/manifest.json`. Any future incompatible change must update that
inventory, add preserved fixtures, define or explicitly refuse a migration path, and document the
decision before changing persisted behavior.
