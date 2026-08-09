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
