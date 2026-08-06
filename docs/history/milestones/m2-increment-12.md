# M2 Increment 12 — Conservative Truncated Journal Recovery

This increment extends explicit recovery only to unambiguous active-journal EOF truncation.

Implemented:

- strict separation of recoverable EOF truncation from complete-undelimited, malformed,
  schema-invalid, hash-invalid, sequence-invalid, legacy, and otherwise ambiguous history;
- validation of the complete M2 prefix, locked governance, governed records, and referenced objects;
- exact preservation of the damaged journal, truncated tail, and every observed snapshot;
- an additive `JournalRecoveryRecord` contract and deterministic schema export;
- one owner-attributed `journal-recovered` event after the last valid hash-chain head;
- validated atomic journal replacement as the commit point;
- same-idempotency-key snapshot and receipt completion after post-commit interruption;
- restart validation, tamper detection, continued mutation, CLI, and cross-platform-safe tests; and
- continued immutability for archive journals.

This increment does not reconstruct a missing event, choose among ambiguous histories, recover an
unrelated incomplete command or receipt, delete a stale lock, alter an archive, generate agent
context, invoke adapters, or execute capabilities.
