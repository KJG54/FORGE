# FORGE M5 Increment 1 New-Chat Handoff

**Prepared:** 2026-07-27

## Repository baseline

- **Repository:** `C:\Users\kryst\Code\FORGE`
- **Remote:** `https://github.com/KJG54/FORGE.git`
- **Branch:** `main`
- **Published baseline commit:**
  `6179f7a22eddb072f99e3d495560e2214290bc6c`
- **Commit message:** `Close milestone 4`
- **Publication:** pushed directly to `origin/main` on 2026-07-27
- **CI:** not monitored for this publication at the owner's direction

Local `main` and `origin/main` pointed to the same exact commit, and the working tree was clean,
immediately before this handoff document was created. The handoff itself is an uncommitted
documentation-only change. At the start of the new chat, verify that the only expected local
change is this file unless the owner has made additional changes.

## Accepted and completed scope

- Milestone 0 is complete and accepted.
- Milestone 1 is complete and accepted.
- Milestone 2 is complete and owner-accepted.
- Milestone 3 is complete, owner-accepted, and published.
- Milestone 4 is complete, formally owner-accepted, and published.
- Milestone 5 implementation has not begun.

The authoritative M4 acceptance record is
[`docs/milestones/m4-report.md`](../milestones/m4-report.md). The repository owner formally
accepted M4 in the Codex task and authorized publication on 2026-07-27.

## M4 implementation summary

M4 delivered eleven bounded increments:

1. strict tracked, disabled-by-default local validator declarations;
2. exact-approval, no-shell supervised execution and immutable `CheckResult` capture;
3. owner-governed complete-scope amendment with derived invalidation;
4. state-neutral workflow deviations and current owner review;
5. non-bypassing exact emergency override records;
6. exact override-bound residual-risk acceptance;
7. append-only risk-acceptance revocation;
8. append-only general decision withdrawal;
9. exact formal run cancellation with terminal adapter-execution proof;
10. sanitized local-only security and handled-failure auditing; and
11. cumulative adversarial acceptance, claim-integrity hardening, and milestone closeout.

The final adversarial suite proves:

- a claim or failed check cannot reach verification or acceptance;
- trusted-data pack status cannot authorize executable validators;
- shell-looking input remains a literal argument under `shell=False`;
- revoked acceptance invalidates downstream progression;
- a withdrawn or superseded current decision stops authorizing its prior purpose;
- executable pack content, hostile imports, repository traversal, and forged claims fail closed;
  and
- same-user hostile processes remain outside FORGE's security boundary and require external
  operating-system, container, virtual-machine, or multi-user isolation.

The closeout audit found and fixed one integrity gap. New `claim-recorded` events bind the complete
canonical `Claim` digest as well as the exact artifact-revision digests. Restart now detects
altered assertion, limitation, attribution, or dependency content. Earlier claim-event history
remains readable under its original actor, sequence, run, step, revision, and transition
bindings, and still cannot authorize progression without independent checks, evidence,
verification, and owner acceptance.

Primary evidence:

- [`docs/milestones/m4-increment-11.md`](../milestones/m4-increment-11.md)
- [`docs/milestones/m4-report.md`](../milestones/m4-report.md)
- [`docs/validators.md`](../validators.md)
- [`docs/contracts.md`](../contracts.md)
- [`docs/persistence.md`](../persistence.md)
- [`SECURITY.md`](../../SECURITY.md)
- `tests/test_m4_acceptance.py`

## M4 validation evidence

Local Windows validation completed before publication:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 283 tests were exercised: 277 passed and 6 expected Windows symlink-privilege cases
  skipped;
- isolated source-distribution and wheel builds passed;
- a clean environment installed the wheel and loaded version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, refused premature
  acceptance with conflict exit 31, listed the sanitized local audit event, and passed doctor;
  and
- the installed wheel exported all 50 public schemas.

Remote Windows, macOS, and Linux results for the M4 closeout commit were not monitored or claimed.

## M5 boundary is not defined in this handoff

This handoff authorizes continuation into M5 discovery and bounded increment planning; it does not
invent M5 requirements. The repository does not currently contain an accepted M5 milestone report
or Increment 1 specification.

The authoritative Production-v1 roadmap was available in the earlier Codex planning task
`019f5cc3-e3bd-7a62-b83e-30e9ac2884bd`. The new chat must read that roadmap completely before
selecting M5 Increment 1. If the task cannot be accessed, ask the owner to attach or restate the
M5 portion rather than deriving it from the M4 limitations list.

In particular, do not assume every M4 limitation is scheduled for M5:

- provider APIs, executable pack providers, background execution, crash recovery, and
  cross-process cancellation are possible future capabilities only where the roadmap assigns
  them;
- explicit evidence, verification, and owner acceptance are deliberate authority boundaries, not
  unfinished automation by default;
- validator exit status intentionally remains structural evidence rather than semantic truth;
- same-user hostile-code isolation requires external controls and is not safely solved by a FORGE
  workflow feature;
- secret screening is intentionally heuristic defense in depth; and
- naming, distribution metadata, and support policy belong to release planning rather than being
  silently bundled into an unrelated increment.

## Required startup procedure

Before editing in the new chat:

1. Read this handoff completely.
2. Verify:
   - the current branch is `main`;
   - local `HEAD` and `origin/main` both equal
     `6179f7a22eddb072f99e3d495560e2214290bc6c`;
   - the remote is `https://github.com/KJG54/FORGE.git`; and
   - this handoff is the only expected working-tree change.
3. Read the authoritative Production-v1 roadmap completely. If unavailable, obtain the M5
   requirements from the owner before inventing scope.
4. Read:
   - `docs/constitution.md`;
   - `docs/milestones/m1-report.md`;
   - `docs/milestones/m2-report.md`;
   - `docs/milestones/m3-report.md`;
   - `docs/milestones/m4-report.md`;
   - all M4 increment reports;
   - ADR-0001 through ADR-0043;
   - `README.md`, `CHANGELOG.md`, `SECURITY.md`;
   - `docs/contracts.md`, `docs/workflows.md`, `docs/persistence.md`,
     `docs/recovery.md`, `docs/validators.md`, `docs/adapters.md`,
     `docs/artifacts-and-evidence.md`, and `docs/acceptance-and-invalidation.md`; and
   - the current contracts, core services, storage, record validation, CLI, security controls,
     and related tests for the chosen M5 boundary.
5. State the exact M5 Increment 1 objective, success criteria, exclusions, authority model,
   persistence impact, compatibility behavior, failure semantics, security implications, and
   validation plan before changing code.
6. Add an ADR for every material new architecture, trust, authority, process, persistence,
   recovery, security, public-contract, or CLI decision.
7. Implement only the first bounded M5 increment assigned by the roadmap.
8. Leave M5 Increment 1 uncommitted for owner review unless the owner explicitly requests
   publication.

## Non-negotiable inherited constraints

- Preserve claim, check, evidence, verification, and owner acceptance as separate facts.
- Do not let worker output, validator output, pack trust, a deviation, an override, or risk
  acceptance fabricate workflow support.
- Trusted-data pack status never grants executable authority.
- No shell-command-string execution.
- No executable capability starts without active exact-profile owner approval.
- Bind governed support to exact current records and digests; later revisions or authority removal
  must fail closed.
- Preserve failures, timeouts, cancellations, revocations, supersessions, amendments, and
  exceptional governance as immutable history.
- Preserve journal hash chaining, deterministic replay, snapshot binding, locking, idempotency,
  archive validation, recovery provenance, and cross-record validation.
- Keep local raw captures, secrets, locks, handoffs, and local audit events outside governed
  acceptance authority.
- Do not claim hostile-code sandboxing, complete secret discovery, authentication from owner
  identity, or semantic truth from process exit status.
- Maintain deterministic Windows, macOS, and Linux behavior.
- Do not begin a later M5 increment merely because it appears adjacent or convenient.

## Expected M5 Increment 1 planning output

Before implementation, the new chat should give the owner a concise boundary statement containing:

- the roadmap language being implemented;
- why the proposed slice is the smallest coherent increment;
- the public contracts and persisted records it changes or reuses;
- which actor has authority and how that authority is proven;
- exact failure and restart behavior;
- security claims and explicit non-claims;
- compatibility or migration requirements;
- focused and cumulative tests;
- installed-wheel acceptance; and
- the stop point after Increment 1.

If more than one viable first slice exists, compare them and recommend one. Do not change files
until missing roadmap context that would materially alter the choice has been resolved.

## Validation expected before owner review

At minimum, run:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pyright `
  --pythonpath .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m pytest -q `
  --basetemp=$env:TEMP\forge-pytest-m5-increment1
.\.venv\Scripts\python.exe -m build `
  --outdir $env:TEMP\forge-m5-increment1-dist
```

Install the resulting wheel into a clean environment and exercise the new public boundary from the
installed package. Export and count all public schemas. Record exact passed/skipped counts and do
not claim remote CI results unless they were actually observed for the exact published commit.

## Environment and GitHub notes

- The local project environment currently uses Python 3.14; the package supports Python 3.12 and
  newer.
- The package version remains `0.1.0a0`.
- GitHub CLI 2.93.0 is installed.
- GitHub authentication was healthy, keyring-backed, and had `repo` and `workflow` scopes when M4
  was published.
- Sandboxed GitHub or package operations may fail because network access is restricted. Retry an
  essential network operation with the appropriate approved permission before concluding that
  authentication or a dependency is broken.
- Publishing has followed the owner's direct-`main` workflow. Do not create a branch or pull
  request unless the owner requests one.
- The owner has repeatedly preferred publishing without waiting for CI. Still run proportional
  local validation and report accurately whether CI was or was not monitored.

## Suggested first message in the new chat

> Continue FORGE Production-v1 from
> `docs/handoffs/m5-increment-1-new-chat-handoff.md`. First verify the exact published M4 baseline
> at `6179f7a22eddb072f99e3d495560e2214290bc6c`, confirm this handoff is the only local change,
> read the authoritative Production-v1 roadmap and required repository evidence, and define the
> smallest coherent M5 Increment 1 boundary. Do not infer that every M4 limitation belongs to M5.
> Preserve the established authority and security invariants, implement only the authorized first
> increment, validate it fully from source and a built wheel, and leave it uncommitted until I
> explicitly authorize publication.
