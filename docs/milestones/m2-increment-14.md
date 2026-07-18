# M2 Increment 14 — Explicit Stale-Lock Remediation

This increment completes the remaining bounded M2 lock-handling requirement without changing
governed initiative history.

Implemented:

- owner-only `forge remediate-lock --reason ... --idempotency-key ...` outside the ordinary locked
  mutation wrapper;
- strict bounded lock metadata parsing and same-host, definitively-dead PID proof;
- refusal of live, foreign-host, malformed, oversized, symbolic, missing, changed, and ambiguous
  locks;
- a separate exclusive remediation guard checked before and after ordinary mutation-lock
  acquisition, including same-key recovery of an interrupted stale guard;
- pre-commit `LockRemediationRecord` authorization bound to project, actor, reason, request digest,
  observed owner, exact bytes, digest, size, and destination;
- same-filesystem atomic rename as the removal commit point, preserving the complete lock bytes
  under `.forge/local/lock-remediations/` rather than deleting them;
- same-key completion of an interrupted prepared operation and validation-only idempotent replay;
- `forge doctor` validation of all retained local authorization/evidence pairs; and
- additive deterministic schema export, ADR-0025, recovery guidance, and cross-platform-safe
  refusal, interruption, tamper, guard, CLI, and exact-byte tests.

This increment does not delete a lock silently, remediate a foreign-host lock, infer command
completion, recover another idempotency key, repair a journal or snapshot, change an archive,
append an initiative event, generate agent context, invoke adapters, or execute capabilities.

Validation evidence:

- 173 tests passed with 4 expected Windows symlink-privilege skips;
- Ruff and strict Pyright passed;
- isolated source and wheel builds passed; and
- the fresh-environment installed wheel passed version, command-help, initialization,
  configuration, bundled-pack, and 44-schema export smoke checks.

The repository owner accepted the M2 gate in the Codex task on 2026-07-17. The milestone-level
evidence and acceptance record is `docs/milestones/m2-report.md`.
