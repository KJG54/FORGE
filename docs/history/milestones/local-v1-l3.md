# Local Production-v1 L3 — Canonical Transaction Receipts

## Authorized scope

- implement one shared non-persisted transaction result model and renderer;
- cover new commits, atomic multi-event commands, committed unsuccessful outcomes, refusals, and
  idempotent replays;
- bind committed output to exact journal sequence ranges and event IDs;
- derive resulting state, blockers, and legal actions from validated replay rather than agent
  inference;
- migrate the high-frequency mutation paths listed in
  [the receipt reference](../transaction-receipts.md); and
- preserve detailed history and record inspection for forensic use.

## Contract and compatibility

One command or atomic transaction produces one canonical receipt. A commit has exactly one
`Recorded ->` line and one `Means ->` line. An idempotent replay identifies the original
transaction and explicitly reports zero new events. A refusal has no `Recorded` line and does not
claim unchanged governed state unless validated before-and-after positions prove it.

The renderer is a presentation layer over existing durable idempotency receipts, exact journal
events, and replayed status. L3 does not change the 51-model schema-`1.0` registry, record shapes,
journal format, event hash chain, workflow locks, pack formats, migrations, archives, authorities,
or transition rules. Valid old repositories and archives remain unchanged.

## Validation boundary

Focused acceptance covers single- and multi-event commits, exact sequence and event identity,
duplicate-free replay, safe and uncertain refusal language, a committed failed check, and retained
history/check inspection. Repository-wide lint, typing, tests, version consistency, distribution
build, and health checks must remain clean before L3 is handed to the owner.

Passing tests establish only L3 implementation evidence. The encompassing Local Production-v1
`implement` step remains in progress, and L4 scratchpad/recap work and later increments remain
outside this change.
