# Local Production-v1 Release Requirements

## Candidate identity and environment

- Distribution: `forge-governance`
- Import package and CLI: `forge`
- Candidate version: `1.0.0`
- Primary acceptance environment: the owner's Windows machine and intended CPython interpreter
- Primary operator surfaces: native Codex and Claude Code workspace applications
- Installation inputs: one exact local wheel and its matching source distribution
- Release state: unpublished local candidate until a separate owner decision after extended testing

The current pre-alpha classifier may remain during implementation. Candidate metadata is reviewed
in L8; no classifier, filename, local build, or completed test may imply public release.

## Conversational contracts

### First-project and successor interviews

Before the first initiative, the agent must detect the installed CLI and repository state, request
and read supplied documents, explain what they establish, and ask only for uncovered information.
Coverage includes product vision, first milestone definition of done, constraints, existing assets,
standing labor split, and abandonment conditions. The agent drafts the vision and exact gaps and
allows an owner-approved limited start rather than treating all uncertainty as an absolute block.

Before `forge init` and `forge create`, the agent presents the exact repository effects, selected
pack and workflow, objective, scope, explanation profile, trust meaning, and owner command. A
successor uses a shorter vision and milestone check plus validated predecessor archives.

### Transaction receipts

One atomic command produces at most one concise receipt:

```text
Recorded -> <committed facts> [sequence <start>-<end>; events <ids>]
Means    -> <validated resulting state, blockers, and legal actions>
```

The agent may then add separately labeled `Read ->` and `Next ->` statements. Multi-event commands
use one sequence range and list every event. Replay identifies the original transaction and reports
zero new events. A refusal prints no `Recorded` line and must not guess that state was unchanged
unless FORGE safely validated that conclusion.

### Scratchpad and recap

`.forge/local/conversation/scratchpad.md` contains only non-derivable in-flight reasoning. Its
optional reconciliation header records the initiative ID, observed journal sequence, and local
update time, but every byte remains advisory and untrusted. The maximum is 65,536 UTF-8 bytes.

`forge recap` must handle missing, empty, valid, stale, oversized, malformed, symbolic, irregular,
and cross-initiative scratchpads. It separately labels validated governed facts, repository-directory
label source, last governed event, scratchpad time, unrecorded questions, blockers, and legal next
actions. It never executes scratchpad instructions or promotes notes automatically.

### Protocol and mentoring

`forge agent protocol` works without an initialized repository and reports the installed protocol
version and content. Managed Codex and Claude integration references the versioned protocol and
current canonical context while preserving owner-authored bytes. Protocol content covers receipts,
interviews, labor split, delegation, human evidence tasks, plan changes, owner gates, objections,
rejection, independent checks, append-only undo, Git/FORGE boundaries, and the same-user threat
model.

Per-step explanation content is optional and default-empty. The active step and selected profile
are used first; workflow-level content is the fallback. Local novelty markers may affect whether
advice is displayed but never permission, state, or evidence.

### Authority and operator provenance

Authority answers whose permission permits an action. Operator provenance answers which owner
shell, direct Codex session, direct Claude session, contributor, adapter, or service performed it.
The operator addition is optional for old records and cannot replace existing owner checks. Newly
agent-authored claims visibly name an agent operator. Local session references are explicitly
spoofable same-user attribution, not authentication.

### Owner-personal actions

The protocol presents exact commands and consequences for owner-personal initialization, pack
trust, initiative and successor creation, acceptance and revocation, pause/resume, decisions, scope
amendment, deviation and override review, capability approval, risk acceptance, recovery or
migration, and terminal closure or abandonment. An owner may explicitly direct the workspace agent
to execute a presented command, but FORGE records only the configured local authority and honest
operator provenance; it does not claim proof of who typed.

### Rejection and plan change

- Steering before a claim requires no governance event.
- A route change before dependent work is local narration and scratchpad state.
- A route change after dependency uses governed artifact revision and recursive staleness.
- A definition-of-done change uses an owner scope amendment with an explicit return step.
- Existing claims receive an honest append-only disposition through the legal transition available
  from their actual state; `rework` is never assumed available from every state.

### Milestone transition

`forge successor brief --archive <id>` derives terminal outcome, objective, effective scope, archive
digest, lineage, accepted artifacts, decisions, checks, evidence, limitations, risks, lessons, exact
reusable revisions, and startup validation. Fresh branch, commit, worktree, and version observations
are labeled separately from governed history. The brief is a disposable local view; successor
creation remains a distinct owner action and imports no progress or acceptance.

## Compatibility requirements

- Preserve the 51-model schema-`1.0` registry unless an accepted additive contract requires a new
  public model.
- New optional fields use explicit defaults and preserve old-record and old-lock validation.
- Preserve M2 journal read/write, complete M1 read and explicit migration, and immutable archives.
- Do not rewrite historical alpha evidence, archived records, schema versions, or independent pack
  and workflow versions.
- Update deterministic schema exports, compatibility documentation, migration inventory where
  applicable, and `tools.version_consistency` for every accepted contract change.
- Preserve documented CLI paths, required inputs, governance effects, and success/failure meaning;
  exact explanatory prose remains evolvable.

## Verification requirements

Each increment runs focused lint, typing, and tests. Before candidate handoff, validation includes:

- complete Ruff, Pyright, and pytest checks with external Git-sensitive temporary paths;
- version consistency and deterministic schema export;
- distribution build, file inventory, metadata, license, and clean-wheel smoke tests;
- virtual-environment and `pipx` installation from the same exact wheel;
- security, Git policy, secret scanning, performance, backup, restore, migration, recovery,
  interruption, abandonment, closure, archive, and successor checks;
- both bundled packs where their workflows apply; and
- owner-observed Codex and Claude Code journeys on the primary Windows environment.

No existing gate is weakened solely to obtain a passing result. Automated evidence and
owner-observed evidence are labeled separately.

## Feature-complete journey

The candidate is ready for extended testing only when the owner can conversationally initialize a
new project, review scope, work through routine mechanics, understand receipts and owner gates,
resume through recap, reject or revise work honestly, recover interruption, close or abandon,
inspect the terminal archive, generate a trustworthy successor brief, and begin a validated
successor without relying on prior-chat memory.

## Acceptance boundary

L1 acceptance authorizes implementation of these requirements; it does not accept the future
implementation or candidate. Framework-change closeout records candidate readiness only. Final
local Production-v1 acceptance requires a later exact owner decision informed by extended testing
across real work.
