# FORGE Friction Register

This is the living, advisory register of friction observed while using, maintaining, or
dogfooding FORGE. It is the canonical routing index for friction observations, not design or
governance authority.

An entry may identify a problem, hypothesis, workaround, or candidate response. It does not
authorize a change, amend scope, establish acceptance, supersede an ADR, or prove that a proposed
response is correct. The repository's normal authority and change-control rules still apply to any
later implementation.

## How to add or update friction

Adding or updating an entry is ordinary documentation maintenance and does not require a FORGE
initiative. The person or agent editing this register still needs the repository owner's ordinary
direction to make the file change.

1. Assign the next stable `FRI-YYYY-NNN` identifier.
2. Preserve the owner's observation separately from agent analysis.
3. Link reproducible evidence when it exists. Label memory, inference, and unverified reports
   honestly.
4. Record a workaround or candidate response without presenting it as authorization.
5. Append status changes to the entry's history instead of erasing the original observation.
6. Link any later roadmap item, ADR, initiative, commit, pull request, or validation result.

Use these statuses:

- `Observed`: reported once and not independently reproduced;
- `Confirmed`: reproduced or supported by direct evidence;
- `Needs discussion`: the observation is established but the desired behavior is unresolved;
- `Planned`: routed into an owner-reviewed plan, without implementation authority;
- `Addressed`: a response was implemented but has not passed the intended regression observation;
- `Verified`: the intended regression observation passed;
- `Deferred`: intentionally postponed with a reason; or
- `Rejected`: no change will be made, with a reason.

Semantic impact determines severity and change-control needs. Line count does not. A one-line
authority change can require an ADR and full initiative, while a long documentation index can be
ordinary maintenance.

## Entry template

```md
## FRI-YYYY-NNN — Short title

- Status:
- Severity:
- Area:
- First observed:
- Sources:
- Related roadmap items:

### Owner observation

What the owner experienced or reported, preferably in the owner's words.

### Reproduced evidence

Exact sessions, commands, outputs, artifacts, counts, or environmental details.

### Agent analysis

Interpretation or likely cause, clearly separated from observed fact.

### Current workaround

What can reduce the friction before a durable response exists.

### Candidate response

Ideas for later discussion. This section grants no implementation authority.

### Status history

- YYYY-MM-DD — Status — reason and linked evidence.
```

## Project-basic dogfood baseline

The entries below came from two owner-observed sessions in the same disposable project directory:

- completed plain-request run: `01a0088f-7eee-79a3-b10a-c25acfa867cc`;
- unfinished universal-starter-prompt run: `01a0088a-de07-7ef2-b3ec-1900c5fb42c7`; and
- project directory: `C:\Users\kryst\Code\FORGE Projects\Project-Basic-Test`.

The two sessions are useful qualitative evidence, but they are not a controlled comparison. The
unfinished run selected `guided` and a backtester-only milestone. The completed run selected
`mentored` and delivered a dashboard-and-alerts prototype.

## FRI-2026-001 — Excessive approval interruptions

- Status: Confirmed
- Severity: High
- Area: Direct-agent interaction, `project-basic`
- First observed: 2026-08-16
- Sources: completed plain-request run
- Related roadmap items: UX-01, Phase 6, Phase 9

### Owner observation

The owner reported that the run felt like repeatedly approving steps rather than collaborating on
or learning about the project.

### Reproduced evidence

The completed run contained 35 owner turns. Thirty were short procedural responses: seven phase
begins, fifteen variants of `continue`, seven step acceptances, and one initiative-creation
authorization. Only five turns carried substantive project direction or reflection. The agent's
active processing time across those turns was approximately 26 minutes; the available thread view
did not expose token totals.

### Agent analysis

The agent inserted conversational pauses around participant-level phase transitions and routine
claim, check, evidence, and verification mechanics. Those pauses were not all owner-only authority
gates.

### Current workaround

At the start of a bounded phase, explicitly authorize routine in-scope agent work through the next
artifact review or owner-only gate.

### Candidate response

After an owner approves a reviewed artifact, let the agent create and register it, submit its
claim, run declared checks, bind evidence, and request FORGE verification without additional
`continue` prompts. Keep exact owner acceptance and other owner-only gates separate.

### Status history

- 2026-08-16 — Confirmed — counted directly from the completed session.

## FRI-2026-002 — Authorization envelope documented but not operationalized

- Status: Confirmed
- Severity: High
- Area: Direct-agent facilitation
- First observed: 2026-08-16
- Sources: completed plain-request run; accepted collaboration task map
- Related roadmap items: UX-01, Phase 6

### Owner observation

The owner expected related approvals to be combined into fewer prompts.

### Reproduced evidence

The accepted task map contained a bounded conversational authorization envelope for source,
tests, documentation, dependency configuration, and validation. The agent nevertheless continued
to request separate phase starts and routine submission confirmations.

### Agent analysis

The envelope was treated as explanatory text rather than an operating instruction for routine
agent work.

### Current workaround

Restate the envelope in the conversation with its files, validation, stopping condition, and next
owner-only gate.

### Candidate response

Give the direct-agent protocol an explicit execution rule for consuming a reviewed, revocable
authorization envelope without changing any persisted FORGE gate.

### Status history

- 2026-08-16 — Confirmed — the envelope and the later interruption pattern coexist in the same run.

## FRI-2026-003 — Mentored profile did not produce learning by building

- Status: Confirmed
- Severity: High
- Area: Explanation profiles
- First observed: 2026-08-16
- Sources: completed plain-request run; review and lessons artifacts
- Related roadmap items: UX-02, Phase 6, Phase 9

### Owner observation

The owner reported that selecting `mentored` did not cause the agent to teach and that there was
little real conversation.

### Reproduced evidence

The agent explained a few research concepts, but built the full prototype during one creation
turn. The review report recorded that no direct owner code-practice evidence existed. The closure
lessons recommended prediction, practice, feedback, and recap before implementation advances.

### Agent analysis

The profile changed the narration more than the labor split. It lacked an observable standard for
project-specific explanation, optional practice, feedback, and learning recap.

### Current workaround

Ask for one useful project-domain explanation or owner practice task at each phase where learning
would materially help, while preserving an explicit delegation option.

### Candidate response

Add representative profile-behavior tests and a non-ceremonial mentoring contract: explain,
connect to the project, offer a meaningful task, provide feedback when attempted, and recap when
useful.

### Status history

- 2026-08-16 — Confirmed — supported by the owner's report and the run's own final artifacts.

## FRI-2026-004 — Bootstrap quality depends too heavily on the starter prompt

- Status: Observed
- Severity: Medium
- Area: Agent orientation and starter prompts
- First observed: 2026-08-16
- Sources: both project-basic sessions
- Related roadmap items: UX-03, Phase 6, Phase 9

### Owner observation

The owner found the universal-prompt session more detailed and more faithful to the intended
approach than the plain-request session under the same owner-reported model and effort setting.

### Reproduced evidence

The universal prompt explicitly elicited protocol and version checks, durable-location
confirmation, task ownership, learning goals, beginner examples, domain teaching, and an
understanding check. The plain request produced a viable bootstrap but did not expose all of those
behaviors as clearly.

### Agent analysis

The universal prompt appears to compensate for protocol-discovery or instruction-prioritization
weakness. Because the sessions used different profiles, objectives, and lengths, it does not prove
prompt causation across the lifecycle.

### Current workaround

Use the universal starter prompt for consequential dogfood until a controlled plain-prompt
regression passes.

### Candidate response

Make a short plain-language request sufficient for correct FORGE orientation. Treat the starter
prompt as customization and recovery assistance rather than a correctness dependency.

### Status history

- 2026-08-16 — Observed — qualitative bootstrap comparison only; controlled regression needed.

## FRI-2026-005 — Dogfood provenance does not control model and effort

- Status: Planned
- Severity: Medium
- Area: Dogfood methodology
- First observed: 2026-08-16
- Sources: owner report; both project-basic sessions
- Related roadmap items: UX-04, Phase 9

### Owner observation

The owner believes model and reasoning effort materially influence facilitation and result quality
and selected Terra with medium effort as the standard baseline for future tests.

### Reproduced evidence

The session reader did not expose model or effort metadata, so the Terra-medium configuration is
owner-reported provenance. Existing dogfood guidance does not require recording model, effort,
prompt variant, app version, protocol identity, or pack identity as one controlled test record.

### Agent analysis

Model and effort can affect project reasoning and facilitation, but deterministic governance
integrity should not depend on either. Uncontrolled configuration makes comparisons anecdotal.

### Current workaround

Record the owner-selected model, effort, profile, prompt, FORGE commit, CLI and protocol versions,
pack version and digest, session ID, and date manually.

### Candidate response

Use Terra with medium effort as the primary dogfood baseline, then run a limited cross-model check
only after the baseline behavior is stable.

### Status history

- 2026-08-16 — Planned — owner selected Terra with medium effort for future controlled tests.

## FRI-2026-006 — Closure-phase acceptance was mistaken for terminal archival

- Status: Confirmed
- Severity: High
- Area: Lifecycle presentation
- First observed: 2026-08-16
- Sources: completed plain-request run; read-only project status
- Related roadmap items: UX-05, Phase 6

### Owner observation

The owner experienced the run as having completed the entire FORGE process.

### Reproduced evidence

The agent said the workflow was fully completed and accepted while also noting that it was not
archived. A later read-only status check showed all seven steps completed, lifecycle `active`, and
zero archives. Terminal `forge close` was never owner-authorized or executed.

### Agent analysis

The workflow step named `close` prepares and accepts closure artifacts, while the separate
owner-only `forge close` transaction creates the terminal archive. The naming and presentation
make those two events easy to collapse.

### Current workaround

After accepting the workflow's close step, explicitly report that closure preparation is complete
and present terminal archival as a distinct owner-only gate.

### Candidate response

Clarify the two meanings in the protocol, workflow guidance, quickstart, receipts, and terminal
agent response. Consider compatibility-safe display wording such as `closure preparation` without
silently renaming locked historical step IDs.

### Status history

- 2026-08-16 — Confirmed — current state remains active with every workflow step completed.

## FRI-2026-007 — `forge next` does not surface terminal close

- Status: Confirmed
- Severity: High
- Area: CLI agent surface
- First observed: 2026-08-16
- Sources: read-only `forge status` and `forge next` in the dogfood project
- Related roadmap items: UX-05, Phase 6

### Owner observation

The completed workflow provided no intuitive final action leading to an archive.

### Reproduced evidence

With all seven steps completed and the initiative still active, `forge status` reported `No actions
are executable now`; `forge next` did not present `forge close`. The protocol separately states
that terminal close becomes legal after all workflow requirements are accepted.

### Agent analysis

The command appears to report step transitions but omits the next legal owner-only lifecycle gate.
This undermines an otherwise strong agent-orientation surface.

### Current workaround

Consult the closure documentation after the final step acceptance rather than relying on
`forge next` alone.

### Candidate response

Make `forge next` display the exact terminal-close ceremony and consequence when every workflow
requirement is accepted, with a regression test for this state.

### Status history

- 2026-08-16 — Confirmed — reproduced against the still-active dogfood repository.

## FRI-2026-008 — Agents selected stale check-result identifiers

- Status: Observed
- Severity: Medium
- Area: Evidence-binding ergonomics
- First observed: 2026-08-16
- Sources: completed plain-request run
- Related roadmap items: UX-06, Phase 6

### Owner observation

No separate owner observation was recorded; the retries contributed to the run's overall delay.

### Reproduced evidence

During plan and creation verification, the agent attempted to bind stale or incorrect immutable
check-result IDs. FORGE refused both bindings safely, after which the agent retried with the IDs
reported by the CLI.

### Agent analysis

Fail-closed behavior worked, but selecting the correct current result is unnecessarily error-prone
for agents when multiple identifiers are present in recent output.

### Current workaround

Re-read the latest receipt or resolve the exact check result immediately before evidence binding.

### Candidate response

Provide a stable machine-readable current-result field or a safe exact-next-command rendering that
cannot select an older check result accidentally.

### Status history

- 2026-08-16 — Observed — occurred twice in one run; needs a focused reproduction before design.

## FRI-2026-009 — Windows launcher and sandbox process friction

- Status: Confirmed
- Severity: Medium
- Area: Installation and local execution
- First observed: 2026-08-16
- Sources: both project-basic sessions
- Related roadmap items: ID-03, Phase 2, Phase 5

### Owner observation

No separate owner observation was recorded; the workarounds contributed to the length and
technical density of the run.

### Reproduced evidence

The global `forge` launcher failed with `uv trampoline failed to canonicalize script path`; agents
used the FORGE repository's `.venv\Scripts\forge.exe`. During creation, `uv` cache access, Python
child-process launching, and the local Streamlit server also required workarounds or elevated
execution.

### Agent analysis

The FORGE launcher problem and the execution sandbox are distinct causes, but both interrupt the
beginner experience and can be misread as project failures.

### Current workaround

Use the confirmed repository-local executable for FORGE and project-local Python for validation;
label sandbox restrictions separately from application defects.

### Candidate response

Repair or replace the Windows launcher route, document the fallback prominently, and keep
environment failures distinguishable from FORGE integrity failures.

### Status history

- 2026-08-16 — Confirmed — reproduced across both sessions.

## FRI-2026-010 — Git durability warning arrived after the project was complete

- Status: Observed
- Severity: Medium
- Area: Project bootstrap and continuity
- First observed: 2026-08-16
- Sources: completed plain-request run; read-only `forge doctor`
- Related roadmap items: UX-07, Phase 3

### Owner observation

No separate owner observation was recorded. The final response disclosed that the project was not
inside a Git worktree only after the prototype and governed records had been created.

### Reproduced evidence

`forge doctor` reports the repository as healthy and filesystem-authoritative, with a warning that
governed records are not versioned by Git. A durable local directory is allowed, so this is not an
integrity failure.

### Agent analysis

The owner should choose the intended Git posture during bootstrap rather than discover the
continuity limitation at closure.

### Current workaround

Ask during intake whether filesystem-only operation is intentional and explain its backup and
collaboration consequences.

### Candidate response

Add an early, non-blocking Git-posture playback to project bootstrap and preserve filesystem-only
operation as a valid explicit choice.

### Status history

- 2026-08-16 — Observed — timing problem established; desired default needs discussion.

## FRI-2026-011 — Owner label was inferred rather than explicitly collected

- Status: Observed
- Severity: Medium
- Area: Initialization interview
- First observed: 2026-08-16
- Sources: completed plain-request run
- Related roadmap items: UX-03, Phase 6

### Owner observation

No separate owner objection was recorded.

### Reproduced evidence

The plain-request run proposed `--owner-name "kryst"` without first receiving that display label in
the visible conversation. The universal-prompt run explicitly asked which owner name to record.

### Agent analysis

A path, account name, or session identity should not be treated as an owner-provided governance
label.

### Current workaround

Ask for the exact display label before presenting `forge init`.

### Candidate response

Add an explicit owner-label field to bootstrap coverage and test that agents do not infer it from
the environment.

### Status history

- 2026-08-16 — Observed — visible conversation lacked an explicit owner-label answer.

## FRI-2026-012 — No documented proportional path for small changes

- Status: Planned
- Severity: High
- Area: Governance usability
- First observed: 2026-08-16
- Sources: owner direction in the FORGE review session
- Related roadmap items: GOV-01, Decision D-06

### Owner observation

The owner wants to record and make small FORGE or project changes without forcing every change
through an entire initiative.

### Reproduced evidence

The Constitution identifies sensitive changes requiring ADRs, and contributing guidance refers to
material changes, but no single beginner-facing policy distinguishes observations, direct
maintenance, compact governed work, and full initiatives.

### Agent analysis

When every useful change appears to require the largest ceremony, governance becomes approval
theater. When the boundary is undocumented, agents may also under-govern consequential changes.

### Current workaround

Use ordinary documentation maintenance for advisory registers, indexes, typo fixes, broken links,
and other narrow non-behavioral changes. Record exact scope and validation in Git without claiming
FORGE verification or acceptance.

### Candidate response

Document a proportional change policy. For now, keep a compact governed mechanism deferred. Reopen
that design only when repeated changes cannot be handled honestly through documentation
maintenance or a full initiative.

### Status history

- 2026-08-16 — Planned — owner selected documentation-only maintenance as sufficient for now.
