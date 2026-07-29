# ADR-0049: Bounded Filesystem Context Discovery

- Status: Accepted
- Date: 2026-07-27

## Context

Canonical agent context deliberately includes only governed artifacts selected by the active
step. That leakage-resistant boundary is appropriate for execution, but it gives an owner no
bounded way to review ordinary repository files that might need to become governed inputs.

M5 requires a measured answer to whether conservative filesystem discovery is sufficient before
considering a durable search index such as SQLite full-text search (FTS).

## Decision

Add a read-only `forge agent discover` command backed by one shared discovery service.

The service inventories path metadata under hard limits. It never follows symbolic links and
never reads unregistered candidate file content. Existing governed required inputs may be hashed
through the established artifact-currentness check, but their content is not returned. Hidden
paths, FORGE state, control files, configured secret
locations, common dependency/build directories, unsupported files, oversized files, and
Git-ignored files are excluded. If Git ignore enforcement is unavailable, unregistered
suggestions are withheld rather than guessed safe.

Candidates are ranked only by bounded lexical matches in their filenames. Selection terms come
from the initiative objective, effective scope, active step, context-selection rules, and declared
input/output roles. Current governed required inputs remain visible and contribute to a separate
required-input coverage result.

The result is structural and advisory:

- `sufficient` means required governed inputs are current and the bounded inventory completed;
- `insufficient` means required inputs are absent or stale, or a hard inventory/candidate bound
  prevented a complete result; and
- `indeterminate` means ignore-policy enforcement was unavailable.

An internal ground-truth measurement helper computes precision and recall for maintained software
and research scenarios. This evidence decides whether the bounded approach is adequate; the
command does not claim semantic relevance or factual sufficiency.

## Consequences

Discovery creates no journal event, file, artifact revision, worker permission, decision,
evidence, verification, or acceptance. A suggested path must still pass the ordinary owner and
governance workflow before it can become authoritative agent context.

No persisted contract, schema, migration, pack version, search database, embedding, or external
service is introduced. SQLite FTS remains deferred unless measured bounded discovery later proves
insufficient.
