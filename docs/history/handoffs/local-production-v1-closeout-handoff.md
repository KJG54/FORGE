# FORGE Local Production-v1 Closeout Handoff

**Prepared:** 2026-08-05

**Path update (2026-08-06):** the development record moved under `docs/history/`. Operative paths
in this handoff were updated to match; historical documents it cites were moved without edits.

**Status:** L9 automated validation is merged; native-app owner observation and governed
candidate-readiness closeout remain pending

**Target:** Complete the minimum native Codex and Claude Code owner-observed smoke, govern the
exact Local Production-v1 candidate through framework-change closeout, archive the initiative, and
stop without manufacturing final Production-v1 acceptance or publishing anything publicly.

## Purpose and authority

This handoff is for the next direct workspace agent handling Local Production-v1 closeout. It does
not authorize the agent to execute owner-only actions by implication. At every owner gate, present
the exact command and consequence, then wait for the owner to run it personally or explicitly
direct the agent to run it.

Framework-change closeout records only that one exact unpublished local candidate is ready for
extended owner testing. Final Local Production-v1 acceptance is a later owner decision after the
real-project campaign. No closeout step authorizes a tag, PyPI/TestPyPI, GitHub Release, repository
visibility change, public support channel, or other publication action.

## Verified repository baseline

- Repository: `C:\Users\kryst\Code\FORGE`
- Remote: `https://github.com/KJG54/FORGE.git`
- PR #29: merged on 2026-08-03
- PR head commit: `1e325fce9ad5d17ab141e32bec7135a4c286f920`
- Merge commit on `main`: `093b17ebe02040a7a54bb383f862bc76bba54ff1`
- PR URL: `https://github.com/KJG54/FORGE/pull/29`
- Local `main`, `origin/main`, and `origin/HEAD` all resolved to `093b17e` when this handoff was
  prepared.
- The deleted PR branch remained checked out locally at `1e325fc`; its tree matched the merged PR
  content. Start closeout from a fresh `codex/local-v1-closeout` branch based on merged `main`.
- The worktree was clean before this handoff file was added.

Suggested startup, preserving this uncommitted handoff and any later owner changes:

```powershell
git status --short
git switch main
git pull --ff-only
git switch -c codex/local-v1-closeout
git status --short
```

If unrelated changes exist, preserve them and resolve scope before staging. Authenticated GitHub
and Git network commands on Windows require access to the Windows keyring; do not treat a
sandboxed authentication error as invalid credentials.

## Exact candidate

The ignored binary artifacts are present locally and passed `tools.local_candidate verify` again
on 2026-08-05.

| Artifact | Size | SHA-256 |
|---|---:|---|
| `dist/local-production-v1/forge_governance-1.0.0-py3-none-any.whl` | 299,387 bytes | `f1a082aab295e5e616cd81c4dedd028b3504c8c520ef1a8489d2dc69c72b2017` |
| `dist/local-production-v1/forge_governance-1.0.0.tar.gz` | 1,389,645 bytes | `9304a6e51ac5aff4de3749cca82e289a7e787ac5e00b0445c92724704de7f9a0` |

Verify without rebuilding:

```powershell
.\.venv\Scripts\python.exe -m tools.local_candidate verify `
  --artifacts dist\local-production-v1 `
  --manifest release\local-production-v1\candidate-manifest.json `
  --hashes release\local-production-v1\SHA256SUMS
```

Do not silently replace either artifact. A candidate-blocking fix to shipped code, configuration,
protocol, or integrated documentation requires a new candidate identity and repetition of the
exact-wheel validation. Post-build observation and governance records may describe the fixed
artifacts without rebuilding them.

## Automated evidence already complete

Do not rerun the complete suite or CI merely for ceremony. The merged L9 evidence records:

- Ruff passed;
- strict Pyright passed with zero errors and warnings;
- schema `1.0`, 51 public models, and 94 CLI commands remained consistent;
- 408 tests passed, with 9 explicit Windows symbolic-link privilege skips;
- clean `venv` and `pipx` installs passed on Windows/CPython 3.14.4;
- `research-basic` completed 7 steps and `software-basic` completed 6, each with a healthy archive;
- backup, restore, migration, snapshot recovery, abandonment, archive access, and successor
  procedures passed;
- all five maintained performance budgets passed; and
- license, vulnerability, complete-history Gitleaks, and candidate-snapshot security review passed.

Rerun focused checks only for closeout-document changes. Repeat the complete candidate matrix only
if shipped candidate inputs change or new evidence specifically calls an earlier result into
question.

## Governed state at handoff

- Initiative: `26c0c628-cc77-478c-b77b-0c1d703891ac`
- Lifecycle: `active`
- Pack/workflow: `forge-framework-change / framework-change@0.1.0`
- Pack digest: `sha256:6e9ab5f0cdc8e67757b3fcd8cc710936149ca8f4df3a6c81d3fc0be29e3b68f4`
- Explanation profile: `mentored`
- Integrity: healthy
- `scope`: `awaiting_acceptance`
- `implement`: `invalidated`
- `verify-release`: `pending`
- `review-risk`: `pending`
- `closeout`: `pending`
- Current `change-scope` revision:
  `cf3f5d12-38ce-4e8b-85b4-b5adf2ff6768`
- Current `release-requirements` revision:
  `5a7ebeec-483f-4352-af15-79c69fd96567`
- Current scope claim: `756f7826-ba83-48b1-8fec-6e97ec0b0d61`
- Current passing `scope-reviewed` check:
  `ad01dfb0-a95b-4147-97b0-85e361c4bc57`
- Current scope evidence: `78fa0cf7-5c6f-4605-a194-7c6cf155e464`
- Prior scope acceptance `d25daa3c-333c-46c1-ada3-5ae018aa27f9` is stale, not revoked or current.
- `forge doctor`, `forge status`, and `forge next` were healthy and consistent on 2026-08-05.
- Only `change-scope` and `release-requirements` are registered current artifacts. The remaining
  workflow output roles have not been registered.

The scope became invalidated because L8's exact candidate-freeze and L9-validation clauses were
added to the working release requirements but had not been recorded as an immutable revision.
Recording revision 2 correctly invalidated dependent support. The rework claim, check, evidence,
and verification are complete; only renewed owner acceptance remains.

## First owner gate: renew scope acceptance

Present this command and its consequence. Do not run it until the owner personally executes it or
explicitly directs the agent to execute it:

```powershell
forge acceptance record scope --scope "L1 local Production-v1 scope and conversational contracts exactly as bound to change-scope revision cf3f5d12-38ce-4e8b-85b4-b5adf2ff6768, release-requirements revision 5a7ebeec-483f-4352-af15-79c69fd96567, passed check ad01dfb0-a95b-4147-97b0-85e361c4bc57, worker claim 756f7826-ba83-48b1-8fec-6e97ec0b0d61, and evidence packet 78fa0cf7-5c6f-4605-a194-7c6cf155e464; this renews implementation authority for L2-L9 but does not accept implementation, candidate readiness, publication, native-app results, or final Production-v1 status" --known-limitation "Native Codex and Claude Code owner-observed smoke remains pending" --residual-risk "Extended real-project usability remains owner judgment" --idempotency-key local-v1-l9-accept-scope-20260803 -C .
```

Consequence: this binds configured-owner acceptance to the exact current scope support and
completes only the `scope` step. It does not accept L9 implementation, validation, risk, closeout,
or final Production-v1 status. Afterward, quote the canonical receipt and run `forge next -C .`.

## Native-app observation required before readiness closeout

Automated and CLI provider checks do not satisfy this boundary. Complete the minimum smoke in
`release/local-production-v1/owner-test-guide.md` once in native Codex and once in native Claude
Code, using fresh tasks and disposable repositories installed from the exact wheel.

For each application, confirm with the owner that:

1. owner-authored `AGENTS.md` or `CLAUDE.md` bytes were preserved;
2. the agent used the installed protocol and found the next legal action without prior chat;
3. one routine mutation showed honest `direct-codex` or `direct-claude` operator provenance;
4. `Recorded` and `Means` were quoted separately from agent `Read` and `Next` judgments;
5. one consequential owner gate showed the exact command and consequence; and
6. no owner-only action ran until the owner explicitly directed it.

Record application versions, Python version, exact wheel digest, commands shown and executed,
receipt clarity, friction, and the owner's explicit observation. Label the results
`owner-observed`; do not infer that label from agent output. Update the post-build validation and
friction reports. If the smoke exposes a candidate blocker, stop governed closeout and return to a
new candidate identity. The longer 13-journey real-project campaign remains after framework
closeout and before final Production-v1 acceptance.

## Governed closeout sequence

Use `forge next`, `forge status`, `forge artifact list`, and the canonical receipts after every
mutation. Stable idempotency keys are mandatory. Capture generated run, artifact revision, claim,
check, and evidence IDs rather than guessing them.

The repeatable mechanics for each remaining step are:

1. begin the step;
2. register its exact required output artifacts;
3. complete the step with the active run ID and honest direct-agent operator provenance;
4. record the declared manual check from actual evidence;
5. register an evidence packet binding current artifact revisions, check, and claim;
6. run `forge verify <step>`;
7. stop at `awaiting_acceptance`, present the exact owner acceptance command and consequence, and
   wait for explicit owner direction; and
8. only after acceptance, continue to the next step.

### Implement

- Begin/rework `implement` only after renewed scope acceptance.
- Register `docs/history/milestones/local-v1-l9.md` as role `framework-changes`, title
  `Local Production-v1 L9 framework changes`, media type `text/markdown`.
- Claim only the merged L1-L9 implementation and exact candidate corrections.
- Record check ID `implementation-validated` and cite the merged PR, focused regressions, complete
  suite, quality gate, and candidate verification.
- Limit the claim/check/evidence explicitly: native usability and final owner acceptance remain
  separate.
- Verify, then obtain exact owner acceptance for `implement`.

### Verify release

- Complete both native-app smoke observations before freezing this step's report revision.
- Register `release/local-production-v1/validation-report.md` as role `verification-report`, media
  type `text/markdown`.
- Record check ID `release-checks-passed` using the already completed exact-wheel evidence plus the
  two owner-observed native smokes. Do not claim that owner observation is automated proof.
- Bind the report revision, implementation artifact revision, check, and claim in evidence.
- Verify, then obtain exact owner acceptance for `verify-release`.

### Review risk

- Register `release/local-production-v1/friction-report.md` as role `friction-report`.
- Register `release/local-production-v1/residual-risks.md` as role `residual-risk-report`.
- Incorporate native observations without erasing the historical automated findings.
- Record check ID `risk-review-complete`. Classify candidate blockers, final-acceptance blockers,
  documentation friction, provider observations, and future improvements separately.
- Keep same-user authority, heuristic secret scanning, dependency drift, backup completeness,
  ignored artifact preservation, Codex adapter fallback, Windows symlink skips, and extended
  usability visible.
- Verify, then obtain exact owner acceptance for `review-risk` with every high risk called out.

### Closeout

- Author `release/local-production-v1/release-readiness-record.md`. It must identify the exact wheel
  and sdist digests, accepted verification and risk revisions, native owner observations, remaining
  extended campaign, and the no-publication/final-acceptance boundary.
- Author `release/local-production-v1/lessons.md`. Preserve at least the Gitleaks identifier lesson,
  invalidated-run terminal-view defect, candidate-identity reset rule, owner-observation boundary,
  and why post-build evidence stays distinct from candidate bytes.
- Register the files as roles `release-readiness-record` and `lessons`.
- Record check ID `closeout-ready`; bind exact current artifacts, claim, and evidence.
- Verify, then obtain exact owner acceptance for `closeout`.

Do not pre-author owner acceptance IDs or claim exact scopes before FORGE generates the current
records. Inspect every record and construct each owner scope from the actual current IDs.

## Initiative archival

After all five workflow steps are completed and currently accepted, `forge next` should offer
successful closure. Present, but do not execute without explicit owner direction:

```powershell
forge close --summary "Close the Local Production-v1 framework-change initiative as an exact feature-complete unpublished local candidate ready for extended owner testing; this closure does not record final Production-v1 acceptance or authorize public publication" --idempotency-key local-v1-close-candidate-readiness-20260805 -C .
```

After closure:

- quote the canonical receipt and archive ID;
- run `forge doctor -C .`;
- inspect archive status and history through supported commands;
- confirm the archive is healthy and terminal;
- confirm no tag or public release was created; and
- update the closeout report with the archive ID and digest without rewriting archive bytes.

Do not create a successor initiative merely because the framework-change initiative closed. The
extended owner campaign and later final acceptance need a separately reviewed governance plan if
the owner wants them governed as a new initiative.

## Validation and publication discipline

- Do not rerun broad CI or the complete local matrix unless candidate inputs changed.
- For report-only and governed-record changes, run focused document/contract checks,
  `tools.local_candidate verify`, `forge doctor`, and `git diff --check`.
- If the exact wheel digest changes, discard all prior exact-wheel install and journey evidence and
  repeat the required candidate validation.
- Commit and publish closeout changes only when the owner requests it.
- Use a draft PR by default and state plainly that the PR closes candidate readiness, not final
  Production-v1 acceptance.
- Never tag, upload, create a GitHub Release, or configure publication channels under this handoff.

## Required reading

Before mutating governed state, read:

- this handoff completely;
- `docs/history/handoffs/local-production-v1-conversational-completion-handoff.md`;
- `docs/history/milestones/local-v1-l9.md`;
- `release/local-production-v1/candidate-manifest.json` and `SHA256SUMS`;
- `release/local-production-v1/validation-report.md`;
- `release/local-production-v1/friction-report.md`;
- `release/local-production-v1/residual-risks.md`;
- `release/local-production-v1/known-limitations.md`;
- `release/local-production-v1/owner-test-guide.md`;
- `release/local-production-v1/extended-testing-plan.md`;
- `release/local-production-v1/release-requirements.md`;
- `packs/forge-framework-change/workflows/framework-change.yaml`;
- `docs/acceptance-and-invalidation.md`, `docs/closure-and-archives.md`, and
  `docs/dogfooding.md`; and
- the live initiative through `forge doctor`, `forge status`, `forge next`, `forge artifact list`,
  `forge acceptance show`, and `forge history`.

## Non-negotiable boundaries

- Claims, checks, evidence, verification, acceptance, closure, and final Production-v1 acceptance
  remain separate facts.
- A merged PR and green automation do not imply owner acceptance.
- Native application observations require explicit owner confirmation.
- Same-user operator provenance is honest attribution, not authentication.
- Preserve the abandoned public-M7 archive and the closed M6 archive exactly.
- Do not modify archive bytes, history, or prior immutable records.
- Do not use a public release workflow, create a tag, or publish a package.
- Do not let final-acceptance testing become retroactive candidate-readiness evidence without an
  explicit reviewed record.

## Suggested opening prompt

> Continue FORGE Local Production-v1 closeout from
> `docs/history/handoffs/local-production-v1-closeout-handoff.md`. Verify merged `main`, the exact local
> candidate hashes, and live governed state before mutation. First present the renewed `scope`
> acceptance command and wait for explicit owner direction. Then coordinate the minimum native
> Codex and Claude Code owner-observed smoke. If both pass without a candidate blocker, govern the
> exact merged candidate through `implement`, `verify-release`, `review-risk`, and `closeout`,
> stopping at every configured-owner acceptance gate. Close and validate the initiative archive
> only after all steps are currently accepted. Do not rerun the complete suite unless candidate
> inputs change, do not infer final Production-v1 acceptance, and do not tag or publish anything.
