# Performance Budgets

M6 Increment 6 defines release-candidate latency guardrails for five maintained paths:

- cold `forge --version` startup;
- active `forge status`;
- canonical hash-chained journal replay;
- neutral `forge agent context` generation; and
- `forge status --archive` access.

These budgets detect release-blocking regressions. They are not real-time guarantees, throughput
claims, service-level objectives, or evidence for an unmeasured platform.

## Maintained workload

`release/performance-budgets.json` defines the exact data-only policy:

- CPython 3.12, 3.13, and 3.14 on Linux, macOS, and Windows, matching the installation matrix;
- three warmups and 20 measured samples;
- nearest-rank p95 using `perf_counter_ns`;
- a 15-second per-operation fail-closed timeout;
- five real validated abandoned archives;
- one active initiative with 25 open immutable decisions; and
- one independent deterministic 1,000-event canonical hash-chain journal.

User-facing CLI budgets include process startup, imports, repository discovery, validation,
rendering, filesystem access, and output capture. The replay case runs in-process with three
iterations per sample so CLI startup does not hide parsing, contract validation, sequence
validation, and hash-chain verification.

## Budgets

| Case | Linux p95 | macOS p95 | Windows p95 |
|---|---:|---:|---:|
| Startup | 500 ms | 500 ms | 750 ms |
| Active status | 1,000 ms | 1,000 ms | 1,500 ms |
| 1,000-event journal replay | 150 ms | 150 ms | 200 ms |
| Context generation | 1,000 ms | 1,000 ms | 1,500 ms |
| Archive access | 1,000 ms | 1,000 ms | 1,500 ms |

The Windows margin accounts for observed process-start and filesystem differences without
weakening the workload or statistic. Every cell must use the same policy and exact release-review
commit.

## Run the review

Run the repository tool with the Python environment and exact `forge` console executable being
reviewed:

```console
python -m tools.performance_review --forge .venv/Scripts/forge.exe
```

On macOS or Linux, use `.venv/bin/forge`. Use `--output <fresh-path>` to retain JSON evidence; the
harness refuses to overwrite an existing report.

The harness creates all repository and journal fixtures under a fresh temporary directory, uses
fixed subprocess argument vectors with `shell=False`, validates expected command output, removes
warmup results, records every measured sample, and deletes the fixture on exit. It fails for an
unknown policy field, unsupported environment, malformed fixture, command error, unexpected
output, timeout, or p95 above budget.

## Interpretation

- A pass proves only the exact interpreter, operating system, executable, host load, and policy
  recorded in that run.
- Elapsed time naturally includes operating-system scheduling and filesystem variation.
- A budget regression should be reproduced before optimization, but it remains release-blocking
  until resolved or explicitly owner-reviewed as residual risk.
- Faster execution cannot weaken integrity validation, path controls, journal replay, archive
  validation, context boundaries, or governance authority.
- Local source-environment results are development evidence. Clean-wheel runs for every supported
  platform and Python version remain M6 closeout evidence.
