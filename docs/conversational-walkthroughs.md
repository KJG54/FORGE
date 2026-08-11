# Conversational Walkthroughs

FORGE is designed to sit behind an ordinary conversation with a workspace agent. You explain the
project and make consequential decisions; the agent translates the agreed work into exact FORGE
operations, performs routine worker actions, and reports durable receipts in plain language.

These walkthroughs are illustrative. Names, paths, identifiers, packs, workflow steps, and exact
commands depend on the repository and the preview FORGE produces at the time. A placeholder such
as `<initiative-id>` is not a command to copy blindly. The agent must display the real command and
its consequences before an owner gate, and the owner must authorize that exact command.

## Walkthrough 1: Start a new project

**Owner:** I want to build a small family recipe manager. I need recipes, ingredient search, and a
simple way to export a backup. I want to start locally and decide about hosting later.

**Agent:** I will first read the installed FORGE agent protocol and check whether this folder is
already governed. I will not initialize anything yet.

The agent performs those read-only checks. In a new folder, it then conducts a document-first
interview under six coverage headings:

1. **Product vision and intended users:** What should the project become, and who is it for?
2. **First milestone objective and definition of done:** What bounded outcome comes first, and
   how will the owner recognize it as complete?
3. **Constraints, exclusions, risks, and abandonment conditions:** What boundaries apply, what is
   deferred, and what would justify stopping?
4. **Existing assets, predecessor work, and reusable exact revisions:** Which supplied documents,
   repositories, archives, or accepted revisions can ground the work?
5. **Standing labor split:** What belongs to the owner, workspace agent, FORGE, and any external
   contributors?
6. **Unresolved material questions:** Which unanswered questions could still change scope or safe
   execution?

**Agent:** Here is my coverage playback: the first initiative will deliver a local recipe manager
for you, with recipe entry, ingredient search, and an exportable backup. Hosting, shared accounts,
and mobile distribution are excluded. We will preserve requirements and a verification report,
run the agreed automated checks, and leave usability and final acceptance to you. The repository
will retain enough context for a fresh agent to resume. Is that accurate?

**Owner:** Yes. Keep hosting out of this initiative.

Only after that confirmation does the agent prepare the owner gates. It shows the exact commands,
affected repository, and consequences for initialization, pack trust, and initiative creation.

**Agent:** The next command initializes FORGE records in this repository. It does not create the
initiative or accept any work. Here is the exact command and consequence. Do you authorize it once?

**Owner:** I authorize that exact command once.

The agent executes it once, reports the receipt, and repeats the same preview-and-authorization
ceremony for pack trust and initiative creation. It does not treat the owner's approval of one
command as approval of later commands.

## Walkthrough 2: Resume and complete routine work

**Owner:** Continue the recipe manager. Where did we leave off?

**Agent:** I will inspect FORGE's current status and recap before changing anything.

**Agent:** The repository is healthy. The active initiative is implementing ingredient search.
The current step is ready to begin, there are no blockers, and its required output is the
implementation artifact. The scratchpad contains an ungoverned note suggesting partial-word
matching; I will treat it as a reminder, not as approved scope. Shall I continue with the accepted
plan?

**Owner:** Yes, continue with the accepted plan.

The agent begins the work using the permitted worker attribution, edits the project, registers the
exact artifact revision, and runs the agreed checks. Routine worker actions do not borrow owner
authority merely because the owner said to continue.

**Agent:** Implementation is complete for the registered revision. The unit and integration checks
passed, and I recorded their exact results. That establishes a worker claim and check evidence; it
does not establish FORGE verification or your acceptance. The next ready action is independent
verification.

The lifecycle remains intentionally separated:

```text
worker claim -> check -> evidence -> FORGE verification -> owner acceptance
```

If a later verifier records a truthful verification, the agent can then present the exact owner
acceptance command and its consequences. The owner may accept, reject, request more evidence, or
stop. Silence and green tests are never converted into acceptance.

## Walkthrough 3: Recover from a refusal or scope change

**Owner:** Add cloud synchronization too, then finish this step.

**Agent:** Cloud synchronization is outside the accepted scope, and the active implementation run
still targets the local-only revision. I will not silently add it or claim the current step is
complete. FORGE also reports that the required `requirements` artifact is missing, so completion
is legal in the state machine but not ready now.

The agent explains both facts:

- **Legal** means the workflow contains that transition from the current state.
- **Ready** means its current prerequisites are satisfied and the command can truthfully run now.

**Agent:** We have two honest options. We can keep cloud synchronization deferred, register the
missing requirements artifact, and complete the current local-only step; or we can change the
initiative scope. A scope change affecting active work requires cancelling the current agent-owned
run first, then an explicit owner-authorized scope amendment. I recommend finishing the bounded
local milestone unless cloud synchronization is now essential.

**Owner:** It is essential. Rework the scope.

**Agent:** I can cancel my active run as a routine agent action if the installed protocol permits
it. Cancellation preserves the history and makes no completion claim. After that, I will show you
the exact scope-amendment command, the requirements it changes, and the work it will invalidate.

The agent cancels only its own active run, reports the cancellation record, and displays the real
scope-amendment command. It does not execute that owner gate until the owner authorizes the exact
command once. After amendment, superseded artifacts, claims, checks, evidence, verification, or
acceptance remain visible as stale history rather than disappearing.

**Owner:** I authorize the displayed scope amendment once.

**Agent:** The amendment was recorded. The affected implementation work is now invalidated and
ready for a truthful rework run. Nothing was accepted or closed by that amendment.

This refusal-and-recovery path is deliberate: FORGE makes the cheapest unsafe shortcut harder than
preserving an honest account of what changed.

## Walkthrough 4: A beginner starting a phase, in guided mode

This is what a phase opening sounds like when the owner is new to the domain and the initiative
uses the `guided` profile. The owner opened with something vague.

**Owner:** I want to build a game but I don't know where to start.

**Agent:** That's a fine place to start. Before any FORGE mechanics, two questions.

Who is this for? For example: just you while learning, friends at a party, or people who already
play a lot of puzzle games. And what would make a first version feel worth playing — even if it's
one screen and one mechanic?

**Owner:** Just me, learning. Something where you dodge things and get a score.

**Agent:** Good — that bounds it usefully. Here's where we are and what this phase is for.

**Phase: Discover what to build and why.** We're turning "dodge things, get a score" into an
objective, constraints, and requirements. That gives later planning and verification a stable
target. Nothing is accepted yet.

| Who | Work in this phase |
|---|---|
| You | Decide what "getting hit" and "winning" mean; name what's out of scope for v1 |
| Me | Turn your answers into a bounded objective and requirements; name open questions |
| Either | Find two or three games that do the mechanic well, to point at |
| You alone | Accepting the discovery outputs — an owner-only gate, later |

Concepts worth understanding here, since you're learning: a game loop, input handling, collision
detection, and game state. You don't need to implement any of them yet. Want me to explain them
now, point you at a good tutorial, or leave them until we hit each one?

**Owner:** Explain them when we get there. What's out of scope?

**Agent:** My suggestion: no menus, no sound, no saved high scores, no multiple levels. One screen,
one mechanic, a score that resets. Those exclusions are what make a first milestone finishable.

Two questions must be answered before we can create the initiative — who it's for, and what a
first useful version does. You've answered both. Everything else can stay open and be recorded as
accepted uncertainty.

Here's the phase closing, once discovery is written up:

**Agent:** What changed: the objective and requirements now exist as a draft. Still uncertain: how
hard the game should be, which you said you'd decide by playing it. Evidence: none yet — nothing
has been checked. What FORGE recorded: nothing. This is still conversation.

Next step is yours: read the draft, and if it matches, I'll show you the exact
`forge create` command with its consequences before anything is recorded.

Two things worth noticing. The agent gave examples with the open-ended question instead of asking
"who is your target audience?" cold. And it kept "what FORGE recorded" as a separate line from
"what changed" — because at that moment the honest answer was *nothing*.

The same phase under `minimal` would be three sentences and no teaching. The governance is
identical either way.

## What to say to an agent

You can start without knowing any FORGE commands:

> This project uses FORGE. Read and follow `forge agent protocol` before doing project work. Help
> me describe the project in ordinary language, conduct the required document-first interview,
> and explain each consequential owner gate before asking me to authorize its exact command.

For an existing project, a shorter prompt is enough:

> This repository uses FORGE. Read the installed protocol, inspect its health, status, and recap,
> then tell me where the initiative stands, what is blocked, and what is ready now. Do not perform
> owner-only actions without displaying the exact command and receiving my explicit authorization.

See [Your first FORGE project](quickstart.md) for the complete first-project guide and the
[user guide](user-guide/README.md) for command and lifecycle reference.
