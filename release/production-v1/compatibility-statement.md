# FORGE Governance 1.0 Compatibility Statement

## Candidate identity

This statement applies to the unpublished `forge-governance==1.0.0` candidate and the future
immutable `v1.0.0` tag only if the exact candidate later passes its complete verification and
receives separate owner publication approval. A development commit or local build reporting
`1.0.0` is not evidence that Production v1 has been released.

## Supported environments

FORGE Governance 1.0 supports CPython 3.12, 3.13, and 3.14 on Linux, macOS, and Windows. The
supported installation modes are a Python virtual environment and `pipx`, using the exact universal
wheel under review.

## Persisted compatibility

The 1.x line guarantees continued support for:

- all 51 public contract models using `schema_version: "1.0"`;
- complete valid `m2-sha256-event-chain` journals for governed reading and mutation;
- complete valid `m1-unhashed-event-journal` journals for read-only inspection and explicit
  owner-authorized migration through `legacy-m1-journal-to-m2-hash-chain-v1`;
- defined additive defaults in frozen earlier schema-`1.0` record shapes;
- deterministic schema export with distribution and pack-contract metadata; and
- immutable archive validation without archive migration or rewriting.

Unknown fields, future schema versions, mixed or malformed formats, tampered records, and unsafe
partial history remain fail-closed except for separately documented conservative recovery paths.

## CLI and Python compatibility

Throughout 1.x, documented CLI command paths, required inputs, governance effects, and
success/failure meaning remain compatible. Minor releases may add optional commands or inputs.
Patch releases may correct behavior without adding required input. Exact help, status, diagnostic,
and error prose is not a stable machine interface.

The supported public Python surfaces are `forge.__version__`, the `forge.contracts` registry and
exports, and `forge.schemas`. Modules under `forge.core`, `forge.storage`, and other undocumented
internals are implementation details.

## Pack compatibility

The installed distribution bundles `software-basic@0.4.0` and `research-basic@0.4.0`. Their pack
and workflow versions remain independent from the distribution version. Both use the
`forge-contracts-1` compatibility marker.

The repository-local `forge-framework-change@0.1.0` and
`forge-production-release@0.1.0` packs also use `forge-contracts-1`, but they are governance
artifacts in this repository rather than publicly installed bundled packs. Trusting any pack as
data grants no executable capability or external authority.

## Semantic-version rule

- `1.0.x` may contain compatible defect, security, performance, documentation, and internal
  implementation corrections.
- `1.x.0` may add backward-compatible optional capabilities, contracts, formats, and migrations.
- Removing or incompatibly changing an existing guaranteed persisted, CLI, or public Python
  boundary requires a new distribution major version.

Schema, journal, pack, workflow, and distribution versions are independent. A new schema or format
can remain compatible within 1.x only while earlier supported inputs continue to work as
documented or retain an explicit safe migration path.

## Explicit non-claims

FORGE Governance 1.0 does not promise compatibility with arbitrary intermediate commits,
unreleased snapshots, malformed or future persisted data, downgrade to older formats, mutation of
immutable archives, undocumented Python internals, exact human-readable CLI prose, independently
installed provider behavior, or a future distribution major version without a later explicit
policy.
