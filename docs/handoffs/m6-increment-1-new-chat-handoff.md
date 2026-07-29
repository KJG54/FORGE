# FORGE M6 Increment 1 New-Chat Handoff

**Prepared:** 2026-07-28

## Repository baseline

- **Repository:** `C:\Users\kryst\Code\FORGE`
- **Remote:** `https://github.com/KJG54/FORGE.git`
- **Accepted published baseline:** `df20b65e6dc04c03dfd6dd526e771664281f0ff2`
- **Baseline commit:** `Merge pull request #6 from KJG54/codex/m5-increment-7`
- **Baseline branch:** local `main` and `origin/main`
- **Acceptance:** M5 explicitly owner-accepted in the Codex task on 2026-07-28
- **Package version:** `0.1.0a0`
- **Supported Python:** 3.12 and newer
- **Local validation Python:** 3.14.4
- **GitHub CLI:** 2.93.0 with Windows-keyring authentication

Immediately before preparing this handoff, local `main` and `origin/main` pointed to the exact
baseline above and the working tree was clean. Acceptance and handoff edits were then started on
`codex/m5-acceptance-m6-handoff`, and the owner subsequently requested their publication. A
receiving agent must verify the actual branch, `HEAD`, remote state, and working tree rather than
assuming this preparation state is still current.

## Accepted and completed scope

- M0 is complete and owner-accepted.
- M1 is complete and owner-accepted.
- M2 is complete and owner-accepted.
- M3 is complete and owner-accepted.
- M4 is complete and owner-accepted.
- M5 is complete and owner-accepted.
- M6 implementation has not begun.

The authoritative M5 acceptance record is
[`docs/milestones/m5-report.md`](../milestones/m5-report.md). M5 delivered seven bounded
increments:

1. the complete declarative `research-basic` workflow through unchanged core services;
2. digest-bound research evidence and citation templates;
3. strict data-only structural text validators that do not claim factual truth;
4. Minimal and Mentored profiles completing the four-profile educational model;
5. canonical record-derived, digest-bound long-gap resumption summaries;
6. bounded, fail-closed advisory filesystem context discovery with measured sufficiency; and
7. shared bundled-pack conformance and closeout against all M5 roadmap exit criteria.

The accepted M5 result proves:

- software and research initiatives use the same core services;
- all 51 public contract models remain domain-neutral;
- all four explanation profiles preserve identical governance;
- a long-paused initiative resumes from canonical records without chat history;
- a repository-local data-only pack validates and creates without Python content; and
- maintained software and research discovery scenarios reached perfect precision and recall, so
  the roadmap's evidence trigger for SQLite Full-Text Search (FTS) was not met.

## M5 validation evidence

Local Windows closeout validation:

- shared closeout conformance: 4 passed;
- cumulative M5 coverage: 33 passed with 1 expected Windows privilege-based symlink skip;
- complete suite: 310 passed with 7 expected Windows privilege-based symlink skips;
- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- `git diff --check` passed;
- Hatchling 1.31.0 built the source distribution and wheel;
- a clean Python 3.14 environment installed the wheel;
- the installed CLI validated both bundled packs, created a Mentored research initiative, passed
  restart and doctor health, and imported FORGE from `site-packages`; and
- the installed wheel exported 51 public schemas plus `index.json` (52 files total).

Remote closeout evidence:

- Increment 7 implementation commit `f66cf03` passed both push and pull-request CI matrices on
  Windows, macOS, and Ubuntu;
- evidence commit `e621d02` independently passed the same six jobs; and
- no separate CI run for merge commit `df20b65` was observed, so do not claim one.

## Authoritative M6 roadmap boundary

The authoritative Production-v1 roadmap is in Codex planning task
`019f5cc3-e3bd-7a62-b83e-30e9ac2884bd`. Read it completely before defining Increment 1. Its M6
boundary is **Release Candidate** hardening.

M6 delivers:

- compatibility and migration tests for all pre-v1 schemas;
- Windows, macOS, and Linux matrices across supported Python versions;
- installation through `pipx` and ordinary virtual environments;
- complete user, pack-author, adapter-author, architecture, security, troubleshooting, and
  recovery documentation;
- example software and research repositories;
- dependency, license, vulnerability, and secret reviews;
- performance budgets for startup, status, journal replay, context generation, and archive access;
- FORGE-governed dogfooding of its own release work; and
- a release-candidate friction and residual-risk report.

OpenTelemetry, SQLite FTS, and release signing may be added only if evidence justifies them. They
cannot block core release-candidate readiness and are not automatically authorized by entering M6.

M6 exit criteria:

- fresh users complete both example workflows from built distributions;
- upgrade, backup, archive, abandonment, successor, and recovery procedures are rehearsed;
- no critical governance, integrity, import, path, or secret defect remains;
- public compatibility commitments are documented; and
- the owner explicitly resolves every release-blocking risk.

M6 is not permission to publish `1.0.0`. Public production publication, tags, final support policy,
release artifacts, and the M7 owner gate remain separate.

## M6 Increment 1 is not selected by this handoff

This handoff authorizes M6 discovery and bounded increment planning. It does not silently choose a
first implementation slice. The receiving agent must compare viable first increments and recommend
the smallest coherent dependency-leading boundary.

In particular, assess whether the first slice should establish:

- the pre-v1 compatibility/schema inventory and migration-test matrix;
- the supported Python/operating-system/install acceptance matrix;
- or another prerequisite demonstrably required before those two.

Do not bundle documentation completion, examples, performance budgets, security reviews,
dogfooding, friction reporting, and release acceptance into one oversized first increment.

## Required startup procedure

Before editing:

1. Read this handoff completely.
2. Verify:
   - the current branch and working tree;
   - local `main` and `origin/main`;
   - whether the acceptance/handoff branch was published or merged;
   - the remote URL; and
   - that no unrelated owner changes are present.
3. Fetch with prune using Windows-keyring-aware host access. Never treat a sandboxed authentication
   failure as invalid GitHub credentials.
4. Read the complete authoritative Production-v1 roadmap from task
   `019f5cc3-e3bd-7a62-b83e-30e9ac2884bd`. If it is unavailable, ask the owner for the M6 text
   rather than reconstructing requirements from deferred-work lists.
5. Read:
   - `docs/constitution.md`;
   - `docs/milestones/m1-report.md` through `docs/milestones/m5-report.md`;
   - all M5 increment records and ADR-0044 through ADR-0049;
   - `README.md`, `CHANGELOG.md`, and `SECURITY.md`;
   - `docs/contracts.md`, `docs/persistence.md`, `docs/workflows.md`, `docs/migrations.md`,
     `docs/recovery.md`, `docs/adapters.md`, `docs/validators.md`, `docs/git-policy.md`,
     `docs/continuity.md`, and `docs/closure-and-archives.md`;
   - `pyproject.toml`, `.github/workflows/ci.yml`, package/build configuration, schema registry,
     migration registry, bundled packs, and installed-wheel smoke patterns; and
   - the focused tests relevant to the proposed M6 Increment 1 boundary.
6. Inventory every pre-v1 persisted/schema format actually supported. Do not equate public model
   count with released migration sources.
7. State the exact Increment 1 objective, success criteria, exclusions, authority model,
   persistence and compatibility impact, failure/restart semantics, security implications,
   cross-platform strategy, validation plan, and stop point before changing code.
8. Add an ADR for every material new architecture, compatibility, support, trust, persistence,
   migration, security, release-process, or public-contract decision.
9. Implement only the owner-approved bounded Increment 1.
10. Leave Increment 1 uncommitted and unpushed unless the owner explicitly requests publication.

## Non-negotiable inherited constraints

- FORGE governs work; it does not become an autonomous builder or release publisher.
- Preserve claims, checks, evidence, verification, owner acceptance, milestone acceptance, and
  release acceptance as distinct facts.
- Trusted-data packs never grant executable authority.
- No shell-command-string execution.
- No executable capability starts without active exact-profile owner approval.
- Bind governed support to exact current records and digests; later revision or authority removal
  must fail closed.
- Preserve journal hash chaining, deterministic replay, snapshot binding, cross-process locking,
  idempotency, recovery provenance, archive validation, and immutable terminal history.
- Preserve original bytes and explicit provenance for migrations. Never silently normalize or
  rewrite an unknown pre-v1 format.
- Keep credentials, raw captures, local audit events, locks, caches, and staging outside governed
  acceptance authority.
- Do not claim hostile-code isolation, cryptographic owner authentication, complete secret
  discovery, semantic truth, or cross-platform success without exact evidence.
- Structural validators and successful processes remain checks, not factual truth or acceptance.
- SQLite FTS remains deferred unless new measured evidence shows bounded discovery is insufficient.
- M6 work cannot tag, publish, or promise Production v1; that authority belongs to M7.
- Maintain deterministic Windows, macOS, and Linux behavior.
- Use one branch per bounded increment. After an online merge, fetch/prune, verify ancestry,
  synchronize local `main`, safely delete the merged local branch, then create the next branch.

## Expected M6 Increment 1 planning output

Before implementation, give the owner:

- the exact roadmap language being implemented;
- the dependency reason this slice should be first;
- at least two viable boundaries when more than one exists;
- the recommended boundary and its tradeoffs;
- public contracts and persisted records changed or reused;
- compatibility and migration claims, including explicit non-claims;
- supported-platform and installation implications;
- security and supply-chain implications;
- focused, cumulative, distribution, and cross-platform validation;
- documentation and evidence artifacts created; and
- the exact stop point before Increment 2.

## Validation expectations

At minimum, preserve the current local checks:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pyright `
  --pythonpath .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m pytest -q `
  --basetemp <fresh-repository-local-or-temporary-directory>
.\.venv\Scripts\python.exe -m build --no-isolation `
  --outdir <fresh-temporary-directory>
```

Install the exact wheel into a clean environment outside the source tree. Exercise the new public
boundary from the installed package, export and count schemas, and test every migration or
compatibility claim against preserved fixtures. Record precise pass/skip counts.

For M6 changes affecting supported platforms, packaging, installation, or CI, inspect the exact
published commit's Windows, macOS, and Linux results. Do not use an earlier commit or a different
branch as final evidence.

## Environment and GitHub notes

- Authenticated `gh` and Git network commands on Windows must request narrowly scoped host access
  so they can reach the Windows keyring and network.
- Never treat a sandboxed `gh auth status` failure as proof that authentication is invalid.
- Do not move credentials to environment variables or plaintext storage to work around isolation.
- GitHub operations use `https://github.com/KJG54/FORGE.git`.
- The repository currently uses a branch-and-pull-request workflow.
- Draft pull requests are the publishing default unless the owner explicitly requests ready status.
- CI currently runs Python 3.12 on `ubuntu-latest`, `macos-latest`, and `windows-latest`. Expanding
  that matrix is M6 work only after its exact increment is selected.

## Suggested first message for the M6 agent

> Continue FORGE Production-v1 from
> `docs/handoffs/m6-increment-1-new-chat-handoff.md`. Verify the accepted M5 baseline and current
> Git state, read the complete authoritative roadmap, and compare viable M6 Increment 1 boundaries
> before editing. Recommend the smallest dependency-leading Release Candidate slice, state its
> exact compatibility, persistence, authority, security, platform, validation, and stop
> boundaries, and do not begin M7 publication work. Preserve every inherited governance and
> integrity invariant, use built-package evidence, and leave the increment uncommitted until I
> explicitly authorize publication.
