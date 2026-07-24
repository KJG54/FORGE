# M4 Increment 2 — Supervised Validator Execution and Immutable Check Capture

## Authorized scope

- explicit execution of one configured validator for one check required by a step already awaiting
  verification;
- active exact-profile capability approval before process creation;
- immutable `RunRecord` attempt binding and one-time approval consumption before launch;
- no-shell argument-vector execution in the approved repository working directory;
- credential-denying environment allowlisting with FORGE-owned temporary paths;
- declared timeout and fixed bounded stdout/stderr capture;
- exact current artifact-revision and check-identity binding;
- immutable typed `CheckResult` capture for pass, failure, timeout, output overflow, launch error,
  and supervision error;
- restart and cross-record validation for the run, approval, invocation, check, and output digests;
  and
- read-only CLI inspection without rendering raw captured output.

## Explicit exclusions

Automatic evidence creation, `forge verify`, owner acceptance, lifecycle advancement, executable
pack providers, provider APIs, background execution, cross-process live cancellation, automatic
crash resume, semantic or factual output interpretation, hostile-code isolation claims, and later
M4 amendment/override/security hardening are not implemented.

## Design evidence

[ADR-0035](../adr/ADR-0035-supervised-validator-execution-and-check-capture.md) records the
validator-specific use of `RunRecord`, pre-launch authority consumption, state-neutral event
sequence, environment and capture policy, process-outcome mapping, interruption behavior, and
continued check/evidence/verification/acceptance separation.

[Trusted Local Validator Declarations](../validators.md) documents the operator workflow and
inspection boundary.

## Test evidence

Focused deterministic fake-validator tests cover success, nonzero failure, timeout, combined-output
overflow, declared-environment access, inherited-credential and home exclusion, credential-channel
refusal, absent approval, revocation, one-time consumption, profile drift, exact artifact-revision
binding, restart validation, CLI output non-disclosure, and no automatic evidence, verification, or
acceptance.

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- 233 tests passed with 6 expected Windows symlink-privilege skips;
- Hatchling produced the source distribution and wheel;
- a clean target loaded `forge` from the installed wheel and reported version `0.1.0a0`;
- the installed wheel exported all 48 schemas; and
- the installed-wheel CLI passed a deterministic approved validator execution and raw-output
  non-disclosure smoke test.

## Stop point

Stop after supervised local execution and immutable check capture. A passing check remains only one
governed fact; the owner must separately register evidence, invoke verification, and record
acceptance through their existing commands.
