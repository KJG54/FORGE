# FORGE

**Framework for Orchestrated Reasoning, Governance, and Execution**

FORGE is a local-first governance framework for human-directed, AI-assisted work. It embeds a
versioned initiative in an ordinary repository and records how work is scoped, authorized,
claimed, checked, evidenced, accepted, paused, recovered, closed, or abandoned.

FORGE governs work. It is not the worker, an autonomous agent runtime, a hosted project manager,
or a same-user security sandbox.

> **Pre-alpha foundation:** The name, distribution name, public marks, contracts, and CLI remain
> provisional. Milestones 1 through 5 are complete and owner-accepted. Milestone 6 release-candidate
> hardening is in progress. This is not a public production release.

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

M3 Increment 6 adds explicit synchronous `forge agent run` execution for compatible Codex and
Claude installations. Each attempt has an adapter-attributed governed run, a disposable workspace
with only digest-verified inputs, bounded timeout and output capture, and a source-bound
`AgentResult` routed into the existing untrusted staging area. Returned files are never applied
automatically; import, run-attributed claim, checks, evidence, and owner acceptance remain separate.

M3 Increment 7 adds a default-disabled executable capability registry. Owners can inspect the exact
Codex or Claude executable profile, preview and persist scoped approval, revoke future execution,
and audit the approval bound to each adapter run. Pack-data trust remains separate and cannot
authorize a process.

M3 Increment 8 adds the owner-controlled lifecycle for the exact pack locked by an active
initiative. `forge pack untrust` and `forge pack trust` are preview-first, append immutable
decisions to journal-backed history, and never grant executable authority. Withdrawing data trust
blocks workflow-dependent mutation while preserving inspection, retrust, run cancellation, and
explicit abandonment.

M3 Increment 9 closes the implementation milestone with an end-to-end acceptance path proving that
manual handoff, Codex, and Claude share the same context, untrusted import, artifact, claim, and
lifecycle rules. It also records the built-in compatibility matrix, audits every M3 exit criterion,
and preserves the boundary that workers cannot approve gates or mutate governed lifecycle state
directly. The complete evidence and limitations are recorded in the
[M3 evidence report](docs/milestones/m3-report.md).

M4 Increment 1 adds strict tracked declarations for disabled-by-default local validators. Owners
can inspect and approve the exact resolved executable, ordered argument vector, working directory,
timeout, expected outputs, environment access, and side-effect risk. Validator declarations never
use shell strings, trusted-data packs cannot register or authorize them, and Increment 1 stopped
before any validator process, check result, evidence, or lifecycle transition was created.

M4 Increment 2 adds explicit supervised validator execution for a check required by a step awaiting
verification. Exact approval is bound and one-time authority is consumed before process creation;
the no-shell invocation receives a credential-denying allowlisted environment, declared timeout,
and bounded local output capture. Every pass, nonzero failure, timeout, overflow, or execution error
becomes an immutable artifact-revision-bound `CheckResult`. Execution never creates evidence,
verifies the step, or records owner acceptance.

M4 Increment 3 adds owner-only `forge scope amend`. It records a complete new effective scope,
validates affected requirements and artifacts against the locked initiative, derives downstream
staleness and gate effects, and returns work to an explicit workflow step. Affected active runs
must be cancelled first, and amended work must produce new claims, checks, evidence, verification,
and acceptance; the amendment waives none of them.

M4 Increment 4 adds owner-only `forge deviation record` and immutable decision-backed review.
Deviation recording is state-neutral and grants no waiver, override, risk acceptance, or
transition. A current `workflow-deviation-review` decision resolves the review requirement;
supersession or staleness reopens it. Open deviations remain visible in status and block successful
closure while explicit abandonment preserves unresolved history.

M4 Increment 5 adds owner-only `forge override record` for one exact locked-workflow requirement
or gate. The immutable record carries rationale, residual risk, temporary/permanent status, and a
review requirement while granting no progression authority. Overrides become explicit
successful-closure blockers;
abandonment preserves unresolved emergency history.

M4 Increment 6 adds owner-only `forge risk accept <override-id>`. The immutable acceptance binds
the exact override digest and its locked-workflow digest, resolving only that override's
residual-risk closure blocker. It never satisfies workflow progression. A scope amendment
affecting the target requirement or gate stales both records and requires fresh review.

M4 Increment 7 adds owner-only `forge risk revoke <acceptance-id>`. Revocation preserves the
original acceptance, reopens only its exact override's residual-risk closure blocker, and permits
a later fresh acceptance. It remains state-neutral and refuses already stale authority.

M4 Increment 8 adds owner-only `forge decision withdraw <decision-id>`. Withdrawal preserves the
original decision and records an exact digest-bound `decision-withdrawal` replacement through the
ordinary supersession mechanism. The prior decision stops being current without changing workflow
state; withdrawing a deviation review reopens that review requirement.

M4 Increment 9 hardens `forge run cancel <run-id>` with an immutable cancellation record binding
the exact run digest, locked cancellation policy, side-effect risk, actor, and workflow
destination. Manual runs remain cancellable because FORGE started no process. Adapter runs require
a prior hash-sealed terminal execution event, so cancellation cannot falsely claim that a live
cross-process worker stopped.

M4 Increment 10 adds structured local security and failure auditing. Handled CLI failures produce
sanitized immutable `LocalAuditEvent` files below `.forge/local/audit-events/` once the repository
can be safely identified. `forge audit list|show` and `forge doctor` inspect them. The files contain
a detail digest instead of raw error text and never become workflow or acceptance authority.

M4 Increment 11 closes the implementation milestone with a cumulative adversarial acceptance
suite covering false completion, executable-trust separation, revoked and superseded authority,
malicious packs, hostile imports, command injection, path escape, forged claims, and the
same-user-process threat boundary. The audit also strengthens newly recorded claims by binding
their complete canonical digest into the hash-sealed journal event. The complete evidence and
limitations are recorded in the [M4 evidence report](docs/milestones/m4-report.md). The repository
owner formally accepted M4 on 2026-07-27.

M5 Increment 1 adds the bundled, data-only `research-basic` pack. Its seven declarative steps cover
question framing, planning, evidence collection, synthesis, structural verification, review, and
closure through the unchanged core lifecycle. Research sources, citations, claims, checks,
evidence, and process outcomes remain distinct from factual truth and configured-owner acceptance.

M5 Increment 2 adds exact research evidence-register and citation-record templates. Template bytes
are UTF-8, inventory-checked, individually digested, included in the complete pack digest, and
copied into governed active state before initiative creation commits. Restart and archives validate
the locked copies without consulting a later installed pack. `forge pack template list|show`
provides read-only access; templates never execute, create artifacts or evidence, or establish
factual truth. Shared pack conformance, new explanation profiles, long-gap resumption changes, and
filesystem discovery remain later M5 boundaries.

M5 Increment 3 adds strict data-only structural validators for the research evidence register and
citation record. Their safe-YAML definitions are digest-bound, locked pack resources with no
executable, argument, environment, hook, expression, or network field. `forge check structure`
evaluates bounded UTF-8 headings and non-empty field prefixes in-process against exact current
artifact revisions and records only a `CheckResult`. A pass does not create evidence, verify a
step, grant acceptance, or establish semantic or factual truth. Shared pack conformance,
explanation profiles, resumption, and discovery remain later boundaries.

M5 Increment 4 enables Minimal and Mentored presentation alongside Standard and Guided for both
bundled packs. The selected inline explanation is exact digest-bound workflow data locked at
initiative creation. Minimal removes teaching detail, while Mentored adds rationale; neither
changes permissions, transitions, gates, checks, evidence, verification, acceptance, or next
actions. Older two-profile packs remain valid for profiles they contain. Both bundled packs are
now `0.4.0`; shared conformance, long-gap resumption, and discovery remain later boundaries.

M5 Increment 5 upgrades long-gap continuity with one canonical resumption summary derived from the
validated effective scope, workflow position, step states, open decisions, current artifact
revision references, non-stale evidence, and preserved legal actions. Paused `forge status` shows
the summary before mutation; `forge resume` hash-binds the same text and referenced records into
the resume event. It embeds no artifact content, grants no authority, and performs no unrelated
filesystem discovery. Bounded discovery and shared conformance remain later boundaries.

M5 Increment 6 adds read-only bounded filesystem context discovery. `forge agent discover`
inventories only path metadata under hard limits, never follows symbolic links, excludes hidden,
FORGE, configured-secret, unsupported, oversized, and Git-ignored paths, and withholds
unregistered suggestions if ignore enforcement is unavailable. Filename-only lexical ranking and
current required-input coverage produce an advisory structural sufficiency result; unregistered
candidate content is never read and no content is registered, authorized, returned, or added to
canonical context. Measured software and research
scenarios keep SQLite FTS deferred. Shared conformance and cumulative M5 closeout remain later
boundaries.

M5 Increment 7 adds one shared conformance contract for both bundled packs and closes the
implementation evidence against all five M5 roadmap exit criteria. It proves shared lifecycle and
authority structure, domain-neutral public contract fields, identical four-profile governance,
canonical long-gap resumption, and creation of a repository-local declarative pack containing no
Python code. Increment 7 adds no runtime feature, schema, pack byte, or authority. M5 is now
owner-accepted; the exact Increment 7 implementation and evidence commits passed Windows, macOS,
and Ubuntu closeout CI. The complete accepted evidence is recorded in the
[M5 evidence report](docs/milestones/m5-report.md).

M6 Increment 1 freezes the exact pre-v1 compatibility inventory. All accepted persisted contracts
use schema version `1.0`; the accepted public registry grew from 37 M1 models to 51 M5 models
without removing an earlier public model. Synthetic fixtures exercise compatibility-critical
additive defaults, future-version refusal, the complete legacy M1 unhashed journal, the current M2
hash chain, and the exact registered migration between those storage formats. No tagged or
publicly distributed pre-v1 release exists, and arbitrary intermediate commits are not claimed as
supported migration sources. See the [pre-v1 compatibility policy](docs/compatibility.md).

M6 Increment 2 defines the 18-cell release-candidate installation matrix: CPython 3.12–3.14 on
Windows, macOS, and Linux through ordinary virtual environments and `pipx`. A repository-local,
shell-free harness installs one exact wheel outside the source tree and verifies the installed
console script, version, help, initialization, configuration, both bundled packs, repository
health, and all 51 schemas. Local evidence does not establish unexecuted matrix cells, and CI
execution remains deferred until M6 closeout. See the
[installation guide](docs/installation.md).

M6 Increment 3 adds uninitialized software and synthetic research example repositories. Each
contains all artifacts required by its bundled workflow but no FORGE state, owner identity,
decision, check, evidence, acceptance, credential, or executable content. A release-test harness
copies the examples into temporary directories and completes both workflows through an exact
installed `forge` executable; synthetic rehearsal acceptance cannot apply to real work. See the
[example repositories](examples/README.md).

M6 Increment 4 completes the repository-local documentation routes for users, pack authors,
adapter contributors, architecture and security reviewers, troubleshooting, and recovery. The
[documentation index](docs/README.md) connects task-oriented guides to the existing canonical
feature references without creating new commands, contracts, authority, compatibility promises,
or release claims.

M6 Increment 5 adds a reproducible dependency, license, vulnerability, and secret-review boundary.
It inventories installed build/runtime/development closures, validates explicit license policy,
audits exact installed runtime versions, and scans full Git history plus a bounded current snapshot
with redaction. The only secret exception is one exact historical synthetic-test fingerprint. See
the [supply-chain and secret review](docs/supply-chain-security-review.md).

M6 Increment 6 defines maintained p95 budgets for cold startup, active status, 1,000-event journal
replay, canonical context generation, and archive access. A shell-free harness measures exact CLI
paths plus isolated replay against temporary workloads containing five validated archives and 25
open decisions. Local timing proves only the observed environment; clean-wheel cross-platform
repetition remains closeout evidence. See the [performance budget guide](docs/performance.md).

Initialize an ordinary project repository with:

```console
forge init --owner-name "Repository Owner"
forge config validate
forge pack validate software-basic
forge pack validate research-basic
forge pack template list research-basic
forge pack template show research-basic templates/research-citation-record.md
forge pack validator list research-basic
forge pack validator show research-basic research-evidence-register-structure
forge create "Objective" --scope "Bounded scope" --trust-pack-data \
  --idempotency-key create-objective
forge pack inspect software-basic
forge pack untrust software-basic --rationale "Re-evaluate this locked data" --apply
forge pack trust software-basic --rationale "Exact locked digest reviewed" --apply
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
forge agent discover
forge agent context --target codex
forge agent context --target codex --apply
forge agent doctor
forge agent doctor --adapter codex
forge agent doctor --adapter claude
forge agent run discover --adapter codex --timeout 300
forge check run discover outputs-present --validator validator.project.tests
forge check list
forge scope amend --scope "Revised bounded scope" --rationale "Requirement changed" \
  --return-to discover --requirement requirements
forge scope show
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
- [Pre-v1 compatibility policy and inventory](docs/compatibility.md)
- [Installation and supported environments](docs/installation.md)
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
- [Trusted local validator declarations](docs/validators.md)
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
- [M3 Increment 6 governed adapter-execution boundary](docs/milestones/m3-increment-6.md)
- [M3 Increment 7 executable-capability boundary](docs/milestones/m3-increment-7.md)
- [M3 Increment 8 pack-data-trust lifecycle](docs/milestones/m3-increment-8.md)
- [M3 Increment 9 replaceable-worker acceptance](docs/milestones/m3-increment-9.md)
- [M3 evidence report](docs/milestones/m3-report.md)
- [M4 Increment 1 declarative-validator boundary](docs/milestones/m4-increment-1.md)
- [M4 Increment 2 supervised-validator boundary](docs/milestones/m4-increment-2.md)
- [M4 Increment 3 scope-amendment boundary](docs/milestones/m4-increment-3.md)
- [M4 Increment 4 workflow-deviation boundary](docs/milestones/m4-increment-4.md)
- [M4 Increment 5 emergency-override boundary](docs/milestones/m4-increment-5.md)
- [M4 Increment 6 exact risk-acceptance boundary](docs/milestones/m4-increment-6.md)
- [M4 Increment 7 risk-acceptance-revocation boundary](docs/milestones/m4-increment-7.md)
- [M4 Increment 8 decision-withdrawal boundary](docs/milestones/m4-increment-8.md)
- [M4 Increment 9 formal-cancellation boundary](docs/milestones/m4-increment-9.md)
- [M4 Increment 10 structured-local-audit boundary](docs/milestones/m4-increment-10.md)
- [M4 Increment 11 adversarial closeout](docs/milestones/m4-increment-11.md)
- [M4 evidence report](docs/milestones/m4-report.md)
- [M5 Increment 1 declarative-research boundary](docs/milestones/m5-increment-1.md)
- [M5 Increment 2 digest-bound-template boundary](docs/milestones/m5-increment-2.md)
- [M5 Increment 3 structural-validator boundary](docs/milestones/m5-increment-3.md)
- [M5 Increment 4 four-profile presentation boundary](docs/milestones/m5-increment-4.md)
- [M5 Increment 5 canonical-resumption boundary](docs/milestones/m5-increment-5.md)
- [M5 Increment 6 bounded-filesystem-discovery boundary](docs/milestones/m5-increment-6.md)
- [M5 Increment 7 shared-conformance closeout](docs/milestones/m5-increment-7.md)
- [M5 evidence report](docs/milestones/m5-report.md)
- [M6 Increment 1 pre-v1 compatibility boundary](docs/milestones/m6-increment-1.md)
- [M6 Increment 2 built-distribution installation boundary](docs/milestones/m6-increment-2.md)
- [M6 Increment 3 example-repository boundary](docs/milestones/m6-increment-3.md)
- [M6 Increment 4 complete-documentation boundary](docs/milestones/m6-increment-4.md)
- [M6 Increment 5 supply-chain and secret-review boundary](docs/milestones/m6-increment-5.md)
- [M6 Increment 6 maintained-performance boundary](docs/milestones/m6-increment-6.md)
- [Documentation index](docs/README.md)
- [Software and research example repositories](examples/README.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
