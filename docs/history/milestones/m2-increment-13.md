# M2 Increment 13 â€” Conservative Interrupted-Command Recovery

This increment resolves only mechanically complete active commands whose journal events committed
before their completion receipt became durable.

Implemented:

- owner-only, locked, idempotent `forge recover-command <interrupted-key>` with a separate recovery
  key and required reason;
- exact active-tail and single-incomplete-command requirements across the repository-wide registry;
- registered event-pattern validation for every ordinary mutation, including two-event completion
  and acceptance commands;
- explicit refusal of partial patterns, specialized close/abandon/migrate/recover transactions,
  archived targets, existing or damaged receipts, and ambiguous histories;
- validation of the hash chain, locked governance, records, preserved objects, replayed state, and
  atomic pre-command/current snapshot boundaries before commitment;
- an additive `CommandRecoveryRecord` schema and owner-attributed `command-recovered` event;
- exact receipt reconstruction bound to original event IDs, initiatives, sequences, and hashes;
- post-commit same-key resume without duplicate recovery events or receipts; and
- restart, tamper, partial multi-event, stale snapshot, CLI, and cross-platform-safe tests.

This increment does not invent a missing business event, complete a partial transaction, repair or
rewrite a journal, change an archive, remove a stale lock, generate agent context, invoke adapters,
or execute capabilities.

Validation evidence:

- 165 tests passed with 3 expected Windows symlink-privilege skips;
- Ruff and strict Pyright passed;
- isolated source and wheel builds passed; and
- the installed wheel passed version, command-help, initialization, configuration, bundled-pack,
  and 43-schema export smoke checks.

Explicit stale-lock remediation remains the recommended next bounded M2 increment.
