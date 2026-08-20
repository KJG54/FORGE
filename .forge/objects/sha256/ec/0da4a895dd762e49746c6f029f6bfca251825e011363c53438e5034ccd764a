# FORGE Production v1 — Master Implementation Specification and Agent Handoff

> **FORGE:** Framework for Orchestrated Reasoning, Governance, and Execution  
> **Document type:** Authoritative implementation specification and planning handoff  
> **Status:** Approved for implementation planning; not yet approved for code implementation  
> **Target release:** Production v1.0.0  
> **License:** Apache-2.0  
> **Primary platforms:** Windows, macOS, and Linux  
> **Primary implementation language:** Python 3.12+  
> **Authority:** Project owner  
> **Supersedes:** Earlier FORGE roadmaps and the original Milestone 1 handoff wherever they conflict with this document

---

# 0. Instructions to the Receiving Agent

This document is the authoritative assignment for planning and eventually building FORGE Production v1.

## 0.1 Your immediate assignment

Do **not** begin implementation after receiving this document.

Your first task is to:

1. Read this specification completely.
2. Inspect the target repository if one already exists.
3. Identify conflicts between this specification and the repository’s current state.
4. Produce a milestone-by-milestone implementation plan using the required planning format in Section 30.
5. Identify only genuine blocking ambiguities, contradictions, or feasibility risks.
6. Propose bounded technical choices where this document intentionally leaves implementation freedom.
7. Stop and return the plan to the owner for review.

Do not create production code, restructure the repository, install dependencies, generate commits, or begin Milestone 0 until the owner explicitly approves the implementation plan.

## 0.2 Implementation behavior after planning approval

After the owner approves the implementation plan:

- Implement **one milestone at a time**.
- Satisfy every deliverable and exit criterion for that milestone.
- Produce the required milestone report and evidence packet.
- Stop for owner review.
- Do not begin the next milestone until the owner explicitly approves progression.

A milestone is not approved merely because its tests pass. Automated checks, implementation claims, evidence, and owner acceptance remain separate.

## 0.3 Interpretation hierarchy

When instructions conflict, use this order:

1. The owner’s most recent explicit decision.
2. This master specification.
3. Accepted FORGE ADRs that do not conflict with this specification.
4. Approved milestone-specific implementation briefs.
5. Repository conventions and existing code.
6. Your own implementation preference.

Do not silently reconcile conflicts. Record them and request an owner decision in the planning report.

## 0.4 Required implementation posture

You are implementing a governance framework, not an autonomous builder.

Do not:

- turn FORGE into an agent runtime,
- allow an agent to approve owner gates,
- hard-code a universal software lifecycle into the core,
- use chat history as authoritative state,
- hide important state in a database,
- add hosted infrastructure,
- introduce multi-agent coordination,
- add a web or desktop interface,
- copy ESDF wholesale,
- expand scope because a future feature appears useful.

Build the smallest complete system that satisfies each approved milestone.

---

# 1. Product Mission

FORGE is a local-first governance framework for human-directed, AI-assisted work.

It embeds a versioned initiative inside an ordinary project repository and governs how work is:

- proposed,
- scoped,
- authorized,
- assigned,
- performed,
- claimed,
- checked,
- evidenced,
- accepted,
- recorded,
- paused,
- resumed,
- changed,
- abandoned,
- archived,
- recovered.

FORGE itself does not perform project work. Humans, agents, scripts, validators, and external tools are replaceable workers operating under FORGE governance.

The framework’s central purpose is to preserve intent, authority, evidence, and continuity across tools and time. A user must be able to stop using one agent, lose a chat session, return after a long gap, or change tools without losing the governed state of the initiative.

## 1.1 Product identity

FORGE is:

- a governance framework,
- a repository-embedded operating contract,
- a workflow and evidence engine,
- a durable human–AI collaboration record,
- a domain-neutral core extended through declarative packs,
- a local CLI and inspectable filesystem format.

FORGE is not:

- a code generator,
- a chatbot,
- an autonomous agent swarm,
- a project-management dashboard,
- a hosted collaboration platform,
- a universal monolithic workflow,
- a security sandbox against the repository owner’s own operating-system account.

## 1.2 Production-v1 user

Production v1 targets one repository owner working with:

- human contributors,
- Codex,
- Claude Code,
- manually invoked scripts,
- local validators,
- other replaceable tools through file handoffs.

V1 does not implement adversarial multi-user authentication or distributed concurrency.

---

# 2. Non-Negotiable Principles

These principles constrain every milestone and design decision.

## 2.1 Human authority

The owner retains exclusive authority over consequential governance actions, including:

- accepting the initiative objective,
- approving scope,
- approving plans where the workflow requires it,
- approving executable capabilities,
- accepting material scope changes,
- recording risk acceptance,
- issuing emergency overrides,
- accepting verified outcomes,
- closing or abandoning an initiative,
- approving release progression.

Agents and contributors may recommend these decisions but may not record them as owner-approved.

## 2.2 Claims are not completion

FORGE must preserve the sequence:

```text
claim → check → evidence → owner acceptance
```

A worker claim is an assertion. A check is a structured evaluation. Evidence is the durable support for the check. Acceptance is the owner’s decision to authorize progression or closure.

No adapter result, message, exit code, or generated file may collapse these stages into one.

## 2.3 Files are inspectable authority

Authoritative content must remain available through ordinary files.

FORGE may create derived caches and indexes, but a user must be able to inspect the initiative without proprietary infrastructure or prior chat history.

## 2.4 Local-first operation

Core lifecycle operations must work without:

- a hosted API,
- a remote database,
- cloud storage,
- a model-provider API,
- a network connection.

Optional adapters may depend on separately installed user tools, but their absence must not prevent manual FORGE use.

## 2.5 Model and worker independence

Core services must not depend on OpenAI, Anthropic, Google, Ollama, or any other provider.

Codex and Claude Code are optional workers accessed through adapters. Manual file handoff remains a supported baseline.

## 2.6 Domain-neutral core

The core must not require software-specific concepts such as:

- programming language,
- source tree,
- build command,
- test suite,
- deployment target,
- package manager.

Those belong in domain packs and capabilities.

## 2.7 Explicit state and recovery

At any time, FORGE must be able to explain:

- which initiative is active,
- the initiative’s lifecycle and integrity states,
- the current workflow and locked versions,
- step states,
- open decisions,
- unresolved gates,
- registered artifacts and revisions,
- checks and evidence,
- stale approvals or acceptance,
- active and historical runs,
- next permitted actions,
- blockers and remediation guidance.

## 2.8 Immutable governance history

Decisions, approvals, checks, evidence, overrides, and acceptance records are append-only governance facts.

Corrections occur through supersession, revocation, amendment, or a new revision. They are never silently edited in place.

## 2.9 Progressive complexity

Do not pre-build future infrastructure. Every dependency, abstraction, or extension mechanism must support an approved milestone requirement.

## 2.10 Education is a view, not authority

Explanation profiles may change wording, detail, examples, and teaching support. They may not change:

- permissions,
- required evidence,
- lifecycle transitions,
- gates,
- acceptance requirements.

## 2.11 Tamper evidence is not same-user isolation

FORGE detects and reports unauthorized or accidental changes to governed records. It does not claim to protect against a malicious process running with the repository owner’s filesystem permissions.

External isolation, operating-system permissions, containers, and multi-user authentication are outside v1.

---

# 3. V1 Scope and Non-Goals

## 3.1 Included in Production v1

Production v1 includes:

- one active initiative per repository,
- any number of immutable archived initiatives,
- successor initiatives with provenance links,
- repository-embedded filesystem persistence,
- Python CLI lifecycle management,
- versioned Pydantic contracts and JSON Schemas,
- append-only event history,
- materialized state and explicit recovery,
- artifact and evidence registration,
- immutable artifact revisions,
- content digests and stale dependency propagation,
- decisions, gates, supersession, revocation, amendments, deviations, overrides, and risk acceptance,
- owner acceptance,
- safe file handoffs and result imports,
- declarative domain packs,
- separate executable capability trust,
- manual worker flows,
- optional Codex and Claude Code CLI adapters,
- software-basic and research-basic packs,
- Standard, Guided, Minimal, and Mentored explanation profiles,
- Windows, macOS, and Linux support,
- public Apache-2.0 release.

## 3.2 Deferred beyond v1

Do not implement in v1:

- web UI,
- desktop UI,
- mobile application,
- hosted accounts,
- cloud synchronization,
- remote pack registry or marketplace,
- automatic plugin installation,
- direct model-provider API integration,
- vector database,
- semantic retrieval engine,
- distributed workflow engine,
- multi-agent coordinator,
- message broker,
- multi-user authentication,
- adversarial authorization boundary,
- remote execution service,
- automatic container isolation,
- ESDF importer,
- shared real-time collaboration.

OpenTelemetry, SQLite full-text search, artifact signing, release signing, container isolation, and semantic retrieval may be investigated only after the core roadmap succeeds and the owner approves evidence-based adoption.

---

# 4. Core User Journeys

The implementation must support these end-to-end journeys.

## 4.1 Initialize an existing repository

A user enters an ordinary repository and runs `forge init`.

FORGE:

1. Confirms the directory is suitable.
2. Creates `forge.yaml` without overwriting unrelated configuration.
3. Creates the `.forge/` structure.
4. Creates or records the owner identity.
5. Generates compatible `.gitignore` additions without destroying existing rules.
6. Validates bundled packs.
7. Leaves the repository initialized but without an active initiative.

## 4.2 Create and complete a software initiative manually

The user:

1. Creates an initiative using `software-basic`.
2. Reviews the generated objective and workflow lock.
3. Progresses through Discover, Plan, Execute, Verify, Review, and Close.
4. Registers project files and governance artifacts.
5. Creates a manual handoff for an external worker.
6. Imports the worker result through safe staging.
7. Records claims and checks.
8. Reviews evidence.
9. Records owner acceptance.
10. Closes the initiative.
11. Inspects the immutable archive.

## 4.3 Interrupt and resume

The user may stop FORGE or the terminal at any point.

On return:

1. `forge status` validates integrity.
2. The materialized state matches the journal head or reports an integrity error.
3. `forge next` provides the next legal actions and blockers.
4. Generated context explains enough to continue without chat history.

## 4.4 Detect modified accepted work

After acceptance, a governed project artifact changes.

FORGE:

1. Detects the digest mismatch.
2. Registers or requires an explicit new revision.
3. Marks dependent checks, evidence, gates, and acceptance stale.
4. Prevents closure or progression where stale records are disallowed.
5. Requires re-checking and reacceptance.

## 4.5 Abandon work without pretending success

The owner abandons an initiative.

FORGE:

1. Requires a reason.
2. Captures unfinished work and unresolved risks.
3. Records final owner authorization.
4. Preserves the entire governed record.
5. Archives the initiative as `abandoned`, never `closed`.
6. Allows a successor initiative to reference it.

## 4.6 Use an optional agent adapter

The user invokes Codex or Claude Code through FORGE.

FORGE:

1. Verifies adapter availability and compatibility.
2. Generates bounded neutral context.
3. Invokes the separately installed CLI.
4. Captures run metadata and exit state.
5. Treats all returned files and claims as untrusted.
6. Routes outputs through the same import pipeline used for manual handoffs.
7. Requires checks, evidence, and owner acceptance normally.

## 4.7 Complete a research initiative

The user chooses `research-basic`.

The same core governs:

- question framing,
- research planning,
- evidence collection,
- synthesis,
- structural verification,
- review,
- acceptance,
- closure.

No software-only fields may be required by the core.

---

# 5. Repository Models

FORGE has two distinct repository models:

1. The **FORGE source repository**, containing the framework implementation.
2. A **FORGE-enabled project repository**, containing an initialized initiative.

Do not confuse these structures.

## 5.1 Target FORGE source repository

Use the following structure unless the approved implementation plan documents a justified refinement:

```text
forge/
├── README.md
├── LICENSE
├── NOTICE
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── pyproject.toml
├── hatch.toml                     # only if separate configuration is justified
├── src/
│   └── forge/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli/
│       │   ├── app.py
│       │   ├── rendering.py
│       │   └── commands/
│       ├── contracts/
│       │   ├── base.py
│       │   ├── actors.py
│       │   ├── initiatives.py
│       │   ├── workflows.py
│       │   ├── artifacts.py
│       │   ├── decisions.py
│       │   ├── runs.py
│       │   ├── verification.py
│       │   ├── packs.py
│       │   ├── capabilities.py
│       │   ├── agents.py
│       │   ├── events.py
│       │   └── state.py
│       ├── core/
│       │   ├── errors.py
│       │   ├── authorization.py
│       │   ├── transitions.py
│       │   ├── lifecycle.py
│       │   ├── artifacts.py
│       │   ├── evidence.py
│       │   ├── acceptance.py
│       │   ├── decisions.py
│       │   ├── verification.py
│       │   ├── recovery.py
│       │   ├── archival.py
│       │   ├── context.py
│       │   └── status.py
│       ├── storage/
│       │   ├── interfaces.py
│       │   ├── filesystem.py
│       │   ├── atomic.py
│       │   ├── journal.py
│       │   ├── snapshots.py
│       │   ├── locking.py
│       │   ├── digests.py
│       │   └── migrations.py
│       ├── packs/
│       │   ├── loader.py
│       │   ├── validation.py
│       │   ├── trust.py
│       │   └── bundled/
│       │       ├── software-basic/
│       │       └── research-basic/
│       ├── capabilities/
│       │   ├── registry.py
│       │   ├── trust.py
│       │   └── validators.py
│       ├── agents/
│       │   ├── interface.py
│       │   ├── context.py
│       │   ├── manual.py
│       │   ├── codex.py
│       │   └── claude.py
│       ├── security/
│       │   ├── paths.py
│       │   ├── imports.py
│       │   ├── secrets.py
│       │   └── limits.py
│       └── schemas/
│           └── export.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── acceptance/
│   ├── security/
│   ├── recovery/
│   ├── cross_platform/
│   ├── fixtures/
│   └── golden/
├── docs/
│   ├── constitution.md
│   ├── glossary.md
│   ├── architecture/
│   ├── adr/
│   ├── user-guide/
│   ├── pack-author-guide/
│   ├── adapter-author-guide/
│   ├── security/
│   ├── recovery/
│   └── compatibility/
├── examples/
│   ├── software/
│   └── research/
├── scripts/
│   ├── export-schemas.py
│   ├── smoke-install.py
│   └── release-check.py
└── .github/
    ├── workflows/
    └── ISSUE_TEMPLATE/
```

Rules:

- Business rules belong in `core/`, not CLI command functions.
- Pydantic contracts contain validation and data shape, not lifecycle orchestration.
- Filesystem code belongs in `storage/` and `security/`.
- Vendor adapter code remains isolated from core services.
- Bundled packs must pass the same validation path as third-party local packs.
- Do not create empty abstraction layers that are not used by the current milestone.

## 5.2 FORGE-enabled project repository

```text
project/
├── forge.yaml
├── AGENTS.md                      # optional managed reference block
├── CLAUDE.md                      # optional managed reference block
├── .gitignore
├── .forge/
│   ├── active/
│   │   ├── initiative.json
│   │   ├── state.json
│   │   ├── events.jsonl
│   │   ├── workflow.lock.json
│   │   ├── decisions/
│   │   ├── artifacts/
│   │   ├── evidence/
│   │   └── context/
│   ├── archive/
│   │   └── <initiative-id>/
│   ├── objects/
│   │   └── sha256/
│   └── local/
│       ├── locks/
│       ├── import-staging/
│       ├── runs/
│       ├── cache/
│       └── secrets/
└── project source and documents
```

### Tracked by default

- `forge.yaml`
- `.forge/active/` governed records
- `.forge/archive/` records
- `.forge/objects/` preserved accepted revisions
- non-secret generated canonical context
- managed vendor references if the owner accepts them

### Ignored by default

- `.forge/local/`
- execution locks
- caches
- verbose logs
- temporary handoffs
- raw adapter process output unless promoted into evidence
- credentials
- environment snapshots
- derived indexes

---

# 6. Archival Preservation Model

An archive must preserve what the owner actually accepted. A path and digest alone are insufficient if the referenced project file later changes or disappears.

## 6.1 Content-addressed object store

Production v1 will use an immutable content-addressed store:

```text
.forge/objects/sha256/<first-two>/<remaining-digest>
```

When an artifact or evidence revision becomes approval-bound, acceptance-bound, closure-critical, or explicitly marked for preservation, FORGE copies the exact file bytes into the object store and verifies the digest.

`ArtifactRevision` records:

- repository-relative working path,
- revision number,
- SHA-256 digest,
- preserved-object path,
- byte size,
- media type,
- provenance,
- registration event,
- preservation status.

## 6.2 Preservation rules

- Governance-native records are already preserved under `.forge/`.
- Every artifact revision referenced by a current approval, check, evidence packet, acceptance, closure, or abandonment record must be preserved.
- Archived initiatives reference preserved objects, not mutable working-tree paths alone.
- Content-addressed objects are immutable and deduplicated.
- Garbage collection is not part of normal v1 operation. An object may be removed only by a future explicit maintenance command that proves no governed record references it.
- V1 may enforce a documented maximum preserved-object size. Oversized closure-critical artifacts must fail registration with guidance rather than silently becoming non-reproducible.
- Large artifact backends are post-v1.

## 6.3 Archive contents

`archive/<initiative-id>/` contains:

- initiative identity,
- terminal state,
- complete validated event journal,
- final materialized snapshot,
- locked workflow and pack manifests,
- decisions and amendments,
- artifact and evidence manifests,
- acceptance or abandonment record,
- final review and lessons artifacts,
- references to preserved content-addressed objects,
- archive manifest and archive digest.

Archived initiatives are immutable through supported commands.

---

# 7. Source-of-Truth and Persistence Model

## 7.1 Authority hierarchy

Use this hierarchy:

1. Artifact and evidence file contents are authoritative for their current bytes.
2. Preserved object-store copies are authoritative for exact accepted historical revisions.
3. Content digests bind governance records to exact revisions.
4. The validated event journal is authoritative for lifecycle history and ordering.
5. The locked workflow and pack versions define applicable rules.
6. `state.json` is a reconstructable materialized view.
7. Summaries, indexes, handoffs, and vendor-specific context are disposable derived views.

## 7.2 Event journal

`events.jsonl` contains concise, append-only governance events.

Each event includes at minimum:

- event schema version,
- event ID,
- initiative ID,
- monotonic sequence number,
- UTC timestamp,
- event type,
- actor reference,
- correlation or run ID where applicable,
- authorization basis,
- affected record IDs,
- affected digests,
- previous event hash after M2,
- event hash after M2,
- concise metadata.

Large content belongs in dedicated files. Events contain references and digests, not duplicated documents.

Meaningful events include:

- initiative creation,
- workflow lock,
- step transitions,
- artifact registration and revision,
- evidence registration,
- claim recording,
- check attempt and result,
- decision recording,
- decision supersession,
- approval or acceptance revocation,
- scope amendment,
- workflow deviation,
- override and risk acceptance,
- pause and resume,
- run creation, completion, failure, or cancellation,
- pack trust changes,
- capability trust changes,
- integrity mismatch detection,
- recovery,
- migration,
- closure,
- abandonment,
- archival.

## 7.3 Materialized state

`state.json` contains current derived state for fast reads.

It includes:

- initiative lifecycle state,
- integrity state,
- current workflow position,
- step states,
- current artifact revisions,
- stale dependencies,
- open gates and decisions,
- active runs,
- permitted next actions,
- journal head sequence and hash,
- snapshot schema version.

The snapshot never overrides valid history.

If state and journal disagree:

1. mark integrity as `integrity_error`,
2. report the mismatch,
3. reject unsafe mutating operations,
4. require explicit `forge recover`,
5. reconstruct from the last valid journal chain,
6. write a new snapshot atomically,
7. record a recovery event.

## 7.4 Atomic writes

Every governed file mutation must use:

1. write to a temporary file in the same filesystem,
2. flush and synchronize where practical,
3. validate the temporary content,
4. atomically replace the destination,
5. verify resulting content,
6. append or coordinate the corresponding event consistently.

The implementation plan must define the exact transaction pattern used to prevent an event from claiming a state change whose durable files were not written, or vice versa.

## 7.5 Locking and idempotency

Mutating commands require a cross-process repository lock under `.forge/local/locks/`.

Each mutation accepts or generates an idempotency key. Retrying the same command after interruption must not duplicate a transition or record.

Lock handling must include:

- owner process metadata,
- creation timestamp,
- stale-lock detection,
- safe refusal when another live process holds the lock,
- explicit diagnostic remediation,
- no silent lock deletion.

---

# 8. Canonical State Machines

Lifecycle, integrity, step, and run status are separate fields.

## 8.1 Repository state

```text
uninitialized
initialized
```

## 8.2 Initiative lifecycle state

```text
active
paused
closing
closed
abandoned
```

Rules:

- Only `active` initiatives permit normal work transitions.
- `paused` initiatives permit inspection and resume but reject normal work mutations.
- `closing` permits final review, required checks, acceptance, and closure preparation.
- `closed` and `abandoned` are terminal archived states.
- Archived initiatives cannot reopen.
- Continued work requires a successor initiative.

## 8.3 Integrity state

```text
healthy
recovering
integrity_error
```

Integrity state constrains allowed commands independently from lifecycle state.

## 8.4 Step state

```text
pending
ready
in_progress
blocked
awaiting_verification
awaiting_acceptance
completed
invalidated
skipped
```

Core invariants:

- `pending` means prerequisites are not yet satisfied.
- `ready` means work may begin.
- `in_progress` means an authorized run or manual effort has started.
- `blocked` requires explicit remediation or owner review.
- `awaiting_verification` means declared work output exists but checks are incomplete.
- `awaiting_acceptance` means required checks and evidence are complete but owner acceptance is missing.
- `completed` means the step’s declared requirements are satisfied.
- `invalidated` means prior completion no longer authorizes progression due to changed scope, artifact revision, revocation, or workflow rule.
- `skipped` requires workflow permission and an authorized reason.

## 8.5 Run state

```text
created
running
succeeded
failed
cancelled
```

Run success records process completion, not step acceptance.

## 8.6 Cancellation

- Cancelling a run never completes or accepts a step.
- Partial outputs remain untrusted until imported.
- A canceled run is terminal.
- Side-effect-free runs may return the step to `ready`.
- Runs with declared external or irreversible side effects move the step to `blocked` for owner review.
- A workflow may impose stricter rules but may never treat cancellation as success.

---

# 9. Canonical Contracts

All persisted contracts:

- use explicit schema versions,
- reject unknown incompatible versions,
- use stable identifiers,
- serialize deterministically where hashing applies,
- support JSON Schema export,
- avoid provider-specific fields in the core.

## 9.1 Identity and authority

### `OwnerIdentity`

Contains:

- owner UUID,
- display name,
- creation timestamp,
- optional local metadata that does not claim authentication.

### `Actor`

Contains:

- actor ID,
- actor type,
- display label,
- tool or adapter reference where applicable.

### `ActorType`

At minimum:

- `owner`
- `human_contributor`
- `forge_cli`
- `agent_adapter`
- `external_tool`
- `unknown_external_process`
- `migration`
- `recovery`

### `AuthorityGrant`

Defines:

- actor,
- allowed action class,
- scope,
- granting owner decision,
- validity period or version scope,
- revocation reference.

The owner record is governance identity, not cryptographic authentication.

## 9.2 Initiative contracts

### `Initiative`

Contains:

- immutable initiative ID,
- objective,
- selected pack and version,
- selected workflow and version,
- owner identity reference,
- creation event,
- lifecycle state,
- predecessor references,
- explanation profile,
- declared scope summary.

### `InitiativeReference`

Used to link successor work to archived predecessors without inheriting approval.

## 9.3 Workflow contracts

### `WorkflowDefinition`

Contains:

- workflow ID and semantic version,
- pack identity,
- human-readable name and description,
- step definitions,
- transition definitions,
- required gates,
- required artifact/evidence classes,
- explanation content,
- compatibility constraints.

### `StepDefinition`

Contains:

- step ID,
- purpose,
- instructions,
- prerequisites,
- required inputs,
- required outputs,
- claim requirements,
- check requirements,
- acceptance requirements,
- allowed actors,
- allowed transitions,
- cancellation behavior,
- context-selection rules.

### `TransitionDefinition`

Contains:

- source state,
- destination state,
- conditions,
- authority requirement,
- invalidation effects,
- event type.

The M1 engine may execute a linear workflow, but the contract must not prevent future branches.

## 9.4 Artifacts and evidence

### `ArtifactRecord`

Logical artifact identity and role.

### `ArtifactRevision`

Contains:

- artifact ID,
- revision number,
- normalized repository-relative path,
- content digest,
- byte size,
- media type,
- provenance,
- registration event,
- preserved-object reference if required,
- superseded revision reference,
- stale dependency effects.

### `EvidencePacket`

Contains:

- evidence ID,
- purpose,
- artifact revision references,
- check result references,
- worker claims where relevant,
- limitations,
- creation actor,
- digest-bound contents.

Evidence does not automatically establish truth. It documents support for a governance decision.

## 9.5 Decisions and governance changes

### `DecisionRecord`

Contains:

- decision ID,
- decision type,
- question or issue,
- considered options,
- chosen outcome,
- rationale,
- actor and authority basis,
- affected records,
- bound digests,
- status.

### `DecisionSupersession`

References the prior decision and explains why a new decision replaces it.

### `ApprovalRevocation`

Preserves the original approval and records when and why it stopped authorizing progression.

### `ScopeAmendment`

Identifies:

- changed scope,
- rationale,
- affected requirements,
- affected artifacts,
- invalidated checks,
- invalidated gates and acceptance,
- return point in the workflow.

### `WorkflowDeviation`

Records approved divergence from the declared workflow without hiding it.

### `EmergencyOverride`

Requires:

- owner authority,
- written rationale,
- affected gate or requirement,
- residual risk,
- temporary or permanent status,
- review requirement.

### `RiskAcceptance`

Records a known unresolved risk accepted by the owner. It does not rewrite failed checks as passed.

## 9.6 Claims, checks, and acceptance

### `Claim`

A worker assertion about work performed or output produced.

### `CheckResult`

Contains:

- check identity and version,
- target artifact revisions,
- capability used,
- exact invocation metadata,
- start and end time,
- exit status,
- normalized outcome,
- captured evidence references,
- limitations,
- result digest.

### `AcceptanceRecord`

Contains:

- owner actor,
- accepted artifact revisions,
- accepted evidence and checks,
- accepted scope,
- known limitations,
- residual risks,
- acceptance timestamp and event,
- revocation reference if later revoked while active or closing.

## 9.7 Runs and handoffs

### `RunRecord`

Contains:

- run ID,
- step ID,
- worker or adapter,
- capability references,
- declared side-effect class,
- status,
- timestamps,
- input context digest,
- output manifest reference,
- exit metadata,
- cancellation details.

### `AgentHandoff`

Portable file-based assignment containing:

- objective,
- active step,
- approved scope,
- constraints,
- relevant decisions,
- permitted actions,
- prohibited actions,
- required outputs,
- return manifest schema,
- verification expectations.

### `AgentResult`

Untrusted manifest containing:

- source run or handoff ID,
- worker claims,
- declared returned files,
- declared limitations,
- tool metadata,
- no governance approval.

## 9.8 Packs and capabilities

### `PackManifest`

Contains:

- pack ID,
- semantic version,
- schema compatibility,
- provided workflows,
- templates,
- explanations,
- data-only resources,
- declared capabilities by reference,
- integrity digest.

### `PackTrustDecision`

Pack trust states:

- `untrusted`
- `trusted-data`

### `CapabilityDefinition`

Contains:

- capability ID and version,
- provider,
- purpose,
- input and output schemas,
- executable and arguments if executable,
- working-directory rules,
- timeout,
- side-effect class,
- authorization class,
- trust requirement,
- verification hooks.

Capability trust states:

- `disabled`
- `approved-once`
- `approved-for-version`
- `approved-for-project`

Trusting pack data never authorizes code execution.

## 9.9 Events and state

### `AuditEvent`

The canonical journal event described in Section 7.

### `MaterializedState`

The reconstructable current view described in Section 7.3.

### `ExplanationProfile`

Supported v1 profiles:

- `minimal`
- `standard`
- `guided`
- `mentored`

---

# 10. Configuration Contract

`forge.yaml` is project-level configuration. It must not contain secrets.

A representative shape:

```yaml
schema_version: "1.0"
project_id: "<generated-uuid>"

owner:
  id: "<generated-uuid>"
  display_name: "Repository Owner"

behavior:
  explanation_profile: standard
  require_clean_git_for_close: false

imports:
  max_files: 100
  max_file_bytes: 10485760
  max_total_bytes: 104857600
  preserve_failed_staging: true

artifacts:
  digest_algorithm: sha256
  max_preserved_object_bytes: 104857600

packs:
  local_paths: []

agents:
  preferred_adapter: null

security:
  secret_path_patterns:
    - ".env"
    - ".forge/local/secrets/**"
```

Exact default limits may be changed in the approved implementation plan, but the plan must document and test them.

Configuration behavior:

- Unknown keys produce actionable warnings or errors according to compatibility policy.
- Secrets are rejected from governed configuration where detectable.
- Environment-specific adapter paths belong in `.forge/local/` or process configuration, not tracked governance files.
- `forge config show|validate` may be added if needed for operational clarity, even though it is not required in the minimum initial CLI list.

---

# 11. CLI Behavioral Contract

The CLI is the supported mutation interface. Core services must remain independently testable.

Commands must:

- use structured error classes,
- return stable nonzero exit codes for failure categories,
- avoid partial mutations,
- explain blockers,
- respect explanation profiles,
- support noninteractive operation where owner authority is not required,
- never assume an agent claim equals completion.

## 11.1 Repository and diagnostics

### `forge init`

- Initialize current repository.
- Refuse destructive overwrite.
- Bootstrap owner identity.
- Create required directories.
- Merge `.gitignore` rules safely.
- Validate configuration and bundled packs.

### `forge doctor`

- Validate repository layout, schemas, journal, snapshot, locks, artifact digests, pack locks, capabilities, adapters, and Git policy.
- Never repair destructive conditions automatically.
- Provide explicit remediation instructions.

### `forge status`

- Show lifecycle, integrity, workflow, steps, stale records, active runs, gates, and next actions.
- Support active or archived initiative selection.

### `forge next`

- Return legal next actions and blockers.
- Never mutate state.

### `forge history`

- Show validated event history.
- Support filtering by event type, step, actor, run, or archived initiative.

### `forge recover`

- Validate the journal chain.
- Rebuild materialized state explicitly.
- Preserve the prior corrupt snapshot for inspection.
- Record recovery provenance.

## 11.2 Initiative lifecycle

### `forge create`

- Require initialized repository and no active initiative.
- Select and lock a trusted-data pack and workflow.
- Create immutable initiative ID.
- Record objective and predecessor references.
- Initialize state and journal.

### `forge begin`

- Begin an eligible step.
- Enforce prerequisites and actor authority.
- Create a manual or tool run where appropriate.

### `forge complete`

- Record a worker claim and transition to verification or acceptance state only when declared outputs exist.
- Must not bypass checks or acceptance.

### `forge decide`

- Record general owner or authorized decisions.
- Support supersession rather than mutation.

### `forge pause`

- Pause the initiative after validating no unsafe mutation is in progress.
- Record pause reason and resumable state.

### `forge resume`

- Validate integrity and restore active operation.
- Generate a resumption summary.

### `forge close`

- Enter or complete closing flow.
- Require declared outputs, checks, review, acceptance, preserved revisions, and lessons.
- Archive atomically.

### `forge abandon`

- Require owner authority, reason, unfinished work, unresolved risks, and final abandonment record.
- Archive atomically as abandoned.

## 11.3 Artifacts and evidence

### `forge artifact add`

- Register a new logical artifact and first revision.
- Require normalized repository-relative path.
- Calculate digest.
- Record provenance.

### `forge artifact revise`

- Register a new immutable revision.
- Never overwrite the historical record.
- Propagate stale dependencies.

### `forge artifact list|show`

- Display revisions, paths, digests, preservation status, dependencies, and staleness.

### `forge evidence add`

- Register evidence and bind it to artifact revisions or checks.

### `forge evidence list|show`

- Display evidence scope, limitations, and referenced revisions.

## 11.4 Acceptance

### `forge acceptance record`

- Owner-only.
- Require declared checks and evidence.
- Bind acceptance to exact digests and scope.
- Record residual risks.

### `forge acceptance revoke`

- Owner-only.
- Allowed only while active or closing.
- Invalidate dependent progression.

### `forge acceptance show`

- Display current and historical acceptance state.

## 11.5 Runs

### `forge run list|show`

- Display run states and metadata.

### `forge run cancel`

- Apply cancellation rules from Section 8.6.
- Never imply step success.

## 11.6 Handoffs and result imports

### `forge handoff`

- Generate portable Markdown and JSON assignment files.
- Include bounded neutral context and a return manifest schema.
- Store temporary generated handoffs under `.forge/local/` unless explicitly promoted.

### `forge import-result`

Use the safe staged-import pipeline:

1. Read a declared result manifest.
2. Copy declared files into `.forge/local/import-staging/<run-id>/`.
3. Reject absolute paths, traversal, symlink escapes, undeclared files, duplicate targets, and invalid schemas.
4. Enforce file count and size limits.
5. Scan known secret locations and patterns.
6. Never execute content.
7. Calculate digests.
8. Preview registration actions.
9. Require explicit artifact revision behavior for collisions.
10. Register records and events atomically.
11. Preserve failed staging until explicit removal.

## 11.7 Agents

### `forge agent context`

- Generate canonical context and optional vendor-specific views.
- Support `--target neutral|codex|claude`.

### `forge agent doctor`

- Detect installed CLI, version, compatibility, authentication availability where safely detectable, and limitations.

### `forge agent run`

- Invoke an approved adapter capability.
- Record a run.
- Capture exit status and returned files.
- Route all outputs through staged import.

## 11.8 Packs and capabilities

### `forge pack list|validate|trust|untrust`

- List bundled and local packs.
- Validate data contracts.
- Record owner trust decisions.
- Untrust prevents future use but does not rewrite history.

### `forge capability list|inspect|approve|revoke`

- Show exact provider, version, invocation, permissions, side effects, and approval duration.
- Revocation prevents future execution.
- Historical runs remain visible.

---

# 12. Pack Architecture

## 12.1 Pack rules

A data-only pack may contain:

- manifest,
- workflow YAML,
- artifact templates,
- evidence templates,
- explanation text,
- context-selection rules,
- declarative check requirements,
- schemas.

It may not execute code merely because it is trusted-data.

## 12.2 Bundled `software-basic`

Workflow:

1. Discover
2. Plan
3. Execute
4. Verify
5. Review
6. Close

The pack may define software-specific outputs and validators, but the core may not.

Representative outputs:

- objective and constraints,
- requirements,
- implementation plan,
- project artifacts,
- verification report,
- review report,
- lessons artifact.

## 12.3 Synthetic non-software conformance workflow

M1 includes a test-only non-software workflow that proves the core can govern a simple non-code initiative without modification.

It should use different artifact names and no software fields.

## 12.4 Bundled `research-basic`

Workflow:

1. Frame Question
2. Plan Research
3. Collect Evidence
4. Synthesize
5. Verify Structure and Support
6. Review
7. Close

Validators check declared evidence structure, citation presence, traceability, and support mapping. They must not claim automatic factual truth verification.

## 12.5 Pack conformance suite

Every pack must pass shared tests for:

- manifest validity,
- unique identifiers,
- semantic versions,
- workflow reachability,
- valid transitions,
- valid artifact/evidence references,
- gate authority requirements,
- explanation completeness,
- absence of undeclared executable behavior,
- compatibility declarations.

---

# 13. Agent Adapter Architecture

## 13.1 Neutral interface

`AgentAdapter` must support:

- availability detection,
- version reporting,
- compatibility assessment,
- invocation preparation,
- process start,
- cancellation,
- output capture,
- result manifest production,
- diagnostics.

Adapters do not receive direct access to core mutation services.

## 13.2 Canonical context

Authoritative generated context lives at:

```text
.forge/active/context/current.json
.forge/active/context/current.md
```

It contains only:

- objective,
- active step,
- approved scope,
- relevant constraints,
- relevant decisions,
- permitted actions,
- prohibited actions,
- required outputs,
- expected evidence,
- return contract,
- known blockers.

It must exclude:

- unrelated repository files,
- ignored paths,
- `.forge/local/secrets/`,
- credentials,
- environment dumps,
- unrelated archived content,
- unnecessary prior artifacts.

## 13.3 Vendor files

`AGENTS.md` and `CLAUDE.md` are derived integration views.

Rules:

- Existing user content is preserved.
- FORGE manages only clearly delimited blocks or references.
- Changes require preview and confirmation.
- Vendor files may be regenerated from neutral context.
- Vendor files are never authoritative governance records.

## 13.4 Adapter fallback

If an adapter is missing, incompatible, or not approved:

- FORGE provides a portable manual handoff.
- The workflow remains usable.
- No lifecycle rule changes.

---

# 14. Verification and Security Model

## 14.1 Validator execution

Trusted local validator capabilities declare:

- exact executable,
- argument array,
- permitted working directory,
- input artifact revisions,
- timeout,
- expected outputs,
- environment allowlist where needed,
- side-effect class,
- risk class.

Do not invoke shell command strings. Use executable and arguments separately.

## 14.2 Side-effect classes

At minimum:

- `read_only`
- `repository_write`
- `external_reversible`
- `external_irreversible`
- `sensitive`

Side-effect class influences owner approval and cancellation behavior.

## 14.3 Path safety

All governed paths must:

- be normalized,
- be repository-relative,
- reject absolute paths,
- reject traversal outside repository,
- resolve symlinks before authorization,
- reject symlink escape,
- use allowlisted governed locations for imports.

## 14.4 Secret safety

FORGE must:

- exclude `.forge/local/` from context,
- scan imported manifests and files for configured secret paths and obvious credential patterns,
- warn or reject accidental inclusion according to policy,
- never store provider credentials in governed records,
- avoid logging secrets in adapter output summaries.

Secret detection is defense in depth, not a guarantee.

## 14.5 Malicious input handling

Tests must include:

- hostile YAML and JSON sizes,
- malformed journals,
- duplicate IDs,
- path traversal,
- symlink races where practical,
- oversized files,
- undeclared result files,
- command-injection strings,
- executable pack content hidden as data,
- forged adapter claims,
- invalid hashes,
- incompatible schema versions.

## 14.6 Threat-model statement

FORGE provides:

- integrity checks,
- auditability,
- explicit trust,
- safe default import behavior,
- authorization rules within supported commands.

FORGE does not provide protection from a malicious process with the owner’s account permissions. Such isolation requires external operating-system or container controls.

---

# 15. Explanation Profiles

## 15.1 Minimal

Show:

- current status,
- required action,
- blockers,
- concise result.

## 15.2 Standard

Show:

- what is happening,
- required action,
- expected outputs,
- blockers,
- result.

## 15.3 Guided

Also explain:

- why the step exists,
- why authority is required,
- what evidence means,
- common mistakes.

## 15.4 Mentored

Also provide:

- deeper conceptual teaching,
- alternatives and tradeoffs,
- reflection prompts,
- links to relevant project decisions and lessons.

Profiles must use the same underlying governance results.

---

# 16. Milestone Governance

Every milestone follows this sequence:

1. Owner approves milestone implementation brief.
2. Agent implements only that milestone.
3. Agent runs required tests.
4. Agent produces a completion claim.
5. Agent produces an evidence packet.
6. Owner or reviewing agent assesses the result.
7. Owner records acceptance, rejection, or required corrections.
8. Work stops until the next milestone is approved.

Each milestone report must include:

- work completed,
- files and contracts added or changed,
- ADRs created,
- test results,
- manual walkthrough results,
- unresolved issues,
- deviations from specification,
- risks introduced,
- recommended next step,
- confirmation that deferred features were not added.

---

# 17. Milestone 0 — Constitution and Repository Foundation

## 17.1 Objective

Establish the project identity, source structure, legal foundation, development tooling, and non-negotiable contracts before production implementation.

## 17.2 Deliverables

### Governance documents

Create:

- `docs/constitution.md`
- `docs/glossary.md`
- ADR for embedded project repositories
- ADR for one active and many archived initiatives
- ADR for source-of-truth hierarchy
- ADR for event ordering and materialized state
- ADR for artifact revisions and preservation store
- ADR for owner identity and actor authority
- ADR for immutable decisions and acceptance
- ADR for pack trust and capability trust
- ADR for threat model and same-user limitation
- ADR for pre-v1 compatibility policy
- imported ADR-0001 naming/project-direction record

### Project foundation

Configure:

- Python 3.12+
- `pyproject.toml`
- Hatchling build backend
- Typer
- Pydantic v2
- PyYAML
- pytest
- Ruff
- Pyright
- package CLI entry point using provisional `forge`

### Public project files

Create:

- Apache-2.0 `LICENSE`
- `NOTICE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- initial `README.md`
- `CHANGELOG.md`

### CI

Configure Windows, macOS, and Linux jobs for:

- clean installation,
- CLI help smoke test,
- Ruff,
- Pyright,
- pytest,
- package build.

Do not publish packages.

### Naming gate

Document that FORGE, Python package names, domains, and public marks remain provisional until clearance. Do not publish publicly as production branding before owner approval.

## 17.3 Pre-v1 contract policy

M0 freezes principles and compatibility rules, not every schema field.

Before release candidate:

- contracts may change through ADRs and migrations,
- no silent breaking changes,
- fixtures and migration tests begin once a schema is used by an approved milestone.

Public semantic-version stability begins at v1.0.0.

## 17.4 Tests

- package builds on all platforms,
- CLI help runs,
- importable package version exists,
- schema-export placeholder command is callable if implemented,
- documentation links validate where practical.

## 17.5 Exit criteria

- Every foundational term has one canonical definition.
- Documentation explicitly says FORGE governs work but does not perform it.
- The master specification supersedes conflicting earlier handoffs.
- Clean checkout installs and displays CLI help on all target platforms.
- No production lifecycle behavior has been prematurely implemented beyond approved scaffolding.
- Owner accepts constitutional artifacts.

## 17.6 Stop condition

Stop after the M0 report. Do not begin M1.

---

# 18. Milestone 1 — Safe Foundation and First Vertical Slice

## 18.1 Objective

Build the smallest complete, secure, resumable governance workflow using the embedded repository model.

## 18.2 Core implementation

Implement:

- versioned canonical contracts,
- JSON Schema export,
- project initialization,
- owner identity bootstrap,
- initiative creation,
- workflow loading and locking,
- pack data validation and trust,
- atomic storage primitives,
- event append and sequence validation,
- materialized state,
- transition service,
- authorization service,
- artifact registration and revision,
- evidence registration,
- decision and supersession,
- approval revocation,
- claims and basic check recording,
- acceptance recording and revocation,
- manual runs,
- status and next-action calculation,
- manual handoff generation,
- safe staged result import.

## 18.3 Required CLI

Implement the M1-appropriate portions of:

- `forge init`
- `forge doctor`
- `forge create`
- `forge status`
- `forge next`
- `forge begin`
- `forge complete`
- `forge decide`
- `forge artifact add|revise|list|show`
- `forge evidence add|list|show`
- `forge acceptance record|revoke|show`
- `forge run list|show|cancel`
- `forge handoff`
- `forge import-result`
- `forge history`
- `forge close`

M1 close may use a preliminary non-hash-chained archive process if M2 owns full archival hardening, but it must preserve required records and exact accepted revisions.

## 18.4 Workflows

Ship:

- bundled `software-basic`,
- test-only synthetic non-software workflow.

## 18.5 Explanation profiles

Implement:

- Standard
- Guided

## 18.6 Import pipeline

Implement every requirement from Section 11.6, including preserved failed staging.

## 18.7 Tests

### Unit

- contract validation,
- path normalization,
- digest calculation,
- transition conditions,
- authorization,
- stale dependency calculation,
- pack validation,
- explanation rendering.

### Integration

- initialize repository,
- create initiative,
- complete workflow,
- restart process between every step,
- owner gate enforcement,
- manual handoff/import,
- artifact revision invalidation,
- acceptance flow.

### Negative and security

- missing artifacts,
- invalid transitions,
- agent owner-decision attempt,
- traversal,
- absolute paths,
- symlink escape,
- undeclared files,
- import collisions,
- invalid manifests,
- excessive file count and size.

### Acceptance

A scripted walkthrough must:

1. initialize a small example repository,
2. create a software initiative,
3. stop and restart,
4. generate a handoff,
5. import an untrusted result,
6. register artifacts,
7. record a claim,
8. record checks and evidence,
9. record owner acceptance,
10. close and inspect the result.

Run the synthetic non-software workflow without changing core code.

## 18.8 Exit criteria

- Software initiative completes end to end.
- Non-software conformance workflow completes unchanged.
- Missing requirements block progression.
- Unauthorized actors cannot record owner actions.
- Unsafe imports cannot escape staging or repository boundaries.
- Artifact changes stale dependent checks and acceptance.
- Standard and Guided profiles differ only in explanation detail.
- ESDF remains unchanged.

## 18.9 Required report

Include:

- architecture implemented,
- schema inventory,
- command inventory,
- full test results,
- walkthrough transcript,
- known limitations,
- ESDF concept assessment without migration.

## 18.10 Stop condition

Stop after owner review. Do not begin M2.

---

# 19. Milestone 2 — Integrity, Recovery, Archival, and Abandonment

## 19.1 Objective

Make governed state dependable across corruption, concurrency, interrupted writes, closure, abandonment, and successor initiatives.

## 19.2 Deliverables

Implement:

- canonical JSON serialization,
- event hash chain,
- snapshot-to-journal-head binding,
- cross-process lock,
- idempotency keys,
- journal validation,
- stale-lock diagnostics,
- artifact drift detection,
- stale evidence and acceptance propagation,
- explicit pause and resume,
- explicit recovery,
- atomic closure and archival,
- atomic abandonment and archival,
- successor initiative creation,
- archived status and history views,
- schema migration framework,
- hybrid Git policy.

## 19.3 Event hashing

Define deterministic serialization and hash calculation. A valid event chain must detect:

- changed event contents,
- removed middle events,
- reordered events,
- invalid sequence numbers,
- invalid previous hashes,
- truncated final records.

Truncation recovery policy must be conservative and explicit. Do not silently discard events.

## 19.4 Recovery

`forge recover` must:

- preserve corrupt snapshots,
- validate the journal to the last valid event,
- reject ambiguous histories,
- reconstruct materialized state,
- verify referenced artifacts and objects,
- record recovery identity and provenance.

## 19.5 Closure

Closure requires:

- required steps complete,
- current artifact revisions preserved,
- required checks passed or explicit allowed risk acceptance recorded,
- required review artifacts,
- current owner acceptance,
- closure decision,
- lessons artifact,
- healthy integrity.

## 19.6 Abandonment

Abandonment requires:

- owner decision,
- reason,
- unfinished work summary,
- unresolved risks,
- active run handling,
- final abandonment record,
- preserved governed history.

Abandonment may occur without successful checks or acceptance but may not appear as closure success.

## 19.7 Successors

A successor initiative:

- gets a new immutable ID,
- references one or more archived predecessors,
- imports no approval automatically,
- may explicitly reuse artifacts through new registrations and provenance,
- cannot mutate predecessor records.

## 19.8 Tests

- interrupted atomic writes,
- journal truncation,
- changed historical event,
- deleted snapshot,
- corrupt snapshot,
- stale lock,
- live concurrent process,
- repeated idempotent command,
- modified artifact,
- missing preserved object,
- closure interruption,
- abandonment interruption,
- successor creation,
- archive mutation refusal,
- migration provenance.

## 19.9 Exit criteria

- Valid history reconstructs state.
- Integrity mismatches never normalize silently.
- Duplicate transitions are prevented.
- Closed and abandoned archives remain distinct.
- Successors work without inherited approval.
- Archived initiatives cannot reopen.

## 19.10 Stop condition

Stop after owner review. Do not begin M3.

---

# 20. Milestone 3 — Agent Context and Governed Capabilities

## 20.1 Objective

Support replaceable external workers while preserving neutral context and FORGE authority.

## 20.2 Deliverables

Implement:

- canonical context generation,
- managed vendor references,
- `AgentAdapter` interface,
- manual adapter baseline,
- Codex CLI adapter,
- Claude Code CLI adapter,
- adapter compatibility matrix,
- adapter diagnostics,
- capability registry,
- capability approval and revocation,
- pack trust and untrust lifecycle,
- agent, pack, and capability commands.

## 20.3 Adapter requirements

Adapters must:

- use separately installed tools,
- use existing user authentication,
- record detected versions,
- refuse incompatible versions clearly,
- support cancellation,
- capture process result safely,
- write outputs only to approved temporary locations,
- produce an untrusted result manifest,
- never call core state mutations directly.

## 20.4 Capability approval preview

Before approval, show:

- capability ID and version,
- provider,
- exact executable,
- argument construction rules,
- working directory,
- environment access,
- side-effect class,
- output locations,
- approval duration.

## 20.5 Context leakage tests

Prove exclusion of:

- `.env`,
- `.forge/local/`,
- secret fixtures,
- unrelated archived initiatives,
- unrelated project directories,
- non-selected artifacts.

## 20.6 Tests

- manual handoff baseline,
- Codex available,
- Codex missing,
- Codex incompatible,
- Claude available,
- Claude missing,
- Claude incompatible,
- adapter cancellation,
- hostile adapter output,
- capability revoked during future invocation,
- trusted-data pack with disabled executable capability,
- vendor file preservation and preview.

## 20.7 Exit criteria

- Manual and adapter workers use identical governance rules.
- Missing adapters degrade to handoff.
- Vendor files regenerate from canonical context.
- Adapters cannot approve or mutate state.
- Revoked capabilities do not execute.

## 20.8 Stop condition

Stop after owner review. Do not begin M4.

---

# 21. Milestone 4 — Verification, Cancellation, Security, and Audit Hardening

## 21.1 Objective

Formalize trustworthy local verification and harden every input and execution boundary.

## 21.2 Deliverables

Implement:

- final typed claim service,
- validator execution service,
- check result service,
- evidence packet service,
- acceptance enforcement,
- complete cancellation semantics,
- hardened scope amendment and invalidation,
- workflow deviation,
- emergency override,
- risk acceptance,
- security audit events,
- incident-recovery documentation,
- comprehensive threat model.

## 21.3 Validator execution

- No shell strings.
- Validate executable and argument list.
- Enforce approved working directory.
- Apply timeout.
- Capture stdout/stderr to local run files.
- Promote only selected summaries or outputs into governed evidence.
- Record exit status accurately.
- Preserve every attempt.
- Never rewrite a failed attempt as passed.

## 21.4 False-completion tests

Seed scenarios where:

- agent claims success without files,
- files exist without required checks,
- checks target old revisions,
- acceptance targets stale evidence,
- validator exits zero but required output is missing,
- forged result manifest claims owner approval,
- override omits residual risk.

All must be blocked.

## 21.5 Security tests

Include:

- command injection,
- executable path substitution,
- unsafe working directory,
- symlink escape,
- malicious pack data,
- schema bombs within bounded test limits,
- malformed journal hashes,
- oversized imports,
- secret fixtures,
- unauthorized actors,
- revoked capability execution.

## 21.6 Exit criteria

- False completion cannot reach acceptance or closure.
- Data trust never authorizes execution.
- Revocation and supersession propagate correctly.
- Security documentation accurately describes limitations.
- Every security-sensitive action is auditable.

## 21.7 Stop condition

Stop after owner review. Do not begin M5.

---

# 22. Milestone 5 — Research and Educational Proof

## 22.1 Objective

Prove that FORGE is genuinely domain-neutral and complete its educational presentation model.

## 22.2 Deliverables

Implement:

- full `research-basic` pack,
- research artifact and evidence templates,
- citation and support mapping structures,
- structural research validators,
- shared pack conformance suite,
- Minimal profile,
- Mentored profile,
- long-gap resumption summaries,
- bounded filesystem context discovery.

## 22.3 Research safeguards

Research validators may check:

- required source metadata,
- citation format,
- claim-to-source mapping,
- missing support declarations,
- evidence packet completeness,
- explicit uncertainty.

They must not claim to automatically determine factual truth or source credibility beyond declared checks.

## 22.4 Long-gap simulation

Simulate a paused initiative with no chat history and a substantial time gap.

A new worker must be able to understand:

- objective,
- completed work,
- decisions,
- current artifacts,
- unresolved questions,
- next actions,
- acceptance requirements,

using only governed state and generated context.

## 22.5 Filesystem context discovery

Use bounded, deterministic selection based on:

- current step,
- explicit artifact relevance,
- workflow-declared context rules,
- approved scope,
- decision references.

Do not dump the repository.

SQLite FTS remains deferred unless measured tests prove the bounded approach insufficient.

## 22.6 Exit criteria

- Software and research use unchanged core services.
- Core requires no software-specific fields.
- Long-gap resumption works without prior chat.
- All explanation profiles preserve identical governance outcomes.
- A third-party data-only pack can be validated without Python.

## 22.7 Stop condition

Stop after owner review. Do not begin M6.

---

# 23. Milestone 6 — Release Candidate Hardening

## 23.1 Objective

Prepare a supportable, documented, cross-platform public release candidate.

## 23.2 Compatibility

Implement and test:

- schema compatibility rules,
- workflow and pack version constraints,
- migration from every approved pre-v1 persisted schema,
- refusal of unsupported future schemas,
- documented downgrade failure behavior,
- backup and recovery procedures.

## 23.3 Packaging

Support:

- `pipx install`,
- virtual-environment installation,
- built wheel,
- source distribution,
- CLI entry point,
- installation smoke tests from built artifacts.

Do not test release readiness only from the source tree.

## 23.4 Documentation

Complete:

- installation guide,
- quick start,
- complete user guide,
- CLI reference,
- architecture guide,
- pack-author guide,
- adapter-author guide,
- security guide,
- recovery guide,
- compatibility policy,
- migration guide,
- troubleshooting guide,
- software example,
- research example,
- known limitations.

## 23.5 Supply chain and project health

Perform:

- dependency review,
- license audit,
- vulnerability scanning,
- secret scanning,
- software bill of materials if practical,
- package metadata validation.

Release signing and OpenTelemetry may be added if justified but must not block core readiness.

## 23.6 Performance budgets

Set measured budgets for:

- CLI startup,
- `forge status`,
- journal replay at representative sizes,
- context generation,
- archive inspection,
- pack validation.

The implementation plan should propose realistic thresholds after early profiling. Performance work must preserve correctness and inspectability.

## 23.7 Dogfooding

Use FORGE to govern its own release-candidate work through a bounded framework-change workflow.

Dogfooding must produce:

- objective,
- plan,
- implementation artifacts,
- checks,
- evidence,
- owner acceptance,
- lessons.

Do not let dogfooding create circular build dependencies that prevent recovery.

## 23.8 Release-candidate evaluation

Produce:

- fresh-user test report,
- friction report,
- residual-risk register,
- compatibility matrix,
- unresolved issue disposition,
- release recommendation.

## 23.9 Exit criteria

- Fresh users complete software and research examples from built packages.
- Upgrade, backup, archive, abandonment, successor, and recovery procedures are rehearsed.
- No critical governance, integrity, import, path, or secret defect remains.
- Public compatibility commitments are documented.
- Owner resolves every release-blocking risk.

## 23.10 Stop condition

Stop after release-candidate owner review. Do not publish v1.

---

# 24. Milestone 7 — Public Production v1

## 24.1 Objective

Publish the owner-approved stable release.

## 24.2 Preconditions

Before publication:

- naming and package clearance accepted,
- release candidate accepted,
- no unresolved critical defects,
- public documentation complete,
- version alignment verified,
- release acceptance recorded through FORGE.

## 24.3 Deliverables

- version `1.0.0`,
- Git tag,
- source artifact,
- wheel,
- source distribution,
- release notes,
- compatibility matrix,
- known limitations,
- supported-version policy,
- migration guide,
- security-reporting workflow,
- issue templates,
- bug template,
- pack proposal template.

Signing may be included if ready but is not a core release blocker unless the owner later makes it one.

## 24.4 Consistency check

The following must agree:

- package version,
- CLI version,
- Git tag,
- schema versions,
- bundled pack versions,
- documentation,
- compatibility matrix,
- release notes.

## 24.5 Final acceptance journey

A new user must be able to:

1. install FORGE,
2. initialize an existing repository,
3. create an initiative with either bundled pack,
4. work manually or through a supported adapter,
5. pause and resume,
6. detect changed artifacts,
7. recover after interruption,
8. close or abandon correctly,
9. inspect the archive,
10. create a successor initiative.

## 24.6 Post-release gate

Do not begin post-v1 work until:

- a v1 retrospective is recorded,
- lessons are preserved,
- observed problems are prioritized,
- the owner approves the next roadmap.

---

# 25. Cross-Cutting Test Strategy

## 25.1 Test levels

### Unit tests

Pure validation, transition, authorization, digest, path, and rendering logic.

### Integration tests

Filesystem services, journal and snapshot behavior, pack loading, CLI-to-core wiring, import staging, adapters.

### Acceptance tests

Real CLI workflows in temporary repositories using built packages.

### Security tests

Hostile paths, imports, capabilities, packs, schemas, and claims.

### Recovery tests

Interrupted writes, corrupt snapshots, damaged journals, missing objects, stale locks.

### Cross-platform tests

Windows path behavior, macOS/Linux permissions and symlinks, line endings, atomic replacement behavior, CLI invocation.

## 25.2 Required test principles

- Use built distributions in release smoke tests.
- Test failures and rejection paths, not only happy paths.
- Preserve deterministic fixtures.
- Use golden files selectively for user-facing context and schemas.
- Avoid tests that depend on real Codex or Claude accounts in normal CI; use adapter fakes and optional manual compatibility jobs.
- Mark operating-system-specific tests explicitly.
- Every reported bug receives a regression test where practical.

## 25.3 Cumulative scenario inventory

The full suite must cover:

- schema round trips,
- incompatible versions,
- migrations,
- one active and multiple archives,
- closure and abandonment,
- successors,
- every state transition,
- unauthorized actions,
- supersession and revocation,
- artifact revision and preservation,
- stale dependency propagation,
- atomic interruption,
- concurrent commands,
- path and symlink attacks,
- import limits,
- capability trust,
- agent fallback,
- cancellation,
- false-completion blocking,
- software and research packs,
- all explanation profiles,
- clean install on every platform.

---

# 26. Documentation Strategy

Documentation is a production deliverable, not cleanup after implementation.

## 26.1 User documentation

Must explain:

- what FORGE is and is not,
- initialization,
- initiative lifecycle,
- artifacts and evidence,
- claims/checks/acceptance,
- pause/resume/recovery,
- close versus abandon,
- archives and successors,
- manual handoffs,
- adapters,
- trust and capabilities,
- common errors.

## 26.2 Architecture documentation

Must explain:

- source-of-truth hierarchy,
- event and snapshot model,
- content-addressed preservation,
- state machines,
- authority model,
- trust model,
- pack boundary,
- adapter boundary,
- security limitations.

## 26.3 Extension documentation

Pack authors need:

- manifest schema,
- workflow schema,
- templates,
- conformance tests,
- trust behavior,
- versioning rules.

Adapter authors need:

- interface contract,
- process behavior,
- result manifest,
- cancellation,
- output staging,
- compatibility declaration.

## 26.4 Recovery documentation

Must include exact procedures for:

- snapshot corruption,
- journal mismatch,
- stale locks,
- missing artifact files,
- missing preserved objects,
- failed migrations,
- interrupted closure,
- abandoned adapter runs.

---

# 27. Quality and Engineering Standards

## 27.1 Code quality

- Type public interfaces.
- Use explicit domain errors.
- Keep functions and services bounded.
- Avoid global mutable state.
- Avoid business logic in CLI rendering.
- Avoid provider conditionals in core services.
- Prefer deterministic behavior.
- Document security-sensitive code.

## 27.2 Dependency discipline

Before adding a dependency, document:

- requirement it satisfies,
- why standard library or existing dependencies are insufficient,
- maintenance and security implications,
- platform support.

## 27.3 Error behavior

Errors must be:

- actionable,
- non-destructive,
- categorized,
- suitable for human and scripted use,
- clear about whether state changed.

## 27.4 Logging

- Human-facing CLI output is not the authoritative audit record.
- Verbose process logs remain local by default.
- Governed events contain concise facts and references.
- Do not write secrets.

---

# 28. Risk Register

The implementation plan must address these risks.

## 28.1 Scope expansion

Risk: FORGE becomes an agent platform or universal project manager.

Control: milestone gates, non-goals, owner review, no deferred infrastructure.

## 28.2 Software assumptions leak into core

Risk: first pack shapes core contracts.

Control: synthetic non-software M1 workflow and research M5 proof.

## 28.3 Event/state inconsistency

Risk: files and journal disagree after interruption.

Control: atomic mutation design, idempotency, integrity state, explicit recovery.

## 28.4 Archive cannot reproduce accepted work

Risk: project files change after closure.

Control: content-addressed preserved revisions and archive references.

## 28.5 Agents gain accidental authority

Risk: adapter outputs mutate state or approve gates.

Control: adapter boundary, untrusted import, owner-only service authorization.

## 28.6 Data trust enables execution

Risk: trusting a pack runs commands.

Control: separate capability approval.

## 28.7 Cross-platform filesystem differences

Risk: atomic writes, locks, symlinks, and paths behave differently.

Control: platform-specific tests and conservative abstractions.

## 28.8 Premature contract stability

Risk: pre-v1 schemas become costly constraints.

Control: recorded pre-v1 amendments and migrations; public stability begins at v1.

## 28.9 Large artifacts

Risk: preserved objects make repositories impractical.

Control: explicit size limits, failure with guidance, large artifact providers deferred.

## 28.10 False security expectations

Risk: users assume same-user processes cannot tamper.

Control: repeated threat-model documentation and accurate language.

---

# 29. Change Control

## 29.1 When an ADR is required

Create or amend an ADR for changes to:

- source-of-truth hierarchy,
- state machine,
- owner authority,
- trust model,
- persistence format,
- archive preservation,
- pack boundary,
- adapter boundary,
- compatibility commitments,
- threat model,
- public CLI semantics.

## 29.2 Scope changes during a milestone

The implementing agent must not silently add work.

For a proposed change, report:

- problem discovered,
- impact on approved requirements,
- options,
- recommendation,
- cost and risk,
- whether work can continue safely without the decision.

Only the owner approves material scope changes.

## 29.3 Deviations

Every intentional deviation from this specification must appear in the milestone report with rationale and consequences.

---

# 30. Required Planning Response from the Receiving Agent

Before implementation, produce a document titled:

> **FORGE Production v1 — Proposed Implementation Plan**

Use the following structure.

## 30.1 Executive interpretation

Explain in your own words:

- what FORGE is,
- what it is not,
- what Production v1 must prove,
- the main architectural boundaries.

## 30.2 Repository assessment

If a repository exists, report:

- current structure,
- reusable assets,
- conflicts with this specification,
- files that should remain untouched,
- migration or cleanup needed before M0.

If no repository exists, state the proposed initialization approach.

## 30.3 Architecture plan

Describe:

- module boundaries,
- service responsibilities,
- storage transaction design,
- event and snapshot design,
- object preservation design,
- authorization design,
- pack loading design,
- adapter boundary,
- testing architecture.

Do not invent features outside this specification.

## 30.4 Milestone plan

For every milestone M0–M7, include:

- objective,
- prerequisites,
- implementation tasks in dependency order,
- files/modules expected to change,
- contracts introduced or amended,
- tests,
- documentation,
- risks,
- exit evidence,
- explicit stop point.

## 30.5 Traceability matrix

Map every major requirement in this specification to:

- milestone,
- implementation component,
- validating test,
- acceptance evidence.

## 30.6 Proposed decisions

List bounded technical decisions requiring owner review, such as:

- exact atomic transaction pattern,
- lock implementation,
- deterministic JSON serializer,
- default size limits,
- CLI exit-code categories,
- event hash format,
- pack file layout.

For each, provide options, recommendation, and tradeoffs.

## 30.7 Risk and ambiguity report

Include only material items that could:

- change architecture,
- prevent cross-platform operation,
- weaken governance,
- cause incompatible persistence,
- expand scope significantly.

Do not elevate minor naming or file-placement preferences into blockers.

## 30.8 Initial work breakdown

Provide the proposed M0 work breakdown in executable order, but do not perform it.

## 30.9 Implementation controls

Confirm that you will:

- implement one milestone at a time,
- stop after each milestone,
- avoid ESDF modification,
- avoid deferred features,
- treat agent output as untrusted,
- preserve owner authority,
- report deviations.

## 30.10 Final planning stop

End the planning response with:

> **Planning complete. No implementation has begun. Awaiting owner review and approval to start Milestone 0.**

---

# 31. Final Production-v1 Acceptance Criteria

FORGE Production v1 is complete only when all of the following are demonstrated from built distribution artifacts:

1. A user installs FORGE on Windows, macOS, or Linux.
2. The user initializes an existing repository without destructive changes.
3. The user creates one active initiative using either bundled pack.
4. The user can inspect all governed state through ordinary files and CLI views.
5. The initiative survives process interruption and long-gap resumption.
6. Workers can operate manually, through Codex, or through Claude Code under identical governance rules.
7. Worker results remain untrusted until imported, checked, evidenced, and accepted.
8. Agents and contributors cannot record owner-only actions.
9. Artifact revisions bind approvals and acceptance to exact content.
10. Changed artifacts stale dependent checks and acceptance.
11. Journal and snapshot mismatches are detected and recoverable explicitly.
12. Unsafe paths, hostile imports, and unauthorized executable capabilities are blocked.
13. Trusted-data packs cannot execute code without separate capability approval.
14. Closure requires current outputs, checks, review, evidence, and owner acceptance.
15. Abandonment remains distinct from successful closure.
16. Archives preserve exact accepted revisions and remain immutable.
17. A successor initiative can reference but not mutate its predecessor.
18. Software and research packs use unchanged core services.
19. Explanation profiles alter educational depth but not governance.
20. Documentation, packages, schemas, pack versions, and release tags agree.
21. The owner records final v1 acceptance and residual risks.

---

# 32. Completion Definition for the Implementing Agent

The agent’s work is not complete when code exists.

For each milestone, completion requires:

- implementation claim,
- passing automated checks,
- manual acceptance walkthrough,
- evidence packet,
- documented deviations and risks,
- owner review.

For Production v1, completion requires the full final acceptance criteria and public release gate.

Until the owner approves the initial implementation plan, the only authorized output is the planning document required by Section 30.
