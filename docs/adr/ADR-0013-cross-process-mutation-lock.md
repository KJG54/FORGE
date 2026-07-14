# ADR-0013 — Cross-Process Mutation Lock

- **Status:** Accepted
- **Date:** 2026-07-14

## Decision

Every supported CLI command that mutates governed initiative state acquires one repository-wide
lock at `.forge/local/locks/mutation.lock` before its core service runs. Exclusive file creation is
the cross-platform arbitration primitive. The bounded JSON metadata records a random ownership
token, process ID, hostname, command, and UTC creation time.

Contention always refuses the second mutation. A same-host process probe distinguishes a likely
live owner from a stale owner for diagnostics only. FORGE never silently deletes either kind of
lock. Release verifies the random token before removing the file, including when the command fails.

## Consequences

Supported CLI mutations cannot overlap across processes. Read-only inspection remains available
and `forge doctor` reports lock ownership and staleness. Bootstrap initialization retains its
existing exclusive-create safeguards because the repository lock directory does not exist before
initialization. Idempotency, explicit stale-lock remediation, and recovery remain later M2 work.
