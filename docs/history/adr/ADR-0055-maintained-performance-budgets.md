# ADR-0055: Maintained Release-Candidate Performance Budgets

**Status:** Accepted

**Milestone:** M6 Increment 6

## Context

Release-candidate hardening requires budgets for startup, status, journal replay, context
generation, and archive access. Microbenchmarks of isolated helper functions would omit the
validation, filesystem, and process costs users experience. End-to-end timing alone would hide
journal replay behind interpreter startup.

Performance results also vary across operating systems and shared runners. A single local timing or
average would be too weak to establish a regression boundary.

## Decision

FORGE maintains one strict data-only policy and one repository-local shell-free harness.

- Startup, status, context generation, and archive access measure exact CLI subprocesses.
- Journal replay measures the canonical installed implementation in-process against a deterministic
  1,000-event valid hash chain.
- Status and archive access use five real validated archives; active status and context generation
  use 25 real open decision records.
- Every case uses three warmups, 20 samples, and nearest-rank p95.
- Platform budgets are explicit and match the CPython/operating-system installation matrix.
- Every subprocess has a fixed argument vector, `shell=False`, expected-output validation, and a
  hard timeout.
- Reports preserve raw millisecond samples, environment, workload, statistic, budget, outcome, and
  limitations without retaining temporary repository content.

## Consequences

The budgets detect material regressions across stable, reviewable workloads without adding a
benchmark dependency or runtime command. Cross-platform closeout can execute the same policy
against exact installed wheels.

Timing remains host-sensitive. A pass is not a real-time guarantee or evidence for another matrix
cell. Optimization may not bypass governance, integrity, archive, or security checks.

## Rejected alternatives

- **Measure only Python helpers.** That omits CLI startup, discovery, output, and filesystem costs.
- **Measure every case as a fresh process.** That would make interpreter startup dominate journal
  replay and obscure replay regressions.
- **Use the mean of a few samples.** It hides tail latency and is unstable under small sample
  counts.
- **Add a benchmark framework dependency.** The standard library provides the bounded measurement
  mechanics required by this release gate.
