# M6 Increment 6 — Maintained Performance Budgets

## Authorized scope

- define explicit p95 budgets for startup, status, journal replay, context generation, and archive
  access;
- bind performance environments to the exact installation matrix;
- create deterministic real repository/archive/decision and synthetic journal workloads;
- measure user-facing CLI paths plus isolated canonical journal replay;
- emit environment-, workload-, sample-, statistic-, and budget-bound JSON results;
- fail closed on unsupported environments, malformed policy, measurement errors, or exceeded
  budgets; and
- document interpretation, non-claims, and closeout repetition.

## Explicit exclusions

Runtime behavior, public contracts, persisted production formats, migrations, pack bytes,
authority, package metadata, dependencies, optimizations, profiling integrations, CI
configuration, dogfooding, residual-risk reporting, release signing, publication, and M7 work are
not implemented.

The complete test suite, distribution rebuild, clean-wheel measurement, cross-platform and
expanded Python-version execution, and remote CI remain deferred to M6 closeout by owner direction.

## Measurement boundary

The policy uses three warmups, 20 measured samples, and nearest-rank p95. Four cases execute the
exact requested console script with fixed arguments and `shell=False`. Journal replay runs the
canonical implementation in-process for three iterations per sample against a deterministic valid
1,000-event hash chain.

Status and archive access validate five real abandoned archives. The active repository has 25 open
immutable decisions so status rendering and context generation exercise maintained non-empty
records. All fixtures are synthetic, temporary, and deleted on exit.

## Design evidence

[ADR-0055](../adr/ADR-0055-maintained-performance-budgets.md) records the end-to-end/in-process
split, workload, p95 statistic, platform budget, timeout, and no-new-dependency decisions.

## Validation evidence

Focused Increment 6 validation passed on Windows with CPython 3.14 and FORGE `0.1.0a0`:

- `6 passed` in the focused performance-policy and fixture tests;
- Ruff reported `All checks passed!`;
- strict Pyright reported `0 errors, 0 warnings, 0 informations`; and
- `git diff --check` reported no errors.

One complete local review used three warmups, 20 measured samples, five validated archives, 25 open
decisions, and a 1,000-event journal. Every nearest-rank p95 result remained within its Windows
budget:

| Case | Observed p95 | Windows budget |
|---|---:|---:|
| Startup | 597.676 ms | 750 ms |
| Active status | 1,259.251 ms | 1,500 ms |
| Journal replay | 44.204 ms | 200 ms |
| Context generation | 740.999 ms | 1,500 ms |
| Archive access | 903.729 ms | 1,500 ms |

This remains local source-environment evidence. Exact-wheel results for all supported
operating-system and Python-version cells remain M6 closeout requirements.

## Stop point

Stop after the policy, deterministic fixtures, measurement harness, focused tests, documentation,
ADR, and local observed result. Do not optimize runtime paths without a separately reviewed defect,
add CI, begin FORGE-governed dogfooding, produce the residual-risk report, or begin Increment 7
without a separate owner decision.
