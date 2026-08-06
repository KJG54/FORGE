# ADR-0025 — Explicit Stale-Lock Remediation

- **Status:** Accepted
- **Date:** 2026-07-17

## Decision

Add a separate owner-authorized `forge remediate-lock` operation for the repository-wide mutation
lock. It requires a non-empty reason and an idempotency key. It may proceed only when the lock is a
bounded, regular, strictly shaped metadata file created on the current host and the recorded PID is
definitively not live. A live same-host owner, a foreign-host owner, malformed metadata, symbolic
paths, missing locks, and any observed ownership or byte change are refused.

The operation cannot acquire the lock it is removing. A second exclusive remediation guard blocks
ordinary mutations before and after their own lock acquisition. An interrupted guard may be taken
over only by the same explicit remediation key after its same-host owner is definitively dead.

Before removal, FORGE writes a versioned `LockRemediationRecord` that binds the project, configured
owner, reason, request digest, observed owner metadata, exact source digest and size, and preserved
path. The removal commit point is a same-filesystem atomic rename from
`.forge/local/locks/mutation.lock` into the key-scoped `.forge/local/lock-remediations/` evidence
directory. The exact bytes are therefore preserved rather than unlinked. A same-key retry either
finishes a prepared rename or validates and replays the completed operation without touching any
new lock.

Lock metadata and evidence remain local-only because they contain host runtime details and do not
belong to any initiative journal. `forge doctor` validates every retained record/evidence pair.
The public record shape is included in deterministic schema export.

## Consequences

Stale locks are never removed implicitly and a remote-host lock is not treated as safely removable
merely because its process cannot be probed locally. Exact local evidence and explicit owner intent
make remediation inspectable and restart-safe without inventing a governance event.

Local evidence is not authoritative governed initiative state and is excluded by the hybrid Git
policy. A process with the repository owner's operating-system permissions can delete it, which is
consistent with FORGE's stated same-user threat-model limitation. Remediation does not validate,
repair, or recover journals, snapshots, receipts, archives, or interrupted business commands.
