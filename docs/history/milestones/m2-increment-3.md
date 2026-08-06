# M2 Increment 3 — Durable Mutation Idempotency

## Authorized scope

- optional caller-provided and automatically generated idempotency keys for governed CLI
  mutations;
- canonical binding of each key to one stable command request;
- reserved event metadata added before canonical hash sealing;
- schema-versioned repository-wide completion receipts bound to exact event hashes;
- successful replay without duplicate records or transitions;
- conflict refusal when a key is reused for a different request;
- conservative detection of interrupted receipt persistence and receipt tampering;
- single-event, multi-event, generated-key, conflict, and interruption regression coverage.

## Explicit exclusions

This increment does not repair or resume an interrupted command and never synthesizes a missing
receipt. Explicit recovery, stale-lock remediation, pause/resume, migration, atomic archive
hardening, abandonment, and successor initiatives remain later M2 work. Initialization retains
its existing bootstrap behavior, and result-import preview remains outside mutation idempotency.
