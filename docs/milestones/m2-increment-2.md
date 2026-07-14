# M2 Increment 2 — Mutation Locking and Stale Diagnostics

## Authorized scope

- repository-wide cross-process locking for supported governed mutations;
- durable bounded ownership metadata under ignored local state;
- refusal while another live process owns the lock;
- explicit stale and malformed lock diagnostics;
- ownership verification and release on success or failure;
- real cross-process contention regression coverage.

## Explicit exclusions

This increment never removes stale locks automatically. Idempotency keys, remediation commands,
pause/resume, recovery, migration, archive hardening, abandonment, and successors remain later M2
work. Manual filesystem mutation outside the supported CLI is not converted into an authorization
boundary.
