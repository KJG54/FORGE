# FORGE

**Framework for Orchestrated Reasoning, Governance, and Execution**

FORGE is a local-first governance framework for human-directed, AI-assisted work. It embeds a
versioned initiative in an ordinary repository and records how work is scoped, authorized,
claimed, checked, evidenced, accepted, paused, recovered, closed, or abandoned.

FORGE governs work. It is not the worker, an autonomous agent runtime, a hosted project manager,
or a same-user security sandbox.

> **Pre-alpha foundation:** The name, distribution name, public marks, contracts, and CLI remain
> provisional. Milestones 1 and 2 are accepted and Milestone 3 implementation is in progress; this
> is not a public production release.

## Current capabilities

M1 Increments 1 through 8 provide strict versioned data contracts, deterministic JSON Schema export,
project configuration validation, owner identity bootstrap, repository discovery, safe path
resolution, non-destructive `forge init`, ordered event journals, deterministic replay, atomic
snapshot replacement, explicit journal/snapshot mismatch detection, safe declarative pack loading,
immutable workflow locks, owner-authorized initiative creation, manual runs, and restart-safe status
and next-action reporting. Increment 4 adds immutable artifact revisions, conservative exact-byte
preservation, working-copy drift reporting, worker claims, manual structured checks, evidence
packets, dependency references, and record-backed verification transitions. Increment 5 adds
owner-only acceptance and revocation, append-only decisions and supersession, deterministic stale
propagation after revision or revocation, and an explicit rework path for invalidated steps.
Increment 6 adds provider-neutral manual handoffs and a two-phase staged result-import pipeline with
bounded schemas, path and symlink controls, secret screening, previews, explicit collision actions,
and single-event artifact registration.

Increment 7 adds owner-only successful closure, complete-step and current-acceptance gates,
exact-byte archive manifests, preserved-object verification, read-only archived status and history,
and terminal immutability through supported commands.

Increment 8 adds read-only repository diagnostics, event-derived run inspection and cancellation,
selectable Standard/Guided presentation, a restarted-process end-to-end software acceptance
walkthrough, and a data-only synthetic community-research workflow proving the core is not
software-specific. The complete evidence and limitations are recorded in the
[M1 evidence report](docs/milestones/m1-report.md).

M2 Increment 1 adds canonical event serialization, SHA-256 previous-hash chaining, snapshot
journal-head binding, and explicit read-only compatibility for complete M1 journals. Migration,
recovery, and the remaining M2 hardening are not yet implemented.

M2 Increment 2 adds repository-wide cross-process locking for supported mutations, inspectable
owner metadata, live contention refusal, and non-destructive stale-lock diagnostics.

M2 Increment 3 adds optional or generated mutation idempotency keys, journal-bound request
identity, completion receipts tied to exact event hashes, duplicate-free successful retry, and
conservative interruption diagnostics.

M2 Increment 4 adds owner-authorized `forge recover` for missing, invalid, or mismatched active
snapshots when—and only when—the complete journal remains valid and hash-chained. Recovery
preserves observed snapshot bytes, verifies governed records and objects, records provenance, and
can safely resume its own interrupted post-commit snapshot or receipt write.

M2 Increment 5 adds owner-authorized `forge pause` and `forge resume`, exact resumable-state
binding, active-run safety checks, inspection-only paused behavior, and durable summaries for
continuing work without relying on prior chat history.

M2 Increment 6 upgrades new successful closures to non-preliminary archives with deterministic
staging, atomic promotion, archive-before-retirement validation, and same-idempotency-key recovery
for interruptions after the closure event commits. Existing M1 archives remain readable with their
original preliminary label.

M2 Increment 7 adds owner-authorized `forge abandon` with required reason, unfinished-work summary,
and unresolved-risk statements. Abandonment is allowed from healthy active or paused work after
all governed runs stop, and creates a distinct non-success terminal record and resumable atomic
archive without requiring completed checks or acceptances.

M2 Increment 8 adds successor initiative creation through repeatable `forge create --predecessor`
links. Every predecessor must be a valid immutable archive; the successor receives a new ID,
workflow, journal, pack-trust decision, and empty governance state. Exact terminal predecessor
artifact bytes may be explicitly registered as new revisions with verified provenance.

M2 Increment 9 expands read-only archive inspection. Normal status now summarizes every validated
archive, selected status exposes terminal ownership, lineage, manifest and journal details, and
archived history identifies its source while displaying the verified M2 event hash chain.

M2 Increment 10 adds explicit registered schema migration. `forge migrate` previews without
persistent mutation; `forge migrate --apply` preserves exact legacy M1 journal bytes, atomically
installs the M2 hash chain and migration provenance, and resumes safely with the same idempotency
key after a post-commit interruption.

M2 Increment 11 adds the hybrid Git collaboration policy. Initialization preserves existing ignore
rules while exposing governed configuration and `.forge/**` records and excluding `.forge/local/`.
Diagnostics evaluate effective Git ignore and index state without staging, committing, or changing
the index; repositories without Git remain fully usable in filesystem-only mode.

M2 Increment 12 extends owner-authorized recovery to one conservative journal case: an
unambiguously EOF-truncated final record after a complete valid M2 prefix. FORGE preserves the
entire damaged journal and observed snapshot, atomically commits the valid prefix plus recovery
provenance, and refuses complete, malformed, legacy, archived, or otherwise ambiguous histories.

M2 Increment 13 adds owner-authorized recovery for one mechanically complete active command whose
journal events committed before its receipt. Registered event patterns prevent partial multi-event
commands from being marked complete; exact recovery provenance and same-key resume preserve the
original effects without repeating them.

M2 Increment 14 adds explicit owner-authorized stale-lock remediation. `forge remediate-lock`
removes only a strictly valid same-host lock whose PID is definitively dead, atomically preserves
its exact bytes with local provenance, excludes concurrent mutations through a separate guard, and
supports same-key restart without touching governed initiative state. Live, foreign-host,
malformed, symbolic, missing, changed, and ambiguous locks are refused.

M2 is complete and owner-accepted. The final evidence is recorded in the
[M2 evidence report](docs/milestones/m2-report.md).

M3 Increment 1 adds the canonical provider-neutral agent context. `forge agent context` writes
deterministic tracked JSON and Markdown views containing only the active governed assignment,
selected required-input metadata, current decisions, authority boundaries, evidence expectations,
return contract, and blockers. It never crawls unrelated project, archive, ignored, environment, or
local-secret content. It is the neutral source used by later integrations.

M3 Increment 2 adds optional digest-bound managed references in root `AGENTS.md` and `CLAUDE.md`.
Codex and Claude targets preview create/append/replace/no-change plans without mutation or echoing
user content; `--apply` explicitly confirms the plan, regenerates neutral context, and atomically
changes only the delimited managed span while preserving all other bytes. Adapters and capabilities
remain deferred.

M3 Increment 3 adds the provider-neutral `AgentAdapter` lifecycle interface and an always-available
manual implementation. `forge agent doctor` reports selection, compatibility, limitations, and an
explicit manual fallback; `forge handoff` now exercises the same digest-bound preparation boundary
without starting a process or changing governed state. External tool discovery remains deferred.

M3 Increment 4 registers a Codex CLI adapter with bounded executable/version probes, stable-feature
compatibility, persisted-login diagnostics, and exact-context read-only invocation preparation.
Missing, incompatible, or unauthenticated installations fall back visibly to manual. FORGE does
not start Codex or allow it to write project state; manual handoff and staged import remain the
execution boundary.

M3 Increment 5 registers the symmetric Claude Code adapter with bounded executable, stable-feature,
and persisted-authentication diagnostics. Its prepared non-interactive plan is digest-bound,
session-free, extension-free, MCP-free, browser-free, and limited to read-oriented tools in plan
mode. FORGE still starts no provider process; portable handoff and staged import remain manual.

Initialize an ordinary project repository with:

```console
forge init --owner-name "Repository Owner"
forge config validate
forge pack validate software-basic
forge create "Objective" --scope "Bounded scope" --trust-pack-data \
  --idempotency-key create-objective
forge status
forge migrate
forge pause --reason "Waiting for owner review"
forge resume
forge recover --reason "Rebuild derived state after an interrupted write"
forge recover-command <interrupted-key> --reason "Receipt write was interrupted" \
  --idempotency-key <distinct-recovery-key>
forge remediate-lock --reason "Confirmed the interrupted process exited" \
  --idempotency-key <stable-remediation-key>
forge agent context --target neutral
forge agent context --target codex
forge agent context --target codex --apply
forge agent doctor
forge agent doctor --adapter codex
forge agent doctor --adapter claude
forge handoff discover --constraint "Do not modify unrelated files"
forge abandon --reason "Stop this initiative" --unfinished-work "Remaining work" \
  --risk "Intended outcome was not delivered"
forge create "Successor objective" --scope "Fresh bounded scope" \
  --predecessor <archived-initiative-id> --trust-pack-data
forge artifact add requirements.md --role requirements --title "Requirements"
forge schema export --output schemas
```

## Development setup

Python 3.12 or newer is required.

```console
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"  # Windows
```

On macOS or Linux, use `.venv/bin/python` instead. Then run:

```console
ruff check .
pyright
pytest
python -m build
forge --help
```

## Governing documents

- [Constitution](docs/constitution.md)
- [Canonical glossary](docs/glossary.md)
- [Architecture decisions](docs/adr/README.md)
- [Dependency rationale](docs/dependencies.md)
- [Versioned contracts](docs/contracts.md)
- [Journal and materialized state](docs/persistence.md)
- [Packs, initiatives, and manual runs](docs/workflows.md)
- [Artifacts, claims, checks, and evidence](docs/artifacts-and-evidence.md)
- [Acceptance, decisions, and invalidation](docs/acceptance-and-invalidation.md)
- [Manual handoffs and safe result import](docs/handoffs-and-imports.md)
- [Atomic terminal decisions and archive inspection](docs/closure-and-archives.md)
- [Successor initiatives and explicit artifact reuse](docs/successors.md)
- [Idempotent mutation retries](docs/idempotency.md)
- [Explicit active-state recovery](docs/recovery.md)
- [Pause and long-gap resume](docs/continuity.md)
- [Hybrid Git collaboration policy](docs/git-policy.md)
- [Canonical neutral agent context](docs/agent-context.md)
- [Neutral agent adapters and manual fallback](docs/adapters.md)
- [Repository initialization](docs/user-guide/initialization.md)
- [M1 internal execution increments](docs/milestones/m1-execution-increments.md)
- [M1 evidence report](docs/milestones/m1-report.md)
- [M2 Increment 1 integrity boundary](docs/milestones/m2-increment-1.md)
- [M2 Increment 2 locking boundary](docs/milestones/m2-increment-2.md)
- [M2 Increment 3 idempotency boundary](docs/milestones/m2-increment-3.md)
- [M2 Increment 4 recovery boundary](docs/milestones/m2-increment-4.md)
- [M2 Increment 5 continuity boundary](docs/milestones/m2-increment-5.md)
- [M2 Increment 6 atomic closure boundary](docs/milestones/m2-increment-6.md)
- [M2 Increment 7 atomic abandonment boundary](docs/milestones/m2-increment-7.md)
- [M2 Increment 8 successor boundary](docs/milestones/m2-increment-8.md)
- [M2 Increment 9 archive-view boundary](docs/milestones/m2-increment-9.md)
- [M2 Increment 10 migration boundary](docs/milestones/m2-increment-10.md)
- [M2 Increment 11 Git-policy boundary](docs/milestones/m2-increment-11.md)
- [M2 Increment 12 truncated-journal recovery boundary](docs/milestones/m2-increment-12.md)
- [M2 Increment 13 interrupted-command recovery boundary](docs/milestones/m2-increment-13.md)
- [M2 Increment 14 stale-lock remediation boundary](docs/milestones/m2-increment-14.md)
- [M2 evidence report](docs/milestones/m2-report.md)
- [M3 Increment 1 canonical-context boundary](docs/milestones/m3-increment-1.md)
- [M3 Increment 2 managed-vendor-reference boundary](docs/milestones/m3-increment-2.md)
- [M3 Increment 3 neutral-adapter boundary](docs/milestones/m3-increment-3.md)
- [M3 Increment 4 Codex-adapter boundary](docs/milestones/m3-increment-4.md)
- [M3 Increment 5 Claude-adapter boundary](docs/milestones/m3-increment-5.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
