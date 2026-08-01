# FORGE Local Production-v1 Conversational Completion Handoff

**Prepared:** 2026-08-01

**Status:** Owner-approved direction; design and implementation have not begun

**Target:** Produce a feature-complete personal/local Production-v1 candidate that is ready for
extended owner testing through the native Codex and Claude Code Windows applications

## Purpose and authority

This handoff replaces the **execution direction** in
`docs/handoffs/m7-production-v1-completion-handoff.md`. The earlier handoff remains historical
evidence of the public-release plan that was accepted at the time; do not edit it to imply that the
old decision never existed.

The owner subsequently decided that:

- Production v1 is a personal, local release for the foreseeable future;
- PyPI, TestPyPI, GitHub Releases, public release tags, public support channels, and public
  publication automation are not required;
- FORGE may remain a provisional local codename;
- naming and formal legal clearance must be reopened before commercialization, hosted service,
  active marketing, public package publication, GitHub Release publication, or meaningful
  third-party adoption;
- the conversational layer described here is mandatory for local Production v1; and
- the current public-release initiative should not be forced through a workflow whose locked
  publication steps no longer describe the desired outcome.

This document authorizes investigation, design preparation, bounded implementation proposals,
local validation, and preparation of the exact governance transition. It does **not** authorize an
agent to infer owner acceptance, cancel or abandon the current initiative without presenting the
exact action, create a successor without owner confirmation, alter an immutable archive, publish
anything externally, change repository visibility, push a tag, or declare local Production v1
accepted before the owner completes extended use testing.

## Repository baseline at handoff

- **Repository:** `C:\Users\kryst\Code\FORGE`
- **Remote:** `https://github.com/KJG54/FORGE.git`
- **Branch:** `main`
- **HEAD:** `4bd3b75` (`Merge pull request #19 from KJG54/codex/m7-increment-2`)
- **Locally recorded `origin/main`:** `4bd3b75`
- **Working tree when inspected:** clean
- **Local tags:** none
- **Distribution:** `forge-governance`
- **Import package:** `forge`
- **CLI:** `forge`
- **Runtime/package version:** `1.0.0`
- **Package classifier:** `Development Status :: 2 - Pre-Alpha`
- **Local interpreter:** CPython 3.14.4
- **M6 archive:** `ea57c39e-98a9-475f-bb60-bb41f7e90f7c`
- **M6 archive digest:**
  `sha256:5a25afde013b3013752b97db88587eb6808cd583ddd05439a293b59085750325`

Verify all of these before relying on them. In particular, inspect the branch, worktree, remote
tracking state, tags, active initiative, archive integrity, package version, and Python environment.
Authenticated GitHub or Git network operations on Windows require narrowly scoped host access to
the Windows keyring; do not treat a sandboxed authentication error as invalid credentials.

## Current governed state

The repository is healthy, but it still contains the active public-release initiative:

- **Initiative:** `d57d380f-a51a-4786-a5e3-eb80d7888cb3`
- **Objective:** Deliver an owner-approved public FORGE Governance Production v1 release
- **Locked workflow:** `forge-production-release / production-v1-release@0.1.0`
- **Lifecycle:** active
- **Current step:** `prepare` (`in_progress`)
- **Active run:** `0fca736a-c6e3-46d1-99db-b2b779ec9596`
- **Completed step:** `scope`
- **Open decision:** `49bac69f-a2a4-4a70-aa5d-64ec1206a1ad`
- **Permitted next action:** `complete:prepare`

M7 Increment 1 was accepted and merged. Increment 2 implementation was merged but was **not**
completed through its governed checks, evidence, verification, and owner acceptance. The files on
`main` therefore include useful 1.0.0 compatibility work, but a merge and an ADR status do not
fabricate governed acceptance.

The locked workflow later requires `approve-publication`, `publish`, and `verify-publication`, with
public-release artifacts and authority. Reinterpreting those steps as local installation would
falsify the locked workflow. A scope amendment cannot replace the workflow lock. The owner approved
the clean approach: preserve the attempt as an honest abandonment archive and use a suitable
successor for the local objective.

## Why the direction changed

An owner-led trial found that FORGE's governance mechanisms work but the human interaction layer is
not intuitive enough for daily use. Even starting a project exposes the user to a long sequence of
FORGE mechanics. The current user guide asks a new user to initialize, inspect and validate packs,
create an initiative, inspect status, begin a step, register artifacts, claim, check, register
evidence, verify, and accept. Those separations are correct internally, but they are not the desired
human interface.

The target experience is:

> A good project manager who happens to keep perfect records. The ceremony should read as the
> project manager taking notes, never as the owner filling out governance forms.

## Actual primary user and agent model

The primary v1 workflow is not an agent process launched by `forge agent run`.

The owner uses the native Codex and Claude Code applications on Windows. Each application can open a
chat directly in a selected project folder and branch. That workspace agent can read and mutate the
repository and run shell commands. The owner normally assigns one agent to one milestone, then asks
for a detailed handoff so a new agent can continue without depending on the old chat context.

The required default interaction is:

- the owner converses in ordinary language;
- the workspace agent performs routine repository and FORGE mechanics;
- FORGE emits canonical, quotable receipts;
- the agent quotes those receipts and separates them from its judgment and plan;
- the owner personally executes consequential owner-only commands when prompted; and
- the next milestone agent resumes from validated repository state, predecessor archives, and a
  derived handoff rather than hidden prior-chat memory.

Direct workspace agents share the same-user filesystem threat boundary. The owner-shell ceremony is
a useful procedural speed bump, not authentication or hostile-agent isolation. Documentation must
say that plainly.

## Local Production-v1 boundary

The immediate target is a **feature-complete local candidate ready for extended owner testing**.
Do not claim final Production-v1 acceptance merely because implementation and automated tests pass.
The owner expects to exercise FORGE across real projects and milestones before deciding that it is
comfortable enough to call complete.

The candidate must allow the owner to:

1. build one exact local wheel and install it cleanly on the owner's Windows machine;
2. open Codex or Claude Code directly in an ordinary project folder;
3. start a new project conversationally without learning routine FORGE commands;
4. have the agent read supplied documents before asking questions;
5. complete a coverage-based project/milestone interview;
6. review a concise proposed vision, objective, scope, constraints, labor split, and definition of
   done;
7. initialize the repository and create the initiative only after owner confirmation;
8. receive canonical receipts and clear next actions after governed mutations;
9. work through a bundled workflow with the agent handling routine mechanics;
10. stop without a farewell ritual and recover the in-flight reasoning later;
11. use a warm recap that combines derived governed state with clearly labeled local working notes;
12. personally execute owner-only acceptance, scope, risk, terminal, and other consequential
    commands when prompted;
13. reject or redirect work without leaving misleading governed claims dangling;
14. recover interrupted work and validate repository health;
15. close or abandon a milestone safely;
16. inspect the immutable archive; and
17. give a new milestone agent a derived transition brief and create a validated successor.

## Explicitly removed from the local-v1 blocker set

The following are not required for the personal/local candidate:

- PyPI or TestPyPI publication;
- a GitHub Release;
- a public `v1.0.0` tag or pushed release tag;
- trusted-publisher or protected-publication environment configuration;
- public issue forms, support commitments, or public security-reporting configuration;
- public installation verification;
- public release attestations or publication provenance;
- formal trademark clearance or registration; and
- a public cross-platform support commitment.

Do not delete sound cross-platform tests, supply-chain checks, compatibility work, or documentation
merely because they are no longer publication blockers. Preserve useful engineering quality while
removing external release ceremony from the definition of done.

## Naming and legal disposition

`FORGE`, `forge-governance`, `forge`, and the `forge` command are provisional local identifiers.
No final public-name decision is needed now. Do not perform a repository-wide rename merely for
local v1 unless new evidence makes it necessary.

The naming decision must be reopened before any public or commercial expansion. The future review
should prefer a distinctive mark and should separately assess product name, distribution, import
package, CLI, domains, repositories, marketplace uses, and applicable trademark records. Package
availability is not legal clearance.

Supersede rather than rewrite ADR-0059. ADR-0060's compatibility work remains useful, but its public
tag and publication statements need explicit disposition in a later local-v1 ADR. Historical
alpha-version and public-plan records remain immutable evidence of what was true when recorded.

## Conversational-layer design decisions

The owner accepted the following direction. The next agent must turn it into exact contracts and
present unresolved choices before implementation.

### 1. Canonical receipts

FORGE, not the agent, must render the authoritative portion of a mutation receipt. The desired
vocabulary separates provenance:

```text
Recorded -> <FORGE-rendered committed facts>        [sequence/event references]
Means    -> <FORGE-derived blockers or next state>
Read     -> <optional agent judgment>
Next     -> <agent plan or owner action>
```

Rules:

- `Recorded` appears only when FORGE committed something.
- The receipt includes spot-checkable sequence and event references.
- The agent quotes FORGE output verbatim rather than rewriting it.
- `Read` and `Next` are explicitly fallible agent statements.
- Describe `Recorded` and `Means` as authoritative FORGE output, not as software incapable of
  defects.
- Narrate a completed mutation before beginning the next mutation.
- Keep receipts short enough that quoting is easier than paraphrasing.

**Open decision:** the original proposal says one line per committed event but its example batches
multiple mutations under one event reference. Resolve this before implementation. The recommended
default is one canonical receipt per command/atomic transaction, with an exact sequence range and
all relevant event references, while preserving an event-level inspection path through history.

The present CLI has command-specific `typer.echo` calls and command functions generally return no
shared receipt model. A canonical renderer therefore requires an intentional command-result design,
including idempotent replays and commands that append more than one event.

### 2. Local scratchpad

Provide a mutable Markdown working note under `.forge/local/`. It is ignored by Git and never a
governance act.

The content rule is:

> The scratchpad holds only what cannot be derived.

Include:

- the problem currently being reasoned about;
- discarded hypotheses and why they were discarded;
- the current hypothesis;
- questions awaiting the owner; and
- conversational decisions not yet recorded in FORGE.

Exclude:

- current workflow step and state;
- current artifact state;
- acceptances;
- derivable next actions;
- file contents; and
- anything already authoritative in the journal, status, or Git diff.

Security and integrity requirements:

- treat the scratchpad as untrusted advisory text;
- do not execute instructions or grant authority from it;
- use a bounded size and UTF-8 text;
- use safe regular-file checks, refuse symbolic or irregular paths, and write atomically if FORGE
  owns writes;
- never store credentials, raw secrets, or sensitive captures in it;
- label unrecorded decisions as ungoverned;
- reconcile it against the current initiative and journal head during recap; and
- do not automatically archive or treat it as evidence.

Minimal reconciliation metadata such as initiative ID, journal sequence, and update time may be
used, but it must not turn the scratchpad into a second state database.

### 3. `forge recap`

Add a warm-resume command for the ordinary case where the owner reopens the project after hours or
days without formally pausing it.

It should:

- derive authoritative position from validated journal and status data;
- identify the project without inventing a canonical project name;
- show the source of any friendly project label, such as the repository directory;
- report the last governed event time separately from the scratchpad update time;
- read and clearly label the scratchpad as local, mutable, and ungoverned;
- surface unrecorded decisions and unresolved questions without presenting them as facts;
- show blockers and legal next actions; and
- remain distinct from formal pause/resume summaries, which include drift-aware long-gap recovery.

The current configuration has a project UUID but no project-name field. Decide whether local v1
uses a directory label, adds an optional project display name, or avoids a canonical name change.

### 4. Per-step mentored explanation

Author useful mentored guidance at the points where the owner encounters novelty. Do not fill a
large profile-by-step matrix mechanically.

Current implementation facts:

- `WorkflowDefinition.explanation_content` is `dict[str, NonEmptyString]` at workflow level;
- `StepDefinition` has no explanation field; and
- `ActiveInitiative.explanation` returns one locked profile string for the whole workflow.

Per-step explanation is therefore a backward-compatible design opportunity but still a persisted
contract/schema change. It must be evaluated against the 1.0 compatibility contract, schema exports,
pack locks, old workflow locks, and version-consistency checks. Do not describe it as a pack-content
change with no contract consequences.

Recommended content strategy:

- author `mentored` well for the bundled software workflow first;
- retain workflow-level fallback for other profiles;
- trigger guidance on novelty, such as first encounter with a step or event type and first session
  after a meaningful gap; and
- keep guidance subordinate and skippable without changing permissions or outcomes.

### 5. First-project interview and bootstrap

The interview occurs before the first initiative exists. The complete flow must also account for
installation detection and `forge init`, which the original proposal omitted.

The agent should:

1. detect whether the CLI is installed and compatible;
2. detect whether the selected folder is a repository and whether FORGE is initialized;
3. ask for documents up front and inspect them before questioning;
4. state what those documents cover and what remains unknown;
5. cover the product, first milestone definition of done, hard constraints, existing assets,
   standing labor split, and abandonment conditions;
6. attempt to draft the vision and identify exact gaps instead of merely calling the vision vague;
7. allow the owner to proceed with explicit limitations rather than making vagueness an absolute
   block;
8. present the proposed initialization, pack, objective, scope, and trust implications; and
9. ask the owner to perform the owner-authorized initialization/creation confirmation.

Use a full interview at project start and a shorter vision/milestone check at successor creation.

### 6. Agent protocol

The protocol is advisory behavior for direct Codex and Claude Code workspace agents. It should be
available through managed `AGENTS.md` / `CLAUDE.md` integration without overwriting owner-authored
content.

Current `vendor_context.py` only manages a small pointer block to generated canonical context. It
does not generate the full proposed protocol. Decide how protocol content is versioned, distributed,
updated, and referenced while preserving the managed-marker safety model.

Required protocol topics:

- receipt narration and provenance vocabulary;
- interview conduct;
- agent-drafted planning and visible labor split;
- delegation only when specification is cheaper than execution and evidence quality does not drop;
- human task packaging with an evidence method and falsification condition;
- three tiers of plan change;
- owner-only command presentation;
- specific objection once, followed by compliance only with legal FORGE transitions;
- rejection and invalidation without leaving misleading claims;
- cheapest generation that works, never guessed verification;
- independent checks;
- append-only undo mechanisms and their consequences; and
- explicit boundaries: FORGE governs records, Git contains file changes, FORGE is not a kill
  switch, and confident codebase misunderstanding is the central practical failure mode.

### 7. Authority versus operator provenance

The current direct CLI often constructs the configured owner actor even when a workspace agent
invoked the command. The design must distinguish, where relevant:

- **authority**: whose permission authorizes the action; and
- **operator/provenance**: whether the action was performed through the owner, a direct Codex or
  Claude workspace session, a manual contributor, or a registered adapter run.

Do not claim authentication that does not exist. A local conversational-session reference can make
attribution more honest without pretending that a same-user agent cannot spoof it. At minimum,
agent-authored worker claims must not misleadingly appear to be human-authored.

Assess contract impact carefully. Avoid adding a large identity/security system that is not needed
for the same-user local threat model.

### 8. Owner-only actions

The default owner experience is conversation plus personally executed consequential commands.
The agent should print the exact command and explain its consequences. The owner pastes it into the
owner's shell.

The current acceptance syntax is:

```text
forge acceptance record <step-id> --scope <exact-accepted-scope>
```

The earlier design example using an acceptance UUID and `--attest` is not implemented. Preserve the
valuable exact-scope binding unless an intentionally reviewed CLI change supersedes it.

Owner-personal actions should include acceptance, revocation, scope amendment, risk acceptance,
terminal abandonment/closure, pack trust, successor creation, and any future external publication.
The ceremony deters accidental authority transfer; it is not cryptographic proof of who typed.

### 9. Rejection, rework, and plan changes

Discussion before a claim is ordinary steering. Once a claim exists, the record must acquire an
honest disposition through supported append-only mechanisms.

Do not assume `rework` can be invoked from every state. In the current bundled workflow, `rework`
has source state `invalidated`. Artifact revision, acceptance revocation, scope amendment, run
cancellation, or another supported invalidation may be required before a step can restart.

Use this plan-change model as a starting point:

- route changed before dependent work: scratchpad plus narration;
- route changed after work depends on it: revise the governed plan and accept recursive staleness;
- definition of done changed: owner-governed scope amendment with a justified return step.

An accepted implementation plan should remain stable. Do not use the governed plan artifact as a
continuously rewritten daily checklist. Daily in-flight position belongs in the scratchpad or a
separate explicitly local view.

### 10. Milestone successor handoff

Do not overload the current `forge handoff` semantics silently. The current command produces a
disposable bounded worker assignment for an eligible active step. It does not produce a milestone
transition brief and cannot run after terminal archival.

Design a separate milestone/successor view or command that can derive:

- initiative identity, objective, effective scope, terminal outcome, archive digest, and lineage;
- accepted artifacts, decisions, checks, evidence, limitations, risks, and lessons;
- exact reusable predecessor artifact revisions;
- current repository branch, commit, worktree state, version, and other freshly observed facts,
  clearly distinguished from governed history;
- startup validation steps for the receiving agent; and
- unresolved local reasoning only after it has been promoted into an owner-reviewed carryover,
  lessons, or next-milestone artifact.

The generated Markdown is a human-readable view, not a new source of truth. A receiving agent must
validate the archive and repository rather than trusting prose.

The scratchpad may not survive a different worktree or machine. Anything required by the next
milestone must be promoted before closure. Do not make arbitrary mutable scratchpad content a hard
closure authority gate; instead surface a clear warning and require the governed closeout materials
to carry durable unresolved matters.

## Suggested governance transition

The next agent must first inspect the exact current run and active state. The proposed transition is
terminal and therefore requires a fresh exact owner decision at execution time.

### A. Prepare the transition record

Before asking the owner to act:

- verify the worktree is clean or identify every change;
- inspect the active run and current initiative using supported commands;
- preserve the current public-release scope, ADRs, artifacts, decisions, and unaccepted Increment 2
  state unchanged;
- draft the exact abandonment reason, unfinished-work summary, and residual risks; and
- explain that cancellation never implies success and abandonment preserves an immutable archive.

Likely owner commands, after exact review, are:

```powershell
forge run show 0fca736a-c6e3-46d1-99db-b2b779ec9596 -C .
forge run cancel 0fca736a-c6e3-46d1-99db-b2b779ec9596 `
  --reason "The owner replaced the public-release objective with a personal/local Production-v1 objective" `
  -C .
forge status -C .
forge abandon `
  --reason "The locked public-release workflow no longer matches the owner-approved local Production-v1 outcome" `
  --unfinished-work "Public preparation, candidate verification, publication approval, publication, public verification, retrospective, and closeout remain incomplete; accepted work is preserved for explicit reuse under a suitable successor" `
  --risk "The conversational-layer contracts and implementation remain incomplete" `
  --risk "Merged Increment 2 compatibility code has not received governed step acceptance" `
  --risk "Local Production-v1 acceptance requires extended owner testing in real Codex and Claude Code projects" `
  -C .
```

The receiving agent must confirm the actual CLI help and current state before presenting these.
Use fresh idempotency keys for terminal mutations and preserve them for interruption-safe retries.
Do not execute the commands merely because they appear in this handoff.

### B. Validate the abandonment archive

After owner-authorized abandonment:

- record the exact archive ID and digest;
- run healthy status and doctor checks;
- inspect the abandoned archive through supported `status --archive` and history commands;
- prove no terminal staging or retired-active marker remains; and
- never edit either the M6 archive or the abandoned public-M7 archive.

### C. Create a suitable successor

The existing local `forge-framework-change@0.1.0` workflow is a plausible successor workflow:

- `scope`
- `implement`
- `verify-release`
- `review-risk`
- `closeout`

Its closeout explicitly records release-candidate readiness without publishing Production v1,
which fits the local candidate objective better than the locked public workflow. Validate this fit
against the final scope before selection; do not create a new workflow merely for naming symmetry.

The successor should reference both:

- the successful M6 archive `ea57c39e-98a9-475f-bb60-bb41f7e90f7c`; and
- the abandoned public-M7 archive `d57d380f-a51a-4786-a5e3-eb80d7888cb3`.

Successor creation imports no progress or acceptance. Reuse any useful artifact through exact
predecessor revision references, and re-evaluate it under the local scope. The code already merged
to `main` remains ordinary repository state, but its governed meaning must not be overstated.

The owner should personally execute the reviewed `forge create` command. A likely objective is:

> Deliver and validate a feature-complete personal/local FORGE Production-v1 candidate with an
> intuitive conversational layer for direct Codex and Claude Code workspace agents, ready for
> extended owner testing without public publication.

The exact scope must include the accepted conversational features, compatibility constraints,
local packaging, validation boundary, exclusions, and stop point.

## Recommended implementation increments

Keep changes bounded and reviewable. The next agent may refine these boundaries after repository
inspection, but must record material changes rather than silently expanding scope.

### Increment L1 - Local-v1 scope and conversational contracts

- Record the superseding local-only release/channel ADR.
- Record FORGE as a provisional local codename and the triggers for renewed clearance.
- Define the direct workspace-agent model, first-run journey, authority/operator provenance,
  receipts, scratchpad, recap, protocol, owner actions, and milestone transition contract.
- Define exact compatibility effects and migration/non-migration behavior.
- Define the owner-testing stop point: feature-complete candidate, not final acceptance.
- Stop for owner review before code.

### Increment L2 - First-run and managed agent protocol

- Add the safe, versioned conversational protocol integration for Codex and Claude Code.
- Preserve owner-authored `AGENTS.md` and `CLAUDE.md` content and managed-marker guarantees.
- Cover installation/init detection, document-first interview, coverage playback, draft vision,
  exact owner confirmation, and bootstrap next action.
- Add tests proving current managed context behavior remains byte-safe and backward-compatible.

### Increment L3 - Canonical transaction receipts

- Implement the reviewed receipt result model and renderer.
- Cover new commits, multi-event commands, failures, refusals, and idempotent replays.
- Derive blockers/next state from replayed FORGE state rather than agent inference.
- Migrate high-frequency mutation commands consistently; do not create two competing receipt
  dialects.
- Keep detailed inspection commands available for forensic use.

### Increment L4 - Scratchpad and warm recap

- Add the safe local scratchpad boundary.
- Implement `forge recap` with authoritative/local separation and reconciliation.
- Cover missing, empty, stale, oversized, malformed, symbolic, irregular, and cross-initiative
  scratchpad cases.
- Preserve formal pause/resume and recovery behavior.

### Increment L5 - Mentored explanations and daily interaction

- Add the reviewed backward-compatible per-step explanation shape or a safer equivalent.
- Author the used mentored path rather than filling every profile mechanically.
- Add novelty/fallback behavior without changing locked permissions or transitions.
- Update schema exports, pack validation, compatibility documentation, and old-lock tests as needed.

### Increment L6 - Direct-operator provenance and owner ceremony

- Implement the smallest honest authority/operator distinction required by the accepted design.
- Ensure agent-authored claims are not presented as human-authored.
- Present exact owner-only commands and consequences without claiming authentication.
- Validate rejection, invalidation, acceptance, revocation, scope change, and terminal paths.

### Increment L7 - Milestone/successor transition brief

- Add a distinct successor/milestone handoff path rather than silently changing worker handoffs.
- Support terminal archive input and exact predecessor revision references.
- Separate governed facts, fresh Git/repository observations, and durable carryover.
- Validate receipt on a clean checkout/archive-only repository and a new successor.

### Increment L8 - Local candidate integration and documentation

- Update README, installation, user guide, continuity, handoff, acceptance, security, recovery,
  compatibility, and local release documentation.
- Remove public publication from the v1 definition without deleting historical decisions.
- Ensure package/runtime/version contracts agree for the local candidate.
- Build one exact wheel and sdist locally; use the exact wheel for downstream installation tests.
- Produce the local candidate manifest, hashes, known limitations, residual risks, and owner test
  guide.

### Increment L9 - Feature-complete candidate validation

- Run focused and complete automated validation.
- Exercise clean local-wheel installs on the owner's supported Windows/Python environment.
- Rehearse the complete new-project, daily-work, warm-resume, acceptance, rejection, recovery,
  abandonment, closure, archive, milestone-handoff, and successor journeys.
- Exercise both bundled packs where compatible.
- Exercise both native Codex and Claude Code app workflows with owner participation; record which
  results are owner-observed and cannot be independently automated.
- Stop with a feature-complete candidate and an explicit extended-testing plan.

## Validation expectations

Use focused tests for each bounded increment. Before handing the candidate to the owner for extended
testing, run at minimum:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pyright `
  --pythonpath C:\Users\kryst\Code\FORGE\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m pytest `
  --basetemp <fresh-path-outside-the-repository>
.\.venv\Scripts\python.exe -m build --no-isolation `
  --outdir <fresh-path-outside-the-repository>
```

Also run the existing version-consistency, distribution-smoke, archive, recovery, backup,
migration, Git-policy, security, and performance checks. Do not weaken existing gates merely to
obtain green results. Use an external temporary directory for Git-sensitive pytest repositories;
do not put them under the real repository's ignored `.forge/local/` tree.

Build one exact local wheel and use that byte-identical wheel for clean venv and `pipx` tests. The
primary acceptance environment is the owner's Windows machine and current intended interpreter.
Existing cross-platform CI remains useful supplementary evidence but does not create a public
support promise.

## Owner-led extensive testing plan

Feature completion is the beginning of the test campaign, not its conclusion. Prepare a concise test
guide covering at least:

1. a new empty software project;
2. an existing project with documents that frame but do not fully define the goal;
3. a research workflow;
4. a project resumed after a day or more without formal pause;
5. an explicit formal pause/resume with working-copy drift;
6. owner rejection after a worker claim;
7. a mid-milestone plan revision;
8. a definition-of-done scope amendment;
9. interrupted mutation recovery;
10. safe abandonment;
11. successful closure and immutable archive inspection;
12. a new agent starting the successor milestone without old chat context; and
13. backup and restore on the owner's actual machine.

Track friction separately from correctness defects. The owner should be able to answer:

- Did I have to know a routine FORGE command?
- Did the agent distinguish records, derived state, judgment, and plans?
- Could I tell exactly when owner authority was required?
- Did recap recover what we were figuring out, not merely where the workflow stopped?
- Could the next agent continue without trusting the previous handoff prose blindly?
- Did any receipt become noisy enough to skim?
- Did the system ever attribute agent work misleadingly to me?
- Did the governance ceremony feel like the project manager taking notes?

Do not record final local-v1 acceptance until this campaign produces enough evidence for the owner
to be comfortable.

## Required reading for the receiving agent

Before changing files or governed state, read:

- this handoff completely;
- `docs/handoffs/m7-production-v1-completion-handoff.md` as historical context;
- `release/production-v1/scope.md` and `release/production-v1/compatibility-statement.md`;
- ADR-0059 and ADR-0060;
- `docs/constitution.md`;
- `docs/milestones/m6-report.md` and M6 Increment 8;
- `docs/agent-context.md`, `docs/handoffs-and-imports.md`, `docs/continuity.md`,
  `docs/successors.md`, `docs/acceptance-and-invalidation.md`, `docs/recovery.md`,
  `docs/closure-and-archives.md`, `docs/security.md`, and `docs/persistence.md`;
- `src/forge/contracts/workflows.py`;
- `src/forge/core/lifecycle.py`, `agent_context.py`, `vendor_context.py`, `handoffs.py`,
  `continuity.py`, `authorization.py`, `verification.py`, `acceptance.py`, and `archival.py`;
- `src/forge/cli/app.py`, especially initialization, mutation output, run cancellation,
  acceptance, handoff, close, and abandon commands;
- both bundled packs, `forge-framework-change`, and `forge-production-release`;
- the schema and migration registries;
- relevant M5/M6 tests for explanation profiles, vendor context, handoffs, resumption,
  successors, archival, and one-wheel validation; and
- the active M7 records through supported FORGE commands.

The owner-provided conversational design proposal was supplied as a temporary attachment in the
prior chat. Do not depend on that attachment being available. This handoff incorporates the durable
decisions and the repository corrections discovered during review.

## Non-negotiable constraints

- FORGE governs work; it does not become an autonomous owner.
- Preserve the distinction between claims, checks, evidence, verification, acceptance, and
  authority.
- Preserve hash chaining, replay, locking, idempotency, recovery provenance, snapshot binding,
  exact-byte artifacts, archive validation, and terminal immutability.
- Never modify the M6 archive or a future abandoned-M7 archive.
- Do not reinterpret locked public-release steps as local steps.
- Do not execute owner-only terminal or successor commands merely because this handoff contains
  examples.
- Do not publish to PyPI, TestPyPI, GitHub Releases, or another public channel.
- Do not create or push `v1.0.0` or any release tag without a new exact owner decision.
- Do not configure trusted publishers, package credentials, repository secrets, security settings,
  or public support channels.
- Do not change repository visibility.
- Do not store credentials, tokens, signing keys, or raw secrets in governed data, Git, logs,
  handoffs, scratchpads, or plaintext environment files.
- Keep command execution shell-free where the existing argument-vector boundary requires it.
- Do not claim cryptographic owner authentication or hostile same-user isolation.
- Do not make deferred public-release work a local-v1 blocker.
- Do not declare final local Production v1 accepted before extended owner testing.
- Use `apply_patch` for edits, preserve unrelated user changes, and keep branches/commits/pushes
  owner-directed.

## Immediate first task for the receiving agent

Do not begin conversational-layer implementation immediately.

First:

1. verify the baseline and read the required materials;
2. inspect the active run and public-M7 initiative;
3. present any repository contradictions or missing design decisions;
4. produce the exact L1 local-v1 scope and conversational contracts;
5. present the cancellation, abandonment, archive-validation, and successor-creation effects and
   exact owner commands; and
6. wait for the owner's exact terminal/governance approvals.

After the clean successor exists, proceed through bounded increments, stopping at each material
contract or owner-acceptance boundary. The final deliverable for this agent is a locally built,
validated, feature-complete candidate plus a practical owner test guide—not a public release and not
fabricated final acceptance.

## Suggested opening prompt for the next agent

> Continue FORGE from
> `docs/handoffs/local-production-v1-conversational-completion-handoff.md`. Treat the earlier public
> M7 handoff and active public-release initiative as historical/current state that must be preserved,
> not as the desired outcome. Verify `main` and governed state before editing. First complete only
> the design and governance-transition preparation: define the exact local Production-v1 scope and
> conversational contracts, inspect active run `0fca736a-c6e3-46d1-99db-b2b779ec9596`, and present
> the precise cancellation, abandonment, archive-validation, and successor-creation consequences
> for owner approval. Do not execute terminal mutations, implement code, publish anything, create a
> tag, or infer owner acceptance from this prompt. The target is a personal/local, feature-complete
> conversational candidate for direct Codex and Claude Code workspace agents, followed by extended
> owner testing.
