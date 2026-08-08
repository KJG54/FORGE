# ADR-0035: Supervised Validator Execution and Check Capture

**Status:** Accepted

**Milestone:** M4 Increment 2

## Context

M4 Increment 1 introduced strict local-validator declarations and exact-profile owner approval but
stopped before process creation. The next boundary must preserve every attempted check, consume
one-time authority before a process can start, bind the result to exact artifact revisions, and
retain the constitutional separation between a check, evidence, verification, and owner acceptance.

Normal `RunRecord` history already binds executable attempts to capability approvals. Workflow work
runs, however, also drive `in_progress` state and cancellation policy. A validator evaluates a step
that is already `awaiting_verification`; treating it as a new workflow work run would create a
second and incorrect lifecycle transition.

Raw validator output can also contain arbitrary project text. It must be bounded and inspectable
without becoming tracked governance content or being echoed through the normal CLI.

## Decision

Add explicit synchronous:

```text
forge check run <step> <check> --validator <capability-id>
```

The selected step must be active and `awaiting_verification`, the check ID must be one of that
step's locked `check_requirements`, and the capability must be one configured
`LocalValidatorDefinition` with an active exact-profile owner approval.

Reuse `RunRecord` as the immutable pre-process attempt contract, but store validator attempts under
`.forge/active/validator-runs/`. A state-neutral `validator-run-started` event binds the run,
future check-result ID, capability and approval, complete invocation digest, check identity, and
exact current target artifact revisions. This record and event commit before process creation.
An `approved-once` approval is consumed by that immutable run binding even if launch, supervision,
timeout, or capture later fails.

The process uses the approved resolved executable and ordered arguments with `shell=False`. The
working directory is the repository root or the one approved normalized repository-relative
directory. The environment begins empty and receives only:

- declared non-credential variable names whose values exist in the caller environment;
- safe platform essentials `LANG`, `LC_ALL`, `SYSTEMROOT`, and `WINDIR` when present; and
- FORGE-constructed `TEMP`/`TMP` or `TMPDIR` values pointing inside the attempt's local directory.

Names recognizable as credential, token, password, secret, private-key, access-key, or API-key
channels make a validator profile unavailable. FORGE never records environment values.

Execution uses the declared timeout and a fixed 1 MiB combined stdout/stderr capture ceiling.
Overflow, timeout, and supervision failure terminate and then, if required, kill the child process.
Raw captures remain Git-ignored under `.forge/local/validator-runs/<run-id>/`. Governed check
history records only their canonical local paths, SHA-256 digests, and byte counts. Normal check
commands never render the captured bytes, and archives do not copy `.forge/local/`.

Every handled attempt produces one immutable `CheckResult` and the existing `check-recorded` event.
Capability-backed results add typed approval, invocation, execution-state, capture-path, digest,
and size fields while existing manual check records and their digest calculation remain compatible.
The process mapping is deliberately narrow:

- completed exit status 0 becomes `passed`;
- completed nonzero exit status becomes `failed`; and
- timeout, output overflow, launch error, or supervision error becomes `error`.

Every result states that process outcome and captured bytes do not establish semantic or factual
truth. A passing result may satisfy the declared check only after the existing record-backed
selection logic evaluates it. Execution creates no `EvidencePacket`, performs no `forge verify`
transition, records no owner acceptance, and does not otherwise change step state.

The two-event `check_run` command pattern is eligible for conservative receipt recovery only when
both `validator-run-started` and `check-recorded` committed. A host interruption after only the
start event remains an incomplete command and cannot be replayed, completed, or marked successful
automatically.

## Consequences

Validator authority is consumed before process creation and every normally returned failure class
has an immutable check fact. The existing run contract remains the common attempt identity without
overloading workflow `active_run_ids` or cancellation transitions. `forge check list|show` is the
inspection surface for validator results; ordinary `forge run` views remain workflow-work views.

Tracked history stays compact and does not retain arbitrary output bytes. Local captures are useful
diagnostic material but are not lifecycle truth and can be removed without changing the governed
result. As elsewhere in FORGE, a malicious process with the repository owner's operating-system
permissions can alter local files or race supported commands; stronger hostile-code isolation
requires an external sandbox or container.

Background execution, cross-process live cancellation, automatic crash resume, evidence creation,
verification, acceptance, executable pack providers, semantic output interpretation, and broader
M4 amendment/override/security hardening remain outside this decision.
