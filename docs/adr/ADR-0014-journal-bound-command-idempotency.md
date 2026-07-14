# ADR-0014 — Journal-Bound Command Idempotency

- **Status:** Accepted
- **Date:** 2026-07-14

## Decision

Every supported governed CLI mutation accepts `--idempotency-key` and generates a UUID key when
the option is omitted. The CLI reports the key before it invokes the mutation. Keys are
repository-wide, case-sensitive, bounded to 128 portable characters, and bind a stable command
identity to the canonical digest of its explicit parameters.

Every event committed by that command receives reserved idempotency metadata before hash sealing.
After the command succeeds, FORGE atomically writes a schema-versioned receipt under
`.forge/idempotency/`. The receipt binds the key, command, request digest, and completion time to
the exact IDs, initiative IDs, sequences, and hashes of every committed event. Receipt filenames
are SHA-256 digests of the key so caller input never becomes a path component.

A retry with the same key and request returns the existing event references without running the
mutation again. Reusing the key for different explicit parameters is a conflict. Committed events
without a matching completion receipt indicate an interrupted command and block further mutation;
FORGE preserves the evidence for explicit recovery rather than guessing whether the remaining
work is safe.

## Consequences

Single- and multi-event commands, including successful closure into an archive, have one durable
repository-wide retry identity. Tampered, missing, extra, or mismatched receipts are detected
against authoritative hash-chained journals. The registry is governed project state rather than
ignored local cache state.

Idempotency does not repair an interrupted command. This increment intentionally leaves
receipt reconstruction and partial-operation resolution to explicit recovery. `forge init`
retains its existing identity-preserving bootstrap idempotency, and `import-result` preview does
not use a key because preview is read-only.
