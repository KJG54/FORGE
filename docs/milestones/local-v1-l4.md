# Local Production-v1 L4 - Scratchpad and Warm Recap

## Authorized scope

- add the bounded local scratchpad reader at `.forge/local/conversation/scratchpad.md`;
- implement read-only `forge recap` with validated governed facts separated from mutable local
  notes;
- reconcile scratchpad initiative and journal metadata against the active validated state;
- cover missing, empty, stale, ahead-of-journal, oversized, malformed, symbolic, irregular, and
  cross-initiative scratchpad cases; and
- preserve the existing formal pause/resume and recovery behavior.

## Contract and compatibility

The scratchpad is optional UTF-8 Markdown capped at 65,536 bytes. It remains below the ignored
`.forge/local/` boundary and is never governance, authority, evidence, permission, or automatic
archive input. FORGE reads no symbolic or irregular path and rejects unsafe control characters so
untrusted note content cannot inject terminal control sequences into recap output.

The scratchpad header carries only the initiative ID and observed journal sequence. It is
reconciliation metadata, not a second state database. The displayed update time comes separately
from the local file. Stale, future-sequence, and cross-initiative notes remain visible only under an
explicit reconciliation warning and mutable-and-ungoverned label.

`forge recap` adds no record, schema, event, transition, permission, migration, archive input, or
project-name field. Valid old repositories and archives remain unchanged. The repository directory
is only a friendly non-canonical label. Formal `forge pause` and `forge resume` retain their
existing owner authorization and drift-aware durable summary contract.

## Validation boundary

Focused L4 acceptance covers the scratchpad safety matrix, authoritative/local output separation,
reconciliation, read-only behavior, and pause/resume preservation. Repository-wide lint, typing,
tests, build, CI, and release health checks remain deferred to the Local Production-v1 milestone
closeout under the owner's explicit validation direction.

Passing focused checks establishes only L4 implementation evidence. The encompassing Local
Production-v1 `implement` step remains in progress, and L5 and later increments remain outside this
change.
