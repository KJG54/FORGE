# FORGE M3 Increment 6 New-Chat Handoff

**Prepared:** 2026-07-19

## Repository baseline

- **Repository:** `C:\Users\kryst\Code\FORGE`
- **Remote:** `https://github.com/KJG54/FORGE.git`
- **Branch:** `main`
- **Increment 5 implementation commit:**
  `8a50dece37cf327e6e581417841a8b78db89c34f`
- **Increment 5 commit message:** `Add Claude Code discovery and safe preparation`
- **Increment 5 CI:** [GitHub Actions run 29676018101](https://github.com/KJG54/FORGE/actions/runs/29676018101)
  — passed on Windows, macOS, and Ubuntu.

The handoff itself is a documentation-only follow-up to the Increment 5 implementation commit.
At the start of the new chat, verify that local `HEAD`, `refs/remotes/origin/main`, and the latest
remote commit match and that the working tree is clean before making changes.

## Accepted and completed scope

- Milestone 0 is complete and accepted.
- Milestone 1 is complete and accepted.
- Milestone 2 is complete and owner-accepted.
- Milestone 3 is in progress.
- M3 Increments 1 through 5 are implemented and published.

The M3 sequence currently provides:

1. canonical provider-neutral agent context;
2. managed digest-bound `AGENTS.md` and `CLAUDE.md` references;
3. the provider-neutral `AgentAdapter` lifecycle and manual baseline;
4. Codex CLI discovery, diagnostics, and safe invocation preparation; and
5. Claude Code discovery, diagnostics, and safe invocation preparation.

Neither provider adapter starts a worker. `forge handoff` remains explicitly manual, and returned
worker content remains untrusted until the existing staged `forge import-result` workflow is used.

## Increment 5 implementation summary

Increment 5 registered `ClaudeAgentAdapter` and factored the provider-independent local-CLI
mechanics into `src/forge/adapters/_local_cli.py`. It added:

- `PATH` discovery and a non-persisted absolute `FORGE_CLAUDE_EXECUTABLE` override;
- bounded `claude --version`, `claude --help`, and `claude auth status` diagnostics;
- Claude-labelled version parsing and fail-closed stable-feature compatibility;
- a diagnostic environment that permits persisted `CLAUDE_CONFIG_DIR` discovery but excludes
  API keys, OAuth-token variables, and cloud-provider credentials;
- visible manual fallback for missing, non-runnable, incompatible, or unauthenticated Claude;
- exact canonical JSON and SHA-256 digest validation; and
- deterministic stdin preparation using non-interactive streaming JSON, plan mode, no session
  persistence, bare startup, only `Read,Glob,Grep`, strict MCP configuration without MCP servers,
  and disabled browser integration.

Process start, supervision, cancellation, output capture, automatic `AgentResult` production,
capability execution, and executable pack trust remain deferred. Persistence formats and the public
45-schema bundle are unchanged.

The design record is
[`docs/adr/ADR-0030-claude-code-discovery-and-safe-preparation.md`](../adr/ADR-0030-claude-code-discovery-and-safe-preparation.md),
and the implementation evidence is
[`docs/milestones/m3-increment-5.md`](../milestones/m3-increment-5.md).

## Increment 5 validation evidence

Local Windows validation completed before publication:

- 204 tests passed;
- 6 expected Windows symlink-privilege skips;
- Ruff passed;
- strict Pyright passed with 0 errors and 0 warnings;
- Hatchling source and wheel builds passed;
- a fresh environment installed the wheel successfully;
- installed-wheel version/help, initialization, configuration, bundled-pack validation,
  initiative creation, manual diagnostics, handoff, and 45-schema export passed;
- the installed Claude Code 2.1.207 CLI was detected as compatible and authenticated; and
- deterministic missing-Claude fallback selected the manual adapter.

## Authority for the next chat

The next authorized work is **M3 Increment 6 only**. Determine its exact requirements from the
attached Production-v1 Master Implementation Specification and the existing approved M3 sequence
before changing code. This handoff does not make a new governance decision and does not itself
define Increment 6 scope.

The current code and ADRs identify future prerequisites such as an isolated output workspace,
durable adapter-run lifecycle, bounded process supervision and cancellation, provider-output
capture, and staged `AgentResult` production. Treat these only as deferred design dependencies.
Implement them in Increment 6 only if the authoritative specification explicitly places them
there, and implement no later capability or milestone work.

## Required startup procedure

Before editing in the new chat:

1. Read the attached Production-v1 Master Implementation Specification completely.
2. Read the original FORGE handoff README and planning-response template for historical context.
3. Verify `main`, a clean working tree, the exact local and remote commits, remote synchronization,
   and the Increment 5 CI result.
4. Read the complete repository, especially:
   - `docs/constitution.md`;
   - all ADRs through ADR-0030;
   - milestone reports through `docs/milestones/m3-increment-5.md`;
   - `docs/adapters.md`, `docs/agent-context.md`, `docs/contracts.md`,
     `docs/handoffs-and-imports.md`, `docs/persistence.md`, `docs/workflows.md`, `README.md`, and
     `CHANGELOG.md`; and
   - the adapter, run, handoff/import, storage, CLI, and relevant test implementations.
5. State the exact Increment 6 boundary, exclusions, compatibility decisions, and validation plan
   before making changes.
6. Implement only that bounded increment and leave it uncommitted for owner review unless the owner
   explicitly authorizes a commit and push.

## Non-negotiable constraints

- Preserve local-first, provider-neutral, deterministic, auditable, and non-destructive behavior.
- Treat providers as replaceable untrusted workers, never as authoritative governed state.
- Do not grant adapters repository mutation services or collapse worker claims, checks, evidence,
  and owner acceptance.
- Preserve existing persistence, migration, recovery, archive, Git, and staged-import guarantees
  unless the specification explicitly requires a compatible bounded change.
- Do not silently repair journals, remove locks, resume interrupted commands, or recover unrelated
  state.
- Do not consume environment API keys or access tokens merely because they are present.
- Maintain Windows, macOS, and Linux compatibility.
- Do not begin Milestone 4 or absorb capability execution, pack executable trust, or other later
  work unless it is explicitly part of Increment 6.
- Add an ADR for any adapter-boundary, compatibility, trust, persistence, threat-model, or public
  CLI decision required by the increment.

## Validation expected before handoff

Run validation proportional to the completed increment, including:

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest-tmp-increment6
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pyright --project pyproject.toml `
  --pythonpath .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m hatchling build -d .dist-increment6
```

Also install the built wheel into a fresh environment and exercise the relevant CLI paths. Remove
only verified temporary validation artifacts afterward. Cross-platform provider tests should use
deterministic fake executables; local installed-provider checks are supplemental evidence.

## Environment notes

- The project virtual environment currently uses Python 3.14.4, while the package supports Python
  3.12 and newer.
- The local Claude Code CLI was version 2.1.207 and persisted-authenticated when Increment 5 was
  validated.
- `gh auth status` reports an expired GitHub CLI token, but normal Git credentials successfully
  push directly to `origin/main`. Do not expose or replace credentials as part of FORGE work.

## Suggested first message in the new chat

> Continue FORGE Production-v1 from
> `docs/handoffs/m3-increment-6-new-chat-handoff.md`. First verify the repository and Increment 5
> CI baseline, then read the authoritative specification and all required project evidence.
> Determine and implement only M3 Increment 6. Do not commit or push the Increment 6 changes until
> I explicitly authorize it.
