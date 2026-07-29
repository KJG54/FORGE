# ADR-0060: Production-v1 Semantic Version and Compatibility Freeze

**Status:** Accepted

**Date:** 2026-07-29

**Milestone:** M7 Increment 2

## Context

FORGE has owner-accepted development baselines from M1 through M6 but no tagged or publicly
distributed package release. Those baselines established 51 independently persisted public
models at contract schema version `1.0`, a current SHA-256 event-journal format, one complete
legacy journal format, one explicit migration edge, and a broad CLI surface. The distribution
remained `0.1.0a0` while those boundaries were developed and tested.

Production v1 needs an exact compatibility promise before final support policy, metadata,
documentation, automation, candidate verification, and publication can rely on it. Distribution,
contract-schema, journal-format, pack, and workflow versions represent different boundaries and
must not be forced to match.

## Decision

### Distribution identity

The Production-v1 candidate uses:

- distribution `forge-governance`;
- Python package `forge`;
- CLI entry point `forge`;
- distribution and runtime version `1.0.0`;
- wheel `forge_governance-1.0.0-py3-none-any.whl`;
- source distribution `forge_governance-1.0.0.tar.gz`; and
- reserved, not-yet-created tag `v1.0.0`.

Development commits may report `1.0.0` before publication. Only the separately owner-approved
immutable tag and matching public artifacts establish that Production v1 has been released.

### Semantic-version guarantees

Throughout the `1.x` distribution line, FORGE will:

- continue reading valid supported schema-`1.0` records;
- preserve the documented meaning and authority boundaries of those records;
- continue reading and mutating the current M2 SHA-256 journal under normal governance;
- continue reading complete valid M1 journals and offering the existing explicit owner-authorized
  migration, without mutating immutable archives;
- preserve documented CLI command paths, required inputs, governance effects, and success/failure
  meaning;
- preserve `forge.__version__`, the exported `forge.contracts` model registry, and deterministic
  schema export as public Python surfaces; and
- retain compatibility with the `forge-contracts-1` declarative-pack contract.

Patch releases may correct defects, security issues, performance, documentation, and internal
implementation without requiring new user input or weakening these guarantees. Minor releases may
add backward-compatible commands, optional inputs, public models, optional persisted fields with
defined defaults, schemas, formats, and migration paths. Removing or incompatibly changing an
existing guaranteed boundary requires a new distribution major version.

A new contract schema or journal format does not by itself require the same numeric distribution
version. It remains backward-compatible within `1.x` only while all previously supported inputs
continue to work as documented or retain an explicit safe migration path.

### Frozen v1 boundary

- The public contract registry contains exactly 51 models.
- Independently persisted public records use `schema_version: "1.0"`.
- Unknown fields and unsupported future schema versions fail closed.
- `m2-sha256-event-chain` is the current read/write journal format.
- `m1-unhashed-event-journal` is readable only when complete and valid and requires
  `legacy-m1-journal-to-m2-hash-chain-v1` before mutation.
- Immutable archives are never migrated.
- Supported release environments are CPython 3.12, 3.13, and 3.14 on Linux, macOS, and Windows,
  using either a virtual environment or `pipx`.
- Bundled `software-basic` and `research-basic` packs remain independently versioned at `0.4.0`.
- Repository-local `forge-framework-change` and `forge-production-release` packs remain
  independently versioned at `0.1.0` and are not installed public packs.

The complete machine-readable boundary is `release/version-contract.json`. The
`tools.version_consistency` check binds it to package metadata, runtime version output, artifact
filenames, release configuration, current documentation, schema metadata, migration inventory,
CLI command paths, and exact pack compatibility declarations.

### Explicit non-guarantees

Production v1 does not guarantee:

- exact human-readable help, status, diagnostic, or error prose;
- private modules under `forge.core`, `forge.storage`, or other undocumented internals;
- compatibility with arbitrary intermediate commits or unreleased package snapshots;
- acceptance of unknown, mixed, malformed, truncated, tampered, or future persisted formats;
- downgrade from a current format to an earlier format;
- mutation or migration of immutable archives;
- behavior of independently installed Codex or Claude provider CLIs beyond FORGE's documented
  detection and fallback boundary; or
- cross-major compatibility without an explicit later policy.

## Consequences

Release inputs now consistently identify the `1.0.0` candidate, while historical `0.1.0a0`
archives, fixtures, reports, checksums, tool references, and milestone records remain unchanged.
The schema index gains distribution and pack-contract metadata without changing any persisted
record schema.

The bundled packs do not receive artificial `1.0.0` versions. Existing exact pack locks remain
valid, and pack compatibility is stated through `forge-contracts-1`.

Until Increment 4 completes metadata and documentation, package classifiers, public project URLs,
and the dated changelog section remain visibly pending. No tag, build acceptance, publication,
publisher configuration, or external support commitment is created by this decision.

## Rejected alternatives

- **Keep `0.1.0a0` until tagging.** Later metadata, automation, and exact-candidate work would not
  exercise the version intended for publication.
- **Use a release-candidate suffix.** The accepted roadmap calls for freezing `1.0.0`; publication
  authority comes from the exact owner gate rather than a temporary version suffix.
- **Set schemas and packs to `1.0.0`.** Those are independent compatibility domains and equal
  numbers would imply a relationship that does not exist.
- **Rewrite historical alpha references.** That would falsify immutable evidence and break recorded
  artifact identity.
- **Freeze exact CLI prose.** Human-readable wording needs room for compatible clarification;
  command paths, inputs, effects, and success/failure meaning are the stable boundary.
