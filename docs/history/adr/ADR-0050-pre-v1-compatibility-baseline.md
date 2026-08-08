# ADR-0050: Pre-v1 Compatibility Baseline and Fixture Policy

**Status:** Accepted

**Milestone:** M6 Increment 1

## Context

The Production-v1 roadmap requires compatibility and migration tests for every pre-v1 schema.
FORGE has published five accepted milestone baselines to its main branch, but it has not tagged or
published a pre-v1 package release. Every independently persisted public contract in those
baselines declares schema version `1.0`.

The accepted baselines do not all contain the same number of public models. M1 exported 37, M2
exported 44, M3 exported 47, M4 exported 50, and M5 exported 51. Later models extend the public
registry; additive fields on existing models use defaults so accepted earlier records remain
readable.

Contract schema versions are separate from storage formats. FORGE supports two event-journal
formats:

- the complete M1 unhashed journal, which is readable but mutation-blocked; and
- the M2 SHA-256 hash chain, which is the current read/write format.

The only registered migration converts the first format to the second while retaining contract
schema version `1.0`.

Without a frozen inventory, “all pre-v1 schemas” could be misread as a promise to recover arbitrary
intermediate commits, unknown formats, malformed history, or packages that were never released.

## Decision

Maintain `tests/fixtures/compatibility/manifest.json` as the machine-readable pre-v1 compatibility
inventory. It records:

- every owner-accepted milestone baseline and its public model count;
- the cumulative public-model additions at each baseline;
- every supported contract schema version;
- every supported event-journal format and its fixture;
- every registered source-to-target migration edge; and
- the explicit absence of tagged or publicly distributed pre-v1 releases.

Freeze synthetic, non-secret fixtures for:

- accepted schema-`1.0` record shapes whose additive defaults are compatibility-critical;
- a complete M1 unhashed event journal; and
- the exact M2 hash-chained result of the registered migration.

Tests must prove that:

1. cumulative milestone additions reproduce the exact current public registry;
2. no accepted earlier public model disappears;
3. accepted schema-`1.0` records load with their defined current defaults;
4. unsupported future schema versions remain rejected;
5. every migration-registry edge and every supported journal format appears in the manifest;
6. the frozen M1 journal plans the registered migration;
7. deterministic conversion produces the frozen M2 bytes; and
8. the frozen M2 journal is current and requires no migration.

Accepted milestone commits are evidence baselines, not semantic-version releases. Compatibility
is promised for the documented schema and storage formats, not for every repository commit.

## Consequences

M6 documentation, examples, installation tests, and the eventual public support policy can build
on a precise inventory rather than an inferred one. A future incompatible contract or storage
change must update the manifest, add exact fixtures, define or explicitly refuse a migration, and
record a new ADR.

This increment changes no public model, schema version, journal format, migration implementation,
CLI command, authority rule, or persisted byte. Complete legacy M1 active journals remain
read-only until the configured owner explicitly applies the registered migration. Archived
initiatives remain immutable.

Malformed, truncated, mixed, unknown, or future formats are not compatibility fixtures and receive
no new support claim. The existing conservative recovery paths and failure behavior remain
unchanged.
