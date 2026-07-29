# M6 Increment 8 Verification Report

Status: **local validation passed; required remote validation pending**

This draft records the exact local release-candidate evidence produced on 2026-07-29. It is not a
passing `release-checks-passed` result, owner acceptance, M6 readiness, or publication authority.
The pull-request and merged-`main` matrices required by the locked release requirements have not
run.

## Candidate distributions

The source tree produced one source distribution and one wheel through the default
source-distribution-to-wheel build path.

| Artifact | SHA-256 |
|---|---|
| `forge_governance-0.1.0a0.tar.gz` | `75d5e0d29e6b9d146ab441a2cbace791d82f399393f45e6447da82aab16ec6f9` |
| `forge_governance-0.1.0a0-py3-none-any.whl` | `800443d7c82523d0a11b3de0cb8834f5c1406ea8741f9ec6eb3f095bff4bca9f` |

The local build report digest is
`sha256:9d450cc074bd460f36b665c211010bd670961d21f8d97014f174b40d92ce8d4d`.

## Local validation

| Boundary | Result |
|---|---|
| Complete pytest suite | 348 passed, 7 skipped Windows symlink cases |
| Ruff | passed |
| Strict Pyright | 0 errors, 0 warnings, 0 information messages |
| Source distribution and wheel build | passed |
| Windows / CPython 3.14 / venv exact-wheel installation | passed; 51 schemas |
| Windows / CPython 3.14 / `pipx` exact-wheel installation | passed; 51 schemas |
| Research example | passed; 7 steps and healthy archive |
| Software example | passed; 6 steps and healthy archive |
| Procedure rehearsal | all 7 maintained procedures passed |
| Isolated performance review | all 5 maintained budgets passed |
| Supply-chain and secret review | passed |

The seven pytest skips require Windows symbolic-link privileges unavailable in this environment.
The supported remote runners must execute these cases where their host policy permits.

The procedure report digest is
`sha256:5562c1589ac7720a36aae8906762f6d53763c271152e3d57d52d06d1d5b93c66`.
It records successful backup, migration, snapshot recovery, restore, abandonment, archive access,
and successor-lineage rehearsals. Successful closure is separately established by both example
workflows.

## Performance finding

The first performance review ran concurrently with both example and procedure rehearsals. The
startup p95 was 892.695 ms against the 750 ms Windows budget, while the other four cases passed.
That report is preserved at
`sha256:52000b34022eae3f0a989c47c148c032622e91e72c67c5013de0d82e7671398c`.

An isolated rerun against the same installed wheel passed every budget. Startup p95 was
584.691 ms, status p95 was 1166.990 ms, journal replay p95 was 41.476 ms, context generation p95
was 702.686 ms, and archive access p95 was 821.281 ms. The isolated report digest is
`sha256:fc8a807f19a425d35528236477097325e76f01619a7cd1fae230794c6af8564a`.

The observed host-contention sensitivity remains a risk-review input. CI keeps performance in
dedicated matrix jobs rather than intentionally co-running these local workloads.

The first two pull-request executions at commit
`acaed32db684a5c33e7650c0362458a002d4623e` reproduced macOS / CPython 3.12 budget failures while
all other matrix cells passed. The first attempt measured startup p95 at 545.671 ms and status p95
at 1095.765 ms; the second measured startup p95 at 501.199 ms and status p95 at 1396.542 ms. The
existing macOS budgets of 500 ms and 1000 ms did not represent the slowest supported Python cell
on the current ARM hosted runner.

The owner approved recalibrating only the macOS platform budgets to 600 ms for startup and 1500 ms
for status. Measurement remains p95 over 20 samples after three warmups, workloads are unchanged,
Linux and Windows budgets are unchanged, and the macOS startup budget remains stricter than
Windows. A new pull-request matrix on the corrected commit remains required evidence.

## Security finding and remediation

The first snapshot scan identified canonical command-idempotency UUIDs as generic API-key
patterns. Inspection established that every finding was a lowercase UUID in either
`metadata.idempotency.key` within the canonical event journal or the corresponding receipt `key`;
no credential, digest, or arbitrary payload was accepted as an exception.

`.gitleaks.toml` now extends the default rules and permits only the `generic-api-key` rule when both
conditions hold:

- the extracted secret exactly matches the canonical lowercase UUID shape; and
- the finding has the exact journal path or a digest-named idempotency receipt path.

The rule remains active for every other secret shape and path. The configuration digest is
`sha256:0c8404293af2b9c33a1eb1f4b5c2c75b114551bc0988738d59821037165902ed`;
its focused regression-test digest is
`sha256:67a33f90d0764488fce16e044c1edaceab31015ecf60afcec862309f6f1223ff`.

The remediated review used Gitleaks 8.30.1 and pip-audit 2.10.1. It approved all 26 installed
dependency-license records, found zero known runtime vulnerabilities, passed Git-history scanning,
and passed the 409-file candidate snapshot. Its report digest is
`sha256:cc4347c75ad53c34d0f078d22020b4357e9c663aea9bdec7d750457b3bdb153c`.

## Remote evidence still required

The exact candidate commit must still pass:

- the pull-request quality, 9-cell complete-test, 18-cell installation, and 9-cell release-scenario
  topology;
- all dedicated remote performance cells;
- both examples and the procedure rehearsal on each operating system at CPython 3.12; and
- the same complete topology after merge to `main`.

Until both remote runs are bound by exact commit identity and result URLs, `verify-release` remains
in progress and M6 closeout remains blocked.
