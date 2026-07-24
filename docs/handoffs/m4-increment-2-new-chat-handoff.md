# FORGE M4 Increment 2 New-Chat Handoff

**Prepared:** 2026-07-24

## Repository baseline

- **Repository:** `C:\Users\kryst\Code\FORGE`
- **Remote:** `https://github.com/KJG54/FORGE.git`
- **Branch:** `main`
- **Published baseline commit:**
  `7c96bab4652ae40cd56117f6e8d6e24201dd20d8`
- **Commit message:** `Add declarative local validator capabilities`
- **Increment 1 CI:** [GitHub Actions run 29981338333](https://github.com/KJG54/FORGE/actions/runs/29981338333)
  — passed on Windows, macOS, and Ubuntu.

The working tree was clean and synchronized with `origin/main` immediately before this handoff
document was created. The handoff itself is an uncommitted documentation-only change. At the start
of the new chat, verify that the only expected local change is this file unless the owner has made
additional changes.

## Accepted and completed scope

- Milestone 0 is complete and accepted.
- Milestone 1 is complete and accepted.
- Milestone 2 is complete and owner-accepted.
- Milestone 3 is complete, owner-accepted, and published.
- Milestone 4 is in progress.
- M4 Increment 1 is implemented and published.

M3 established provider-neutral context, managed vendor references, manual/Codex/Claude adapters,
governed agent execution, exact executable capability approval and revocation, pack-data trust
lifecycle, and cross-adapter acceptance. Agent output still enters the same untrusted import,
claim, check, evidence, verification, and owner-acceptance sequence.

## M4 Increment 1 implementation summary

Increment 1 added the non-executing trusted-local-validator boundary:

- strict public `LocalValidatorDefinition` records under
  `forge.yaml.capabilities.local_validators`;
- `validator.`-namespaced, disabled-by-default registry entries;
- separate executable and ordered argument fields with no shell-command-string field;
- normalized repository-root or repository-relative working-directory rules;
- timeouts from 1 through 3,600 seconds;
- symbolic expected outputs, environment-variable names, and `SideEffectClass` risk;
- read-only resolution of absolute, repository-relative, or `PATH` executables;
- rejection of missing or irregular executables, unsafe paths, newline/NUL invocation parts,
  malformed environment names, duplicate declarations, and Windows `.bat`/`.cmd` shims;
- reuse of preview-first owner capability approval and immutable revocation;
- exact definition-version and digest matching for every validator approval scope, including
  `approved-for-project`; and
- proof that a valid trusted-data pack may name a capability ID but cannot register or authorize
  the executable profile.

Increment 1 does **not** start validators, create validator runs, record `CheckResult` objects,
interpret output, produce evidence, verify a step, accept work, or advance lifecycle state.

The primary evidence is:

- [`docs/adr/ADR-0034-declarative-local-validator-capabilities.md`](../adr/ADR-0034-declarative-local-validator-capabilities.md)
- [`docs/milestones/m4-increment-1.md`](../milestones/m4-increment-1.md)
- [`docs/validators.md`](../validators.md)
- `tests/test_validator_capabilities.py`

## Increment 1 validation evidence

Local Windows validation completed before publication:

- 226 tests passed;
- 6 expected Windows symlink-privilege skips;
- Ruff passed;
- strict Pyright passed with 0 errors and 0 warnings;
- source distribution and wheel builds passed;
- a clean target installed the wheel and passed version, initialization, and strict
  configuration validation; and
- the installed wheel exported 48 schemas, including
  `local-validator-definition.schema.json`.

Remote CI for the exact published commit passed on Windows, macOS, and Ubuntu.

## Intended next boundary

The next candidate is **M4 Increment 2 — supervised validator execution and immutable check-result
capture**.

This handoff is not itself an owner authorization or a substitute for the authoritative roadmap.
Before editing, the new chat must confirm the exact Increment 2 boundary from the Production-v1
roadmap and the completed Increment 1 stop point. If the owner authorizes Increment 2, keep it to
the smallest safe execution slice needed to:

- select one declared validator required by the current workflow step;
- require an active exact-profile capability approval before process creation;
- use the declared executable and argument vector with shell execution disabled;
- resolve and enforce the declared working directory;
- construct an allowlisted environment containing only declared names and safe platform
  essentials, never arbitrary inherited credentials;
- enforce the declared timeout and bounded stdout/stderr capture;
- bind execution to the exact current artifact revisions and governing step/check identity;
- preserve every failed, successful, timed-out, and errored attempt immutably;
- create a typed `CheckResult` whose capability, approval, invocation, timestamps, exit status,
  outcome, limitations, and digest remain auditable; and
- leave evidence registration, `forge verify`, and owner acceptance as explicit later actions.

The new chat must decide through an ADR whether validator attempts reuse the existing `RunRecord`
contract or need a compatible validator-specific execution record, how one-time approvals are
consumed, and how output capture is preserved without introducing a second source of lifecycle
truth.

## Explicit exclusions for the next increment

Unless the authoritative Increment 2 boundary explicitly requires one of these as an inseparable
prerequisite, do not implement:

- automatic evidence-packet creation;
- automatic `forge verify` transitions;
- automatic owner acceptance or gate approval;
- executable validator definitions supplied by trusted-data packs;
- executable pack providers or hooks;
- provider APIs, background workers, or remote execution;
- cross-process live cancellation;
- broad cancellation-policy redesign;
- automatic crash resume;
- output claims about semantic or factual truth;
- hostile-code isolation claims;
- scope-amendment, override, risk-acceptance, or incident-recovery hardening assigned to later M4
  increments; or
- M5 work.

## Required startup procedure

Before editing in the new chat:

1. Read the authoritative Production-v1 roadmap completely. It is available in the prior Codex
   planning task `019f5cc3-e3bd-7a62-b83e-30e9ac2884bd`; if that task cannot be read, ask the owner
   to attach the specification rather than inventing requirements.
2. Verify `main`, the exact local and remote commits, remote synchronization, the CI result, and
   the expected handoff-only working-tree change.
3. Read:
   - `docs/constitution.md`;
   - ADRs through ADR-0034;
   - `docs/milestones/m3-report.md`;
   - every M4 increment report available, currently
     `docs/milestones/m4-increment-1.md`;
   - `docs/contracts.md`, `docs/validators.md`, `docs/adapters.md`,
     `docs/artifacts-and-evidence.md`, `docs/workflows.md`, `docs/persistence.md`,
     `docs/recovery.md`, `README.md`, and `CHANGELOG.md`; and
   - the current capability, verification, run, cancellation, record-validation, locking,
     idempotency, CLI, and security tests and services.
4. State the exact Increment 2 scope, exclusions, persistence compatibility, authority model,
   failure semantics, and validation plan before changing code.
5. Add an ADR for any new process, trust, persistence, check-result, cancellation, security, or
   public CLI decision.
6. Implement only the authorized bounded increment.
7. Leave Increment 2 uncommitted for owner review unless the owner explicitly says to publish,
   commit and push, or update both local and remote branches.

## Non-negotiable constraints

- Preserve `claim → check → evidence → owner acceptance` as four separate facts.
- A zero exit status may support a passing check but can never prove work completion, create
  evidence automatically, or authorize acceptance.
- Trusted-data pack status never grants executable authority.
- No shell-string command execution.
- No validator starts without an active exact-profile owner capability approval.
- Bind checks to exact current artifact revisions; later revisions must make prior support stale.
- Preserve failed, timed-out, errored, and successful attempts rather than overwriting history.
- Do not leak credentials through environment inheritance, stdout/stderr, governed records, or
  tracked configuration.
- Preserve journal, snapshot, idempotency, locking, archive, recovery, and cross-record validation
  guarantees.
- Maintain Windows, macOS, and Linux behavior using deterministic fake validator executables in
  automated tests.
- Continue to state that same-user malicious processes require external operating-system or
  container isolation.

## Validation expected before owner review

Run:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pyright --project pyproject.toml `
  --pythonpath .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m pytest -q `
  --basetemp=$env:TEMP\forge-pytest-m4-increment2
.\.venv\Scripts\python.exe -m build --no-isolation `
  --outdir $env:TEMP\forge-m4-increment2-dist
```

Install the built wheel into a clean target and exercise the new validator CLI from the installed
package. Verify schema export and a deterministic fake-validator success, failure, timeout, output
limit, environment allowlist, approval refusal, revocation, one-time consumption, profile drift,
and no-auto-evidence/no-auto-acceptance path. Remove only verified temporary artifacts created by
the validation run.

## Environment and GitHub notes

- The project virtual environment uses Python 3.14.4; the package supports Python 3.12 and newer.
- The package version remains `0.1.0a0`.
- GitHub CLI 2.93.0 is installed.
- GitHub authentication is healthy, keyring-backed, and has `repo` and `workflow` scopes.
- A sandboxed `gh auth status` can falsely report an invalid token because the sandbox blocks
  GitHub's validation request. Rerun GitHub network operations with the approved network-enabled
  permission before asking the owner to reauthenticate. Do not expose, rotate, or replace the
  token based only on a sandboxed failure.
- Publishing in this project has followed the owner's established direct `main` workflow. Do not
  create a branch or pull request unless the owner requests one.

## Suggested first message in the new chat

> Continue FORGE Production-v1 from
> `docs/handoffs/m4-increment-2-new-chat-handoff.md`. First verify the exact published Increment 1
> baseline and CI, read the authoritative roadmap and required repository evidence, then determine
> and implement only M4 Increment 2. Preserve the claim/check/evidence/acceptance separation and do
> not execute shell strings, allow trusted-data packs to grant execution, or begin later M4 work.
> Leave Increment 2 uncommitted until I explicitly authorize publication.
