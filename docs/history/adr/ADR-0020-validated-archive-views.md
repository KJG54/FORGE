# ADR-0020: Validated Archive Status and History Views

**Status:** Accepted

**Milestone:** M2 Increment 9

## Context

FORGE can retain many immutable closed and abandoned initiatives while one fresh successor is
active. The original M1 archive selectors validated a chosen archive, but the default status view
listed only archive IDs and archived history did not identify its validated source or expose the
M2 journal-chain identity. Operators therefore had to know an archive ID in advance and could not
readily distinguish objectives, terminal outcomes, lineage, or integrity guarantees.

## Decision

Keep the specified `forge status --archive` and `forge history --archive` command surface. Add
read-only archive summaries derived only after complete archive validation. Default status reports
every archive's canonical ID, objective, terminal state, guarantee class, and event count. Selected
status additionally reports terminal ownership and records, lineage, manifest inventory, preserved
objects, journal head, archive digest, and closure- or abandonment-specific facts.

Archived history reports its source initiative, terminal lifecycle, filtered and total event
counts, journal head, archive digest, and each event's ID and hash-chain links. Filtering remains a
presentation operation after the complete journal and archive have validated. The event-only
history API remains available for compatibility.

## Consequences

Inspection becomes useful across many archives without introducing a new command family or a new
persisted schema. Any damaged archive makes repository-wide status fail closed. Selected status and
history remain byte-for-byte read-only and cannot reopen or alter a terminal initiative.

Schema migration, journal repair, stale-lock removal, unrelated transaction recovery, and hybrid
Git policy remain outside this decision.
