# M5 Increment 6 — Bounded Filesystem Context Discovery

## Authorized scope

- add one read-only `forge agent discover` command and shared core service;
- inventory repository path metadata under explicit depth, entry, file, size, aggregate-size,
  path-length, and candidate limits;
- never follow symbolic links or read unregistered candidate file content;
- exclude FORGE state, hidden paths, control files, common dependency/build paths, configured
  secret locations, unsupported files, oversized files, and Git-ignored paths;
- fail closed by withholding unregistered suggestions when Git ignore enforcement is unavailable;
- derive lexical filename matches from effective governed assignment data;
- report current required-input coverage and structural sufficiency;
- rank suggestions without registering or authorizing them; and
- measure precision and recall against maintained software and research ground-truth scenarios.

## Explicit exclusions

Unregistered candidate content reading, semantic search, factual or research-quality judgment,
external lookup, SQLite FTS, persistent indexes, automatic artifact registration or revision,
canonical-context mutation, worker permissions, decisions, evidence, verification, acceptance,
pack changes, schema changes, shared pack conformance, cumulative M5 closeout, and remote CI
inspection are not implemented.

## Authority and trust

Discovery output is advisory path metadata. It grants no lifecycle or worker authority and cannot
satisfy a workflow condition. A candidate becomes governed only through the existing explicit
artifact and workflow operations.

Configured secret-path rules and effective Git ignore rules are exclusion controls, not proof that
a displayed path or filename is nonsensitive. Owners must review a suggestion before governing or
sharing it.

## Persistence, compatibility, and failure semantics

The command is read-only and writes no discovery cache or governed record. Existing initiatives,
packs, journals, snapshots, archives, and schema exports remain compatible without migration.
The public contract count remains 51 models and the schema export remains 52 files including its
index.

Missing current required inputs, drifted registered inputs, inventory truncation, and exhausted
candidate capacity report `insufficient`. Unavailable Git ignore enforcement reports
`indeterminate` and withholds all unregistered suggestions. Operational validation errors fail
through the existing sanitized CLI failure boundary.

## Design evidence

[ADR-0049](../adr/ADR-0049-bounded-filesystem-context-discovery.md) records the bounded inventory,
fail-closed ignore handling, lexical measurement, authority, persistence, and FTS-deferral
decisions.

## Validation evidence

- focused discovery, measurement, privacy, drift, fail-closed, hard-limit, budget, CLI-neutrality,
  and symlink coverage: 7 passed with 1 expected Windows privilege-based symlink skip;
- adjacent canonical-context, Git-policy, artifact/evidence, and CLI coverage: 26 passed with
  1 expected Windows privilege-based symlink skip;
- cumulative M5 increment coverage: 29 passed with 1 expected Windows privilege-based symlink
  skip;
- partitioned complete-suite coverage: 306 passed with 7 expected Windows privilege-based symlink
  skips and no failures;
- Ruff clean, strict Pyright clean with 0 errors and 0 warnings, and `git diff --check` clean;
- source distribution and wheel built successfully with Hatchling 1.31.0; and
- a clean Python 3.14 installed-wheel smoke proved bounded sufficient software and research
  discovery, unrelated-filename exclusion, healthy restart, and all 52 schema export files for
  the unchanged 51 public models.

Remote CI is intentionally not inspected or claimed until M5 closeout.

## Stop point

Stop after bounded discovery is measurable for both bundled domains and exposed as an advisory,
read-only command. Do not add a search index, content search, automatic context mutation, shared
pack conformance, or M5 closeout behavior.
