# M6 Increment 3 — Static Examples and Workflow Rehearsal

## Authorized scope

- add one uninitialized software example for the bundled `software-basic` workflow;
- add one uninitialized synthetic research example for the bundled `research-basic` workflow;
- supply every declared output artifact and map it to its exact step, role, and check;
- add a temporary-only rehearsal harness for an exact installed `forge` console executable;
- complete, close, archive, and diagnose both example copies through unchanged public commands;
  and
- document the distinction between static example content, synthetic rehearsal records, human
  acceptance, and fresh-user evidence.

## Explicit exclusions

Runtime behavior, public contracts, persistence, migrations, pack bytes, authority, package
version, CI configuration, expanded installation-matrix execution, full documentation completion,
supply-chain review, performance budgets, dogfooding, friction reporting, release publication,
and M7 work are not implemented.

Full-suite pytest, rebuilt distributions, clean-wheel installation, remote CI, and cross-platform
rehearsals are intentionally deferred to M6 closeout under the owner's accelerated workflow
direction. Increment 3 uses only focused structural/static checks and the two directly relevant
local rehearsals.

## Authority, persistence, failure, and security semantics

The examples ship no governed state and grant no authority. The harness creates only fresh
temporary copies, uses a synthetic owner, applies conspicuous limitations to claims, checks,
evidence, and acceptances, and removes all generated state when the process exits. It cannot point
at an existing repository.

Every subprocess uses a fixed argument vector with `shell=False`. Unknown examples, a missing or
non-file executable, missing output artifacts, command failures, unexpected output, unhealthy
active state, invalid closure, unhealthy archive state, or doctor failure stop the rehearsal.

Research content is synthetic and repository-local. It contains no participant, credential,
external capture, or personal data and makes no externally factual claim.

## Design evidence

[ADR-0052](../adr/ADR-0052-static-example-repositories-and-temporary-rehearsal.md) records why
examples remain uninitialized and why automated acceptance is confined to disposable release
testing.

## Validation evidence

- focused scenario, bundled-workflow, artifact, documentation, secret-screening, and harness
  boundary coverage: 4 passed;
- focused Ruff coverage for the harness and Increment 3 tests: clean;
- focused strict Pyright coverage for the harness and Increment 3 tests: 0 errors and 0 warnings;
- `git diff --check`: clean;
- the locally installed `forge` console script reported `0.1.0a0`;
- the research rehearsal completed all 7 steps, closed the initiative, validated a healthy archive,
  and passed doctor;
- the software rehearsal completed all 6 steps, closed the initiative, validated a healthy
  archive, and passed doctor; and
- both rehearsals used fresh temporary copies that were deleted automatically.

The complete pytest suite, distribution rebuild, clean-wheel example rehearsal, cross-platform
execution, and remote CI were intentionally not run. They remain M6 closeout evidence.

## Stop point

Stop after both example directories, workflow maps, temporary rehearsal harness, focused
conformance tests, documentation, and local source-environment rehearsals. Do not start the full
documentation set, supply-chain work, performance work, dogfooding, closeout matrix, or Increment
4 without a separate owner decision.
