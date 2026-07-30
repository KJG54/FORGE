# FORGE M7 Production-v1 Completion Handoff

**Prepared:** 2026-07-29
**Target:** Complete M7 and the remaining work required for an owner-approved public Production v1

## Purpose and authority

This handoff gives a receiving agent the repository baseline, the authoritative M7 roadmap, the
known release gaps, and a recommended incremental path through public `1.0.0` completion.

It authorizes investigation, bounded planning, implementation, validation, and preparation of M7
work. It does **not** grant standing authority to:

- select or clear a public name on the owner's behalf;
- create or overwrite a Git tag;
- configure a package-index publisher or repository secret;
- publish to PyPI, GitHub Releases, or another public channel;
- record owner acceptance; or
- begin post-v1 feature work.

Each irreversible external action and every configured-owner gate still requires an explicit owner
decision bound to the exact current commit, artifacts, evidence, limitations, and residual risks.

## Repository baseline

- **Repository:** `C:\Users\kryst\Code\FORGE`
- **Remote:** `https://github.com/KJG54/FORGE.git`
- **Accepted main baseline:** `b873435e12530b9af4f066fb82d121f0c748f2d9`
- **Baseline commit:** `Merge pull request #16 from KJG54/codex/m6-closeout`
- **Merged PR:** `https://github.com/KJG54/FORGE/pull/16`
- **Handoff branch when prepared:** `codex/m7-handoff`
- **Package distribution:** provisional `forge-governance`
- **Import package and CLI:** provisional `forge`
- **Package version:** `0.1.0a0`
- **Supported release-candidate matrix:** CPython 3.12–3.14 on Windows, macOS, and Linux
- **M6 archive:** `ea57c39e-98a9-475f-bb60-bb41f7e90f7c`
- **M6 archive digest:** `sha256:5a25afde013b3013752b97db88587eb6808cd583ddd05439a293b59085750325`
- **M6 archive state:** hardened successful closure with 50 hash-chained events

PR #16's exact head commit `4b4966f4da3226e50b33e4e072ce53220ee2223f` passed all 38 jobs in
GitHub Actions run `30485925991`. The merged-`main` run
[`30486631428`](https://github.com/KJG54/FORGE/actions/runs/30486631428) completed with 37 of 38
jobs passing. `Release scenarios (macos-latest, Python 3.12)` failed at `Enforce performance
budgets`: `archive_access` recorded a 1044.293 ms p95 against its 1000 ms budget, with a 1213.944 ms
maximum. The receiving agent must triage and resolve this red merged baseline before using it as
Production-v1 evidence.

Immediately before this document was added, local `main` and `origin/main` both pointed to
`b873435`. Verify the actual branch, `HEAD`, remote state, working tree, tags, releases, and CI
before relying on this baseline.

## Completed and accepted scope

- M0 is complete and owner-accepted.
- M1 is complete and owner-accepted.
- M2 is complete and owner-accepted.
- M3 is complete and owner-accepted.
- M4 is complete and owner-accepted.
- M5 is complete and owner-accepted.
- M6 is complete, owner-accepted, merged, and preserved in a hardened archive.
- M7 implementation and public release have not begun.

The cumulative M6 evidence is
[`docs/milestones/m6-report.md`](../milestones/m6-report.md). M6 delivered eight increments:

1. the pre-v1 compatibility and migration baseline;
2. the 18-cell built-distribution installation matrix;
3. software and research example repositories and installed-wheel rehearsals;
4. complete task-oriented documentation routes;
5. dependency, license, vulnerability, Git-history, and snapshot secret review;
6. maintained cross-platform performance budgets;
7. governed FORGE self-dogfooding; and
8. one-wheel release-candidate validation, risk review, lessons, and closeout.

M6 verified one exact candidate through complete local checks plus 38-job pull-request and
merged-main matrices. It intentionally did not tag, sign, upload, publish, create a support
commitment, or authorize M7.

## Mandatory pre-M7 blocker: clean-checkout terminal state

The first receiving agent must resolve this before creating an M7 successor initiative.

### Reproduction

On the clean post-merge checkout at `b873435`:

```console
forge status -C .
```

reports:

```text
Integrity: integrity_error
Blocker: Terminal retirement is incomplete; retry the terminal command with the same idempotency key
```

The M6 archive itself validates, and no archive staging or retired-active directory remains. The
problem is that successful closure leaves an empty `.forge/active/` directory as an in-memory
completion marker, but Git cannot track empty directories. A branch switch or clean clone therefore
removes that directory. Current status logic treats its absence as interrupted retirement, while
initiative creation assumes the directory exists and calls `iterdir()` directly.

This is a public repository-embedding defect, not a reason to modify the immutable M6 archive or
manually manufacture M7 state.

### Required repair boundary

Implement the smallest fail-closed fix that makes a clean checkout of a fully archived repository
healthy and able to create a successor:

- absence of `.forge/active/` is a normal no-active-initiative state only when all archives
  validate and no archive staging or retired-active marker exists;
- a real staging or retired marker continues to report an interrupted terminal transaction;
- successor creation safely creates the missing empty active directory before writing;
- irregular, symbolic, or non-directory active paths remain refused;
- archive bytes, terminal events, closure records, and the M6 archive digest remain immutable;
- `forge status`, `forge doctor`, and successor creation work after a clean Git checkout; and
- interruption-safe close/abandon retry behavior remains unchanged.

Add a regression that simulates successful closure followed by removal of the empty active
directory, as Git does, and proves healthy status plus safe successor creation. Exercise both
closure and abandonment where the shared boundary applies. If the solution changes the documented
terminal transaction or repository persistence contract, add an ADR and update the canonical
archive, persistence, Git-policy, and recovery documentation.

Do not use a tracked placeholder inside `.forge/active/`; current status correctly treats
unexpected active content as an integrity error, and a placeholder would become part of the
governed-state boundary.

## Mandatory pre-M7 blocker: red merged-main performance evidence

The exact PR head passed all 38 jobs, but the post-merge run for the accepted `main` commit failed
one macOS/Python 3.12 performance-budget job. All other performance cases and all other jobs passed.
Treat the failure as unresolved evidence, not automatically as either a product regression or
harmless runner noise.

Before M7 release work:

- reproduce `python -m tools.performance_review` on comparable macOS/Python 3.12 runners;
- compare repeated distributions and the PR-head evidence, especially the `archive_access` p95
  tail;
- inspect whether archive validation performs avoidable repeated work;
- prefer a measured implementation fix when one exists;
- change the budget or sampling policy only with documented evidence that the existing threshold
  is invalid, preserving a meaningful regression gate; and
- obtain a green run on the exact merged repair commit.

Do not rerun until green and discard the failed evidence. Preserve the failed run URL, measured
values, diagnosis, chosen remedy, and successful replacement evidence in the governed M7 record.

## Authoritative M7 roadmap

The authoritative Production-v1 roadmap is preserved in Codex planning task
`019f5cc3-e3bd-7a62-b83e-30e9ac2884bd`. Its final amended M7 boundary is:

### M7 — Public Production v1

Deliver:

- publish `1.0.0` after naming clearance and final acceptance;
- publish source and Python distribution artifacts;
- publish release notes, compatibility matrix, supported-version policy, known limitations, and
  migration guide;
- establish public issue, security, bug, and pack-proposal workflows;
- record release evidence, acceptance, residual risk, and lessons as FORGE artifacts; and
- freeze v1 persisted contracts under semantic-version guarantees.

Exit criteria:

- a new user can install FORGE, initialize a repository, use either bundled pack, work manually or
  through supported adapters, recover interrupted work, close or abandon an initiative correctly,
  inspect its archive, and create a successor;
- repository tags, distributions, schemas, documentation, and bundled packs agree on versions;
  and
- post-v1 work begins only after a recorded retrospective and prioritization decision.

This text is the governing outcome, but the receiving agent should read the complete roadmap task
before changing release contracts. The roadmap explicitly keeps OpenTelemetry, SQLite Full-Text
Search, release signing, container isolation, shared operation, semantic retrieval, and ESDF import
outside required v1 completion unless separately justified and owner-approved.

## Current M7 gap inventory

The following were true at baseline and require explicit disposition:

- `FORGE`, `forge-governance`, the `forge` import package, and the `forge` CLI are still documented
  as provisional; no accepted naming or trademark-clearance record exists.
- `pyproject.toml` and `src/forge/__init__.py` declare `0.1.0a0`.
- `pyproject.toml` declares `Development Status :: 2 - Pre-Alpha` and has no public project URLs.
- `release/installation-matrix.json`, installation commands, filenames, tests, and other release
  evidence bind `0.1.0a0`.
- all public persisted records use `schema_version: "1.0"`; that contract version is distinct from
  the Python distribution version and must not be mechanically rewritten.
- bundled packs and the local framework-change pack have independent versions; M7 must document
  their compatibility rather than blindly forcing every version to `1.0.0`.
- `CHANGELOG.md` contains only `[Unreleased]`; there is no dated `1.0.0` release section.
- `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, installation guidance, and several canonical
  references still describe pre-alpha or no-supported-release behavior.
- only `.github/workflows/ci.yml` exists. There is no owner-approved release workflow, package-index
  trusted publisher, environment protection, GitHub Release automation, or rollback/yank procedure.
- there are no repository tags or public release records at the handoff baseline.
- there are no checked-in issue forms for bugs, features, security routing, or pack proposals.
- no M7 FORGE initiative or M7-specific release workflow pack exists.
- the existing `forge-framework-change` workflow explicitly closes release-candidate work **without
  publishing Production v1**. Do not reuse it unchanged as publication authority.
- merged-main CI run `30486631428` failed the macOS/Python 3.12 `archive_access` performance budget
  and must be resolved before it can support M7 acceptance.

## Recommended execution shape

Use one mandatory prerequisite followed by eight bounded M7 increments. The increment boundaries
below are a recommendation, not fabricated owner acceptance. Present the exact scope, tradeoffs,
artifacts, checks, irreversible effects, and stop point for owner approval before each increment.

### Prerequisite P0 — Restore a healthy post-archive Git baseline

- Fix the missing-empty-active-directory defect described above.
- Add clean-checkout status, doctor, successor, close, and abandon regressions.
- Diagnose and resolve the macOS/Python 3.12 `archive_access` performance-budget failure without
  weakening the gate merely to obtain green CI.
- Run focused transaction/Git tests, the complete suite, distribution smoke, and remote CI.
- Merge the fix, synchronize local `main`, and confirm `forge status` is healthy from a fresh
  checkout.
- Do not create M7 governed state until this repair is merged.

### Increment 1 — M7 scope, naming, channels, and governed release workflow

- Complete owner-reviewed name, distribution, CLI, public-mark, and package-index availability
  checks. Record uncertainty honestly; automated searches are not legal clearance.
- Decide canonical repository, documentation, issue, security-reporting, and package publication
  URLs.
- Decide whether signing, attestations, a software bill of materials, TestPyPI rehearsal, and
  tokenless trusted publishing are in scope. The roadmap does not make signing a v1 blocker.
- Add an ADR for the v1 release/version/channel contract.
- Add a dedicated declarative, Python-free, capability-free M7 release workflow pack. Recommended
  steps are scope, prepare, verify candidate, approve publication, publish, verify publication,
  retrospective, and closeout. Every step should require exact outputs, checks, evidence, and
  owner acceptance.
- After the pack is reviewed and the P0 fix is merged, create an M7 successor initiative referencing
  M6 archive `ea57c39e-98a9-475f-bb60-bb41f7e90f7c`. Trusting the pack as data must not grant
  executable or publication authority.
- Stop for owner acceptance of the exact M7 scope and locked workflow.

### Increment 2 — Freeze the v1 compatibility and version contract

- Define the semantic-version guarantees beginning at Python distribution `1.0.0`.
- Freeze supported persisted contracts, schema exports, journal formats, migration edges, public
  CLI behavior, and explicit non-claims.
- Decide and document independent bundled-pack and workflow version compatibility.
- Update package version sources, matrix metadata, schema/index metadata where applicable, tests,
  and version-consistency checks.
- Do not rewrite existing `schema_version: "1.0"` records or immutable archives merely because the
  distribution becomes `1.0.0`.
- Add a single automated consistency check covering package metadata, runtime `--version`,
  distribution filenames, release configuration, documentation, schemas, and bundled-pack
  compatibility declarations.
- Stop before representing the candidate as publicly released.

### Increment 3 — Public support, security, and contribution workflows

- Replace pre-alpha support language with an explicit supported-version policy.
- Establish public bug and pack-proposal issue forms and a clear feature/request route.
- Establish a safe public security-reporting path without directing vulnerability details into
  ordinary public issues. External repository settings require owner action and verification.
- Update contribution, code-of-conduct, triage, disclosure, and maintenance expectations.
- Define severity, supported branches, fix/backport policy, and response statements without
  inventing service-level commitments the maintainer cannot sustain.
- Stop for owner acceptance of the support burden and public communication channels.

### Increment 4 — Release documentation and package metadata

- Produce dated `1.0.0` release notes from the accepted milestone evidence.
- Finalize the compatibility matrix, supported-version policy, known limitations, migration guide,
  installation guide, troubleshooting, recovery, and public quick start.
- Update `README.md`, documentation indexes, examples, `CHANGELOG.md`, package classifiers, author
  and project URLs, and all alpha-version filenames and commands.
- Ensure limitations still state the same-user threat boundary, heuristic secret detection,
  optional-adapter requirements, and exact supported platforms.
- Build the sdist and wheel and validate their rendered metadata and included file inventory.
- Stop before uploading or tagging.

### Increment 5 — Reproducible release automation and rehearsal

- Design an owner-gated release workflow that builds one source distribution and one wheel from an
  exact commit or immutable tag, records hashes, and reuses those exact artifacts for validation
  and publication.
- Prefer short-lived, repository/environment-scoped publication authority over stored plaintext
  tokens when the selected package index supports it; verify current official guidance at
  implementation time.
- Prevent pull requests, ordinary pushes, forks, and unapproved actors from publishing.
- Add environment protection, explicit target selection, concurrency/idempotency behavior, failure
  recovery, and a no-retag/no-overwrite rule.
- Rehearse the workflow without publishing Production v1. A TestPyPI or private-channel rehearsal
  is an external action and requires owner approval; it is not final PyPI evidence.
- Document GitHub Release, package-index upload, checksum, yank, rollback, and incident procedures.
- Signing or attestations remain an explicit owner decision, not an assumed blocker.

### Increment 6 — Exact Production-v1 candidate acceptance

- Freeze one candidate commit and build one exact sdist and wheel.
- Repeat the complete source, build, metadata, license, vulnerability, Git-history, snapshot-secret,
  performance, backup, migration, recovery, archive, abandonment, successor, and fresh-user
  boundaries.
- Run the full Windows/macOS/Linux and CPython 3.12–3.14 test matrix.
- Run all 18 venv/`pipx` installation cells against the exact wheel.
- Complete both bundled workflows and manual, Codex, and Claude adapter paths where compatible.
- Test a fresh clone whose only initiative is archived, proving the P0 repair.
- Produce exact hashes, release manifest, compatibility statement, residual-risk register, and
  pre-publication evidence packet.
- Stop at a dedicated owner publication gate. A green matrix, candidate artifact, or merged commit
  is not publication acceptance.

### Increment 7 — Owner-gated `1.0.0` publication

- Present the owner with the exact commit SHA, tag name, artifact hashes, package metadata, target
  repositories, release notes, known limitations, rollback/yank procedure, and residual risks.
- Only after explicit approval, create the immutable `v1.0.0` tag and publish the exact approved
  source and wheel artifacts to the approved package index and GitHub Release.
- Never move, replace, delete, or silently rebuild the release tag or artifacts.
- Record every external result URL, identifier, timestamp, digest, and failure as evidence.
- If any target or artifact differs from the approved manifest, stop and obtain a new owner
  decision rather than improvising.

### Increment 8 — Post-publication verification, retrospective, and M7 closeout

- Install `forge-governance==1.0.0` from the public package index in clean environments rather than
  from the source tree or a local wheel.
- Verify `forge --version`, help, initialization, both bundled packs, all schemas, manual handoff,
  supported adapters, recovery, successful closure, abandonment, archive inspection, and successor
  creation.
- Confirm the Git tag, GitHub Release, source distribution, wheel, hashes, schemas, documentation,
  package metadata, and bundled-pack compatibility all agree.
- Record publication evidence, final residual risks, user-facing limitations, failures and
  corrections, and lessons as FORGE artifacts.
- Obtain final owner acceptance, close and archive the M7 initiative, and publish the retrospective.
- Record a separate prioritization decision before any post-v1 feature work begins.

## Production-v1 definition of done

FORGE is complete for the authoritative Production-v1 roadmap only when:

- P0 is merged and a fresh post-archive checkout is healthy;
- the public name and distribution channel have explicit owner clearance;
- the exact `1.0.0` contracts, metadata, docs, packs, schemas, and support policy agree;
- the complete exact-artifact candidate matrix passes;
- the owner approves the exact irreversible publication action;
- the approved tag, GitHub Release, source distribution, and wheel are public and immutable;
- clean public-index installations pass the complete v1 user journey;
- release evidence, acceptance, residual risk, and lessons are governed and archived; and
- the retrospective and post-v1 prioritization gate are recorded.

OpenTelemetry, SQLite FTS, release signing, a web or desktop UI, hosted accounts, cloud sync,
provider APIs, a remote pack marketplace, vector search, a distributed workflow engine, multi-user
authentication, hostile-code isolation, and ESDF import are not required to declare Production v1
complete under the authoritative roadmap.

## Required startup procedure

Before editing:

1. Read this handoff completely.
2. Verify the current branch, clean worktree, remote URL, local `main`, `origin/main`, tags, GitHub
   releases, and package version.
3. Fetch with prune using Windows-keyring-aware host access. Never treat a sandboxed authentication
   failure as invalid credentials.
4. Confirm PR #16 is merged, preserve the failed merged-main run `30486631428`, and reproduce or
   otherwise rigorously diagnose its macOS/Python 3.12 `archive_access` performance failure.
5. Reproduce the P0 integrity blocker from a clean checkout.
6. Read the complete authoritative roadmap task
   `019f5cc3-e3bd-7a62-b83e-30e9ac2884bd`.
7. Read:
   - `docs/constitution.md`;
   - `docs/milestones/m0-report.md` through `docs/milestones/m6-report.md`;
   - every M6 increment report;
   - all ADRs, especially release, compatibility, migration, archival, Git, trust, security, and
     one-wheel closeout decisions;
   - `README.md`, `CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md`;
   - `docs/compatibility.md`, `docs/installation.md`, `docs/security.md`,
     `docs/supply-chain-security-review.md`, `docs/release-candidate-closeout.md`,
     `docs/closure-and-archives.md`, `docs/successors.md`, and `docs/recovery.md`;
   - `pyproject.toml`, `src/forge/__init__.py`, `.github/workflows/ci.yml`,
     `release/*.json`, both bundled packs, the local framework-change pack, schema registry,
     migration registry, build tools, and release harnesses; and
   - the archived M6 initiative through supported `forge status --archive` and `forge history`
     commands.
8. Complete P0 on its own branch and merge it before creating M7 governed state.
9. Compare the recommended M7 increment plan with the exact owner priorities. Record material
   changes rather than silently broadening the roadmap.
10. Leave every increment uncommitted and unpushed until the owner explicitly requests publication.

## Non-negotiable inherited constraints

- FORGE governs work; it does not become an autonomous builder or publisher.
- Worker claims, checks, evidence, verification, owner acceptance, milestone acceptance, release
  acceptance, and external publication remain distinct facts.
- Never self-accept or infer owner approval from green CI, a merge, a tag, or an earlier broad
  statement when exact evidence has materially changed.
- Trusted-data packs never grant executable or publication authority.
- Keep command execution shell-free where the existing boundary requires argument vectors.
- Preserve hash chaining, deterministic replay, snapshot binding, locking, idempotency, recovery
  provenance, exact-byte artifact preservation, archive validation, and terminal immutability.
- Never alter the M6 archive to fix current code or documentation.
- Use one exact built distribution across downstream candidate tests.
- Never store package-index credentials, repository tokens, signing keys, or raw secrets in
  governed artifacts, Git, logs, handoffs, or plaintext environment files.
- Treat tags, releases, package uploads, yanks, repository settings, and public issue/security
  channels as consequential external state changes requiring exact authority.
- Do not claim cryptographic owner authentication, hostile same-user isolation, complete secret
  detection, factual truth, or unobserved cross-platform success.
- Do not make deferred enhancements a v1 blocker without new evidence and owner approval.
- Use one branch and pull request per bounded increment. After merge, fetch/prune, verify ancestry,
  synchronize local `main`, and remove merged branches safely before starting the next increment.

## Validation expectations

Use focused tests during bounded increments and reserve the complete release topology for the
pre-publication and post-publication gates. At minimum:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pyright `
  --pythonpath C:\Users\kryst\Code\FORGE\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m pytest <focused-tests> `
  --basetemp <fresh-path-outside-the-repository>
.\.venv\Scripts\python.exe -m build --no-isolation `
  --outdir <fresh-path-outside-the-repository>
```

Do not place Git-sensitive pytest repositories under the real repository's ignored
`.forge/local/` tree; inherited ignore rules can invalidate Git-policy tests. Use a fresh external
temporary directory. Windows symbolic-link privilege skips must remain explicit.

Before publication, repeat the complete one-wheel matrix and all M6 release scenarios on the exact
M7 candidate. After publication, repeat the user-facing journey from the public package index.
Record exact pass/skip counts, commit SHAs, run URLs, artifact hashes, package URLs, and limitations.

## GitHub and publication notes

- Authenticated `gh` and Git network operations on Windows require narrowly scoped host access to
  the Windows keyring and network.
- Never move credentials into plaintext or environment variables to work around keyring isolation.
- Draft pull requests remain the default unless the owner explicitly requests ready status.
- A release workflow should use protected environments and least-privilege permissions.
- Verify current official package-index and GitHub guidance before configuring trusted publishing,
  attestations, signing, or provenance.
- Never use a pull-request event or untrusted fork context for package publication.
- Never reuse an existing version or move an existing public tag.

## Suggested first message for the receiving agent

> Continue FORGE from
> `docs/handoffs/m7-production-v1-completion-handoff.md`. Verify merged baseline `b873435`, preserve
> and diagnose the macOS/Python 3.12 performance failure in main CI run `30486631428`, and reproduce
> the clean-checkout terminal-state blocker before editing. First propose and implement only the P0
> repairs that make an archive-only checkout healthy and successor-capable without weakening
> interrupted-retirement detection or changing the immutable M6 archive, and restore green
> performance evidence without weakening the gate merely to pass. After P0 is merged, read the
> complete authoritative roadmap task
> `019f5cc3-e3bd-7a62-b83e-30e9ac2884bd`, present the recommended eight-increment M7 plan for owner
> approval, and create a dedicated data-only governed Production-v1 release workflow. Preserve
> exact owner gates for naming, version freeze, irreversible publication, post-publication
> verification, and retrospective closeout. Do not tag, upload, publish, or begin post-v1 work
> without a new exact owner decision.
