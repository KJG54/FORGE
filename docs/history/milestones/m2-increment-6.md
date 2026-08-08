# M2 Increment 6 — Resumable Atomic Closure and Archival

This increment upgrades successful closure and only successful closure.

Implemented:

- non-preliminary archive manifests for new closures;
- deterministic same-filesystem archive staging and atomic promotion;
- archive validation before active-state retirement;
- atomic active-directory retirement with a validated recoverable retired tree;
- same-request, same-idempotency-key continuation after closure-event commitment;
- recovery from incomplete staging, completed promotion, and interrupted retirement;
- status diagnostics that direct the owner to the exact safe retry;
- compatibility reads for existing preliminary M1 archives; and
- Windows, macOS, and Linux-compatible transaction behavior and tests.

The accompanying CI correction replaces the unsafe Unix-style Windows `os.kill(pid, 0)` liveness
probe with a read-only Win32 process-status query. Lock inspection therefore never signals or
terminates the process it is checking.

The closure event remains the governance commit point. Recovery never deletes or rewrites journal
history and never appends a second terminal event.

This increment does not repair damaged journals, recover unrelated commands, delete stale locks,
abandon initiatives, create successors, migrate schemas, or implement the hybrid Git policy.
Those remain separately authorized later increments.
