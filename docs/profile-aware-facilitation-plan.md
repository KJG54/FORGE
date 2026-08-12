# Profile-Aware Collaboration and Learning Plan

This is an implementation handoff for adding beginner-friendly, phase-explicit,
profile-aware collaboration and learning guidance to FORGE. It is not a
governed decision, accepted initiative scope, or owner approval by itself. An
agent implementing this plan must still follow `forge agent protocol`, inspect
repository state, and present the normal owner gates before mutating governed
FORGE state.

## Problem

FORGE has strong governance boundaries, but fresh-user testing shows that the
owner experience can still feel procedural, blended together, and dependent on
the agent already understanding FORGE. In particular:

- fresh agents may confuse FORGE with unrelated `forge` tools;
- beginners need a short universal prompt that routes agents to the right source
  of truth;
- the six-heading document-first interview is correct but too abstract for many
  owners;
- explanation profiles currently affect FORGE explanation depth more than
  practical project collaboration and learning behavior;
- workflow steps do not consistently render as distinct human-readable phases;
- owner, agent, either-party, and owner-only tasks are not consistently mapped;
- guided and mentored modes should help owners learn about what they are
  building or researching, not just learn FORGE terminology;
- guided and mentored use should feel like talking with a teacher who is guiding
  the owner through a real project, not filling out a form; and
- FORGE should remain usable with capable agents beyond Codex and Claude without
  pretending every agent has a first-class adapter.

## Product Direction

FORGE should provide the structure that lets any capable workspace agent become
a better project guide and, when requested, a better project mentor. The agent
remains conversational; FORGE remains the authority for governed records. The
new layer should help the agent answer:

- Where are we in the project?
- Why does this phase exist?
- What should the owner do?
- What should the agent do?
- What can either party do?
- Which actions are owner-only authority gates?
- What does the owner want to learn through this project?
- What concepts, skills, and resources would help the owner understand the work?
- What questions must be answered before moving forward?
- What can remain uncertain for now?
- What proves this phase is done?

The system should improve every explanation profile, with `mentored` receiving
the richest project-domain teaching, learning-path, and walkthrough behavior.
FORGE education remains part of the experience, but it is secondary to helping
the owner understand the work being built or researched.

## Goals

1. Add profile-aware collaboration and learning behavior across `minimal`,
   `standard`, `guided`, and `mentored`.
2. Add explicit phase guidance so workflow steps do not blend together.
3. Add collaborative labor guidance for owner, agent, either-party, and
   owner-only gate responsibilities.
4. Add pack-level interview and learning guidance so agents ask better questions
   and adapt to the owner's experience level without hardcoding every
   conversation in core CLI logic.
5. Add a conversational teacher contract for guided and mentored modes so agents
   gather context naturally, teach through the project, and translate the
   conversation into FORGE records.
6. Add a universal starter prompt for fresh agents that do not know FORGE.
7. Select the explanation profile at initiative creation for now; profile
   switching during a later phase is intentionally deferred.
8. Keep FORGE platform-neutral where possible while preserving Codex and Claude
   as existing first-class direct targets.
9. Reduce token waste by allowing agents to fetch compact, relevant guidance
   instead of relying on a large one-size-fits-all prompt.
10. Preserve all existing governance, authority, security, exact-byte,
   compatibility, archive, and acceptance boundaries.
11. Capture unclear owner-experience questions during testing so future FORGE
    changes are driven by observed friction rather than assumptions.

## Non-Goals

- Do not turn FORGE into a general-purpose project manager.
- Do not make FORGE itself a chatbot.
- Do not remove owner-only gates or weaken command-preview ceremony.
- Do not treat direct workspace agents as authenticated owners.
- Do not make all questions rigidly mandatory for every project.
- Do not implement profile switching after initiative creation in the first
  slice.
- Do not hardcode deep domain curricula for games, web apps, AI apps, research
  methods, or other specific fields in the first slice.
- Do not require third-party agent adapters before manual/direct use.
- Do not make provider success equivalent to claim, check, evidence,
  verification, or owner acceptance.
- Do not grant packs authority to register arbitrary executable adapters or
  command arguments.

## Recommended Initiative Objective

Use this as a starting point for the governed initiative objective:

```text
Design and implement a beginner-centered, profile-aware FORGE collaboration and
learning layer for direct workspace agents, including universal starter prompts,
pack-level interview and learning guidance, phase-explicit workflow guidance,
collaborative labor maps, profile-specific behavior, platform-neutral
manual-agent guidance, documentation, and tests, while preserving existing
governance authority and owner-gate semantics.
```

## Recommended Bounded Scope

Include:

- protocol updates for collaboration style, learning goals, question cadence,
  phase playback, and task delegation;
- conversational teacher contract updates for guided and mentored modes;
- bundled pack data additions for software and research interview and learning
  guidance;
- workflow-step guidance additions for phase labels, owner/agent/either tasks,
  owner-only gates, and phase done signals;
- profile-specific rendering rules for `minimal`, `standard`, `guided`, and
  `mentored`;
- profile-selection interview prompts for learning style, experience level, and
  desired project participation;
- requirements that open-ended questions include examples or answer choices when
  the owner may be a beginner;
- universal, Codex, Claude, and manual starter prompts;
- read-only CLI helpers if they fit the implementation budget;
- docs and examples that show the intended conversation;
- tests for schema compatibility, pack validation, CLI output, profile behavior,
  prompt discoverability, and no authority drift.

Exclude:

- hosted or multi-user operation;
- third-party adapter plugin ABI;
- switching an active initiative from one explanation profile to another;
- comprehensive domain-specific curricula or resource catalogs;
- public package publication or release automation;
- changing old archives or rewriting historical records;
- automatic owner acceptance;
- automatic installation from the network without explicit owner authorization;
- broad agent runtime discovery beyond existing bounded adapter diagnostics.
- fully integrated conversational workflow commands beyond starter/interview/
  step guidance; record those as future work after the first behavior is tested.

### Scope-Control Warning

The first implementation slice should not try to solve every teaching,
curriculum, task-management, and CLI-workflow problem at once. The priority is
to make the behavioral contract real: starter prompts, profile semantics,
conversational interview rules, phase guidance, collaboration task maps, and
tests that prove those behaviors do not weaken governance.

Defer richer `forge guide ...` workflows, profile switching, deep domain
curricula, domain resource catalogs, broad task-management features, and new
third-party adapter support until dogfooding shows the exact shape needed. If an
implementation choice starts expanding beyond the selected behavioral contract,
record it as future work rather than absorbing it into the first slice.

## Design Principles

### FORGE Guides; Agents Converse and Teach

FORGE should supply compact, authoritative guidance. Agents should adapt that
guidance to the owner, project, profile, and stated learning goals. In guided
and mentored modes, the agent should teach the project domain as work happens,
not merely explain FORGE mechanics.

### Required Coverage, Flexible Conversation

FORGE should define required coverage areas and examples, not force a fixed
script. Agents should ask small batches of questions, summarize what was learned,
and avoid making the owner repeat information already supplied.

The interview should also identify the owner's experience level and learning
preferences when the selected profile implies teaching. For example, a student
building a first game may need concepts like the game loop, input handling,
rendering, state, collision, and assets explained as part of the work plan.

Open-ended beginner questions should usually include brief examples. For
example, instead of asking only "Who should the game target?", an agent should
ask "Who is this game for? For example: young kids, casual mobile players,
friends at a party, people who like puzzle games, or just you while learning."
Simple yes/no or obvious factual questions do not need examples.

### Conversational Teacher Experience

Guided and mentored mode should feel like a natural teacher-led project
conversation. The owner should be able to start with an ordinary statement such
as "I want to build a game but I do not know where to start." The agent should
respond conversationally, gather context, teach the relevant project concepts,
and translate the agreed direction into FORGE mechanics in the background.

The agent should not present the owner with a large form, rigid questionnaire,
or command ceremony before the owner understands the project phase. FORGE
terminology should be introduced only when it helps the owner make or review a
decision.

For beginner/open-ended questions, use this pattern:

1. Ask the question in ordinary language.
2. Give two to four short examples when the answer may not be obvious.
3. Briefly explain why the answer matters when useful.
4. Accept short, partial, or "I do not know yet" answers.
5. Summarize what was learned.
6. Identify whether the uncertainty can remain out of scope or must be resolved
   before the next gate.

Guided and mentored teaching should use this loop:

1. Explain the concept.
2. Connect it to the owner's project.
3. Ask whether the owner wants resources, explanations, practice tasks, worked
   examples, or some mix when the preference is unclear.
4. Offer a small task, decision, example, explanation, or resource.
5. Ask a brief understanding check when useful.

Each phase should open with:

- where the project is now;
- what the phase is trying to build, learn, or decide;
- what the owner does;
- what the agent does; and
- which owner-only gate, if any, may appear later.

Each phase should close with:

- what changed;
- what the owner learned or practiced in guided and mentored modes;
- what remains uncertain;
- what evidence or review exists;
- what FORGE did or did not record; and
- the next collaboration step.

This is a conversation contract, not a change to governance. The agent may be
warm and educational, but must still preserve scope, authority, claims, checks,
evidence, verification, acceptance, and owner gates as separate facts.

### Distinct Phase Experience

Every active workflow step should be explainable as a phase with:

- phase name;
- purpose;
- owner tasks;
- agent tasks;
- either-party tasks;
- owner-only gates;
- open questions;
- done signal;
- likely next phase.

### Delegation Without Authority Confusion

The owner may ask the agent to operate a displayed command, but authority still
comes from the owner. The guidance must distinguish:

- routine agent work;
- owner tasks that teach project skills or preserve human judgment;
- either-party tasks the owner may delegate;
- owner-only authority gates that require explicit command preview and approval.

In mentored mode, the agent should not automatically perform every task it can
perform. It should identify which tasks are useful for the owner to attempt for
learning, explain why, and offer an explicit delegation option when appropriate.
Estimated learning value may be included where helpful, but should not become a
required scoring system in the first slice.

When a learning-support preference is unclear, the agent should ask rather than
guess. For example, ask whether the owner wants links/resources, an explanation
in the chat, a small exercise, a worked example, or a combination. During owner
testing, recurring unclear preferences should be captured as candidate FORGE
improvements.

### Profile Learning Depth, Same Governance

Profiles change collaboration style and learning depth, not authority:

| Profile | Expected behavior |
|---|---|
| `minimal` | Optimize for low token use and fast execution. Ask only scope-, safety-, and correctness-critical questions. Show terse phase, output, blocker, and next-action guidance. |
| `standard` | Optimize for clear collaboration. Explain what is happening, what the owner should review, task ownership, and the next action without turning the work into a lesson plan. |
| `guided` | Optimize for better decisions and contextual project learning. Explain options, tradeoffs, vocabulary, architecture, research methods, or domain concepts as they affect decisions. |
| `mentored` | Optimize for learning by building. Create a project-specific learning path, assign useful owner practice tasks, recommend resources, explain concepts, check understanding when useful, and adapt the work plan to the owner's skill level. |

Example: for a computer science student building a first game, `minimal` might
move quickly through the game loop, input, rendering, collision, and scoring.
`mentored` should treat those as learning milestones, explain each concept,
recommend resources or exercises, and decide with the owner which parts the
student should attempt versus delegate to the agent.

For the first implementation slice, the owner selects the profile at initiative
creation. Changing profile mid-initiative can be revisited later after the
initial profile behaviors are proven in owner testing.

## Proposed Data Model Changes

Prefer additive, default-empty fields so old locks and records continue to load.
Exact names can change during design, but the implementation should support the
following concepts.

### Pack-Level Interview Guidance

Add guidance that can be inspected before trusting or creating an initiative:

```yaml
interview_guidance:
  vision:
    purpose: Understand the human goal, intended users, and learning goals.
    questions:
      - What are you trying to build or learn?
      - Who is this for?
      - What would make the first version useful?
      - What do you want to understand better by the end of this project?
    must_answer_before_create:
      - intended_users
      - first_useful_outcome
  first_milestone:
    purpose: Bound the first initiative.
    questions:
      - What is the smallest valuable milestone?
      - What should be explicitly out of scope?
      - What does done look like in plain language?
  risks_and_constraints:
    purpose: Avoid unsafe or wasteful scope.
    questions:
      - Are there deadlines, tools, budget, privacy, or platform limits?
      - What would make you pause, abandon, or restart?
  learning_path:
    purpose: Shape guided and mentored work around the owner's skill level.
    questions:
      - What experience do you already have with this kind of work?
      - What learning style do you prefer: brief explanations, examples, resources, small exercises, or trying first and then reviewing?
      - Which parts do you want to do yourself for practice?
      - Would you prefer resources, explanations, exercises, or worked examples?
```

### Step-Level Phase Guidance

Add guidance to workflow steps:

```yaml
phase_guidance:
  label: Define the first milestone
  owner_tasks:
    - Decide intended users and first useful outcome.
    - Identify exclusions that must stay out of scope.
    - In guided or mentored mode, choose what you want to learn or practice in this phase.
  agent_tasks:
    - Turn owner answers into a bounded proposal.
    - Identify missing context and risks.
    - Explain relevant project concepts at the selected profile depth.
    - End substantial explanations with a brief understanding check when useful.
  either_tasks:
    - Gather examples, notes, screenshots, or reference links.
    - Find learning resources or comparable projects.
  owner_only_gates:
    - Authorize exact initialization, pack trust, creation, acceptance, scope amendment, and terminal commands when applicable.
  done_signal: The owner confirms the playback and all material open questions are either answered or explicitly accepted as uncertainty.
```

### Profile Rendering Guidance

Add rendering guidance either globally or per pack:

```yaml
profile_guidance:
  minimal:
    question_batch_size: 1
    explanation_depth: terse
    learning_depth: none_by_default
  standard:
    question_batch_size: 3
    explanation_depth: clear
    learning_depth: light_context
  guided:
    question_batch_size: 3
    explanation_depth: reasoning
    learning_depth: decision_support
    require_tradeoffs: true
  mentored:
    question_batch_size: 2
    explanation_depth: teaching
    learning_depth: learning_by_building
    require_project_map: true
    require_phase_walkthrough: true
    require_learning_path: true
    require_owner_practice_tasks: true
```

## Proposed CLI Additions

Start with docs and protocol if implementation time is limited. Add read-only CLI
helpers when the schema shape is settled.

### `forge agent starter`

Print current starter prompts without requiring an initialized repository.

Examples:

```console
forge agent starter --target universal
forge agent starter --target codex
forge agent starter --target claude
forge agent starter --target manual
forge agent starter --target universal --profile mentored
```

Requirements:

- read-only;
- works before `forge init`;
- identifies the installed FORGE protocol version;
- points to `forge agent protocol`;
- distinguishes installed CLI path from GitHub source fallback;
- prints no secrets or local state;
- supports compact and full output if useful.

### `forge pack interview`

Inspect pack interview guidance without trusting the pack or creating state.

Examples:

```console
forge pack interview software-basic --profile mentored
forge pack interview research-basic --profile guided
```

Requirements:

- read-only;
- works for bundled, validated pack data;
- does not create state or imply pack trust;
- shows question groups, required coverage, learning prompts, and
  profile-specific collaboration guidance;
- keeps output bounded.

### `forge step guide`

Inspect active-step phase guidance after initiative creation.

Examples:

```console
forge step guide
forge step guide --profile mentored
```

Requirements:

- read-only;
- validates active state;
- reports phase label, tasks by party, done signal, owner-only gates, blockers,
  and next legal actions;
- never records claims, checks, evidence, verification, or acceptance.

## Protocol Updates

Update `src/forge/resources/agent-protocol-1.3.0.md` or introduce a new protocol
version. The protocol should require direct workspace agents to:

1. Identify FORGE from the installed CLI or the official repository URL supplied
   by the owner.
2. Run `forge --version` and `forge agent protocol` when available.
3. If unavailable, read the owner-supplied FORGE repository docs before
   suggesting installation.
4. Ask for existing documents before broad questions.
5. Ask questions in small batches appropriate to the profile.
6. In guided and mentored modes, ask what the owner wants to learn about the
   project domain or craft.
7. Explain why question batches matter in guided and mentored modes.
8. Build and maintain a coverage playback under the existing six headings.
9. Produce a collaborative task map during bootstrap and at step transitions.
10. Present each workflow step as a distinct phase.
11. Distinguish owner tasks, agent tasks, either-party tasks, and owner-only
    authority gates.
12. Identify owner learning tasks separately from routine owner review tasks.
13. Identify questions that must be answered now versus uncertainties that can
    be accepted out of scope.
14. After initiative creation, present a beginner-readable project map in
    guided and mentored modes.
15. In mentored mode, present a project-specific learning path and recommend
    resources or exercises when useful.
16. In guided and mentored modes, end substantial explanations with a brief
    understanding check, such as "Does that make sense?".
17. Use the conversational teacher pattern for beginner/open-ended questions and
    phase transitions.
18. De-emphasize FORGE terminology until it is needed for a decision, receipt,
    or owner-only gate.
19. Preserve receipt quoting rules and owner-only command-preview ceremony.

## Documentation Updates

Update or add:

- `README.md`: add a visible "Fresh agent starter prompt" link near the
  workspace-agent section.
- `docs/README.md`: add the starter prompt guide to the audience map.
- `docs/agent-starter-prompts.md`: prompt variants for universal, short,
  Codex, Claude, manual, installed CLI, and GitHub-only cases.
- `docs/conversational-walkthroughs.md`: add a phase-explicit beginner
  walkthrough and a human/agent task map example.
- `docs/quickstart.md`: explain that the owner can hand a fresh agent the
  universal prompt.
- `docs/agent-context.md`: clarify platform-neutral manual/direct use versus
  first-class adapters.
- `docs/pack-author-guide.md`: document interview and phase guidance fields
  once they exist.
- `docs/workflows.md`: document phase guidance once implemented.
- `docs/adapters.md` and `docs/adapter-author-guide.md`: clarify that adapter
  support is distinct from manual/direct prompt-based use.

## Suggested Implementation Phases

### Phase 1: Design and Lock Scope

- Draft the exact schema additions.
- Decide whether this requires a new protocol version.
- Keep profile selection at initiative creation; explicitly defer profile
  switching.
- Decide whether CLI helpers are in the first implementation slice or deferred.
- Write one golden beginner walkthrough for `software-basic`.
- Write one golden research walkthrough for `research-basic`.
- Include examples after open-ended beginner questions in the walkthroughs.
- Include one walkthrough that starts from a natural beginner prompt, such as
  "I want to build a game but I do not know where to start."
- Confirm compatibility strategy for old locks and pack digests.

Deliverables:

- ADR if architecture, schema, compatibility, or authority semantics change.
- Updated bounded scope and definition of done.

### Phase 2: Starter Prompts and Docs

- Add `docs/agent-starter-prompts.md`.
- Add root README and docs index links.
- Add tests that starter docs mention the official repository, `forge --version`,
  `forge agent protocol`, document-first interview, task split, phase playback,
  and owner-only gate ceremony.

Deliverables:

- Prompt documentation that can be used before any code changes land.

### Phase 3: Pack Guidance Schema

- Add additive contract fields for interview guidance and phase guidance.
- Update schema export and compatibility fixtures.
- Update bundled `software-basic` and `research-basic` packs.
- Add validation tests for default-empty old packs and new guidance-bearing
  packs.

Deliverables:

- Validated guidance data available from bundled packs.

### Phase 4: Protocol and Context Rendering

- Update agent protocol to require profile-aware collaboration and learning
  guidance.
- Include active-step phase guidance in canonical context where appropriate and
  safe.
- Ensure context remains allowlist-based and does not include unrelated files or
  content.
- Preserve current leakage boundaries.

Deliverables:

- Agents receiving context can render distinct phases and task maps.

### Phase 5: Read-Only CLI Helpers

- Implement `forge agent starter` if approved.
- Implement `forge pack interview` if approved.
- Implement `forge step guide` if approved.
- Keep all helpers read-only unless later explicitly scoped otherwise.

Deliverables:

- Fresh agents can fetch compact guidance instead of consuming large docs.

### Future Phase: Natural Workflow Commands

After the first collaboration and learning behavior is dogfooded, consider
adding commands that make the conversational teacher model feel native to
FORGE's ordinary workflow. Candidate commands or command families:

- `forge agent starter` as the stable fresh-agent entry point;
- `forge guide start` to render the selected profile, interview posture,
  learning preferences, and first-phase conversation shape;
- `forge guide phase` to render the current phase opening, owner/agent/either
  task map, learning options, owner-only gates, and next collaboration step;
- `forge guide reflect` to help agents close a phase by summarizing what
  changed, what was learned, what remains uncertain, and what FORGE recorded.

These commands should remain read-only unless a later governed design explicitly
authorizes mutations. They should be considered future work, not required for the
first implementation slice.

### Phase 6: Walkthroughs and Dogfood

- Dogfood with a fresh-agent scenario:
  "Use FORGE from this GitHub URL, install if needed, start a beginner software
  project, and walk me through it."
- Dogfood with an installed-CLI scenario:
  "This repository uses FORGE. Resume and tell me what phase we are in."
- Dogfood with a non-Codex/non-Claude capable agent using universal/manual
  guidance.
- During each dogfood run, capture unclear user-experience questions, missing
  examples, confusing wording, and moments where the agent guessed instead of
  asking.

Deliverables:

- Friction report.
- Residual-risk report.
- Future-improvement notes for unclear or repeated owner-experience friction.
- Any necessary follow-up tasks.

## Testing Strategy

Add focused tests before broad suite runs.

Suggested coverage:

- old workflow locks and old packs load with default-empty guidance;
- new guidance fields are included in schema exports;
- invalid guidance is rejected by pack validation;
- pack digests include guidance data where appropriate;
- `minimal`, `standard`, `guided`, and `mentored` render different
  collaboration and learning levels without changing governance authority;
- starter prompt output works outside initialized repositories;
- prompt docs mention the official repo and installed CLI path;
- no helper command writes `.forge/` or records journal events;
- context generation remains allowlist-based;
- owner-only gates are still labeled owner-only;
- Codex and Claude managed references still preserve owner-authored bytes
  outside FORGE markers;
- manual/direct platform-neutral guidance does not imply first-class adapter
  support;
- adapter execution boundaries remain unchanged.

## Acceptance Criteria

The implementation is ready for owner review when:

- a new user can hand a fresh agent one starter prompt and the agent correctly
  routes itself to FORGE rather than another `forge` tool;
- before initialization, the agent performs state detection, asks for documents,
  conducts a beginner-readable interview, and plays back a first milestone;
- each workflow step can be explained as a distinct phase;
- the task map separates owner, agent, either-party, and owner-only gate work;
- `guided` mode helps the owner understand project choices and tradeoffs;
- `mentored` mode feels like learning by building, including a learning path,
  owner practice tasks, explanations, and useful resources;
- guided and mentored modes gather information conversationally rather than as a
  form or checklist;
- guided and mentored explanations include brief understanding checks when
  useful;
- guided and mentored agents ask whether the owner wants resources,
  explanations, practice tasks, worked examples, or a mix when that preference is
  unclear;
- open-ended beginner questions include examples most of the time;
- phase openings and closings make the workflow feel distinct and teachable;
- profile switching is documented as deferred rather than partially supported;
- `minimal` mode remains compact;
- other capable agents can participate through universal/manual guidance;
- Codex and Claude still work through existing managed references and adapters;
- all owner-only authority boundaries are preserved; and
- tests prove no governance record, acceptance, check, evidence, adapter success,
  or command execution is conflated with any other lifecycle fact.

## Risks and Open Questions

- Too much guidance may increase token use. Mitigation: make guidance inspectable
  through compact read-only commands and profile-specific rendering.
- Too many questions may feel bureaucratic. Mitigation: require small batches and
  distinguish must-answer-now from can-remain-uncertain.
- Project-domain teaching may sprawl into an unbounded curriculum. Mitigation:
  require project-specific learning paths tied to the active phase, not generic
  full courses.
- Hardcoded domain concepts may over-expand the first initiative. Mitigation:
  leave domain-specific starter concepts to the agent at runtime for now, while
  documenting the future option of pack- or template-level domain guidance.
- Pack guidance may bloat pack digests and fixtures. Mitigation: additive fields,
  focused fixture updates, and clear compatibility tests.
- Platform-neutral language may overpromise support. Mitigation: clearly separate
  manual/direct use from registered adapter support.
- Agents may still skip protocol requirements. Mitigation: put starter prompts in
  easy-to-find docs and make the protocol explicit about fresh-agent routing.
- The right integrated FORGE command shape may not be obvious before dogfooding.
  Mitigation: note natural workflow commands as future work and use testing
  friction to decide which commands should exist.

## Future Work

- Add natural workflow commands that make starter guidance, phase openings,
  phase closings, learning preferences, and collaboration task maps easy for
  agents to fetch during ordinary work.
- Revisit profile switching after initiative creation once the initial
  profile-at-start behavior has been tested.
- Consider optional domain-specific concept packs or templates after runtime
  agent-generated domain guidance has been tested.
- Convert recurring owner-experience friction into concrete protocol, pack,
  prompt, or CLI improvements.
