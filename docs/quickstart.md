# Your first FORGE project

This guide walks you through starting, running, and finishing a FORGE-governed project from
nothing, working with an AI workspace agent (Claude Code or Codex). No prior FORGE knowledge is
assumed. Plain-language definitions for every term used here are in the
[glossary](glossary.md).

FORGE's job in one sentence: it keeps a trustworthy, append-only record of what was decided,
who authorized it, what was claimed, what was checked, and what you actually accepted — so that
neither you nor your agent has to reconstruct that from chat history.

## What you need

- Python 3.12 or newer, and Git.
- A workspace agent: the Claude Code or Codex app, opened in a project folder (or a cloud
  workspace session).
- FORGE installed — once per machine or container:

```console
pip install git+https://github.com/KJG54/FORGE.git@main
```

Check it worked: `forge --version` should print a version, and `forge agent protocol` should
print the workspace-agent protocol. You never need to read that protocol yourself — it is the
agent's instruction sheet.

## Step 1 — Decide where the project lives

A FORGE project's records live inside its repository, so the repository needs a home that
outlasts the session. Pick one deliberately:

| Where you work | Durable home | What to do |
|---|---|---|
| On your computer | The project folder itself | Create a folder (for example `C:\Projects\recipe-box`), open your agent in it |
| Cloud workspace session | A private remote repository | Create an empty private GitHub repository first, open the session on it |
| Quick experiment | None — declared throwaway | A cloud session with no remote is fine; just say it is a test |

The trap to avoid: cloud containers are ephemeral. A project built there with no remote —
governance records and all — is deleted when the container is reclaimed. If you want it to
survive, the remote must exist and be pushed to.

## Step 2 — Tell your agent what you want

Open the agent in the project folder (or cloud repository) and describe the project naturally:

> I want to build a recipe manager for my family, using FORGE. Backtest ideas welcome, but keep
> it simple.

A correctly behaving agent will, before touching anything:

1. run `forge agent protocol` and follow it;
2. check the state of the folder (empty? already a FORGE project? someone else's repository?);
3. ask whether you have **existing documents** — notes, requirements, sketches, a plan — and read
   what you point it at before asking broad questions; and
4. interview you for what the documents do not cover.

The interview works through six areas: what the product is and who it is for; what the first
milestone is and what "done" means; constraints and things explicitly out of scope; anything that
already exists and can be reused; who does what (you, the agent, FORGE); and open questions that
still need answers. Short answers are fine. "I don't know yet" is a legitimate answer — the agent
records the uncertainty instead of guessing.

## Step 3 — Confirm the playback, then the two gates

When the interview covers enough, the agent plays back one proposal: vision, first-milestone
objective, bounded scope, exclusions, definition of done, and which workflow pack it suggests
(for software projects, typically `software-basic`: discover → plan → execute → verify → review →
close). Read it. Correct anything. Your approval of the playback approves *only* the text you
read — it does not let the agent start creating things silently.

Then come the owner gates. The agent must show you exact commands and wait:

```console
forge init <folder> --owner-name "Your Name"
forge create "<objective>" --scope "<bounded scope>" --pack software-basic --trust-pack-data
```

You can run them yourself, or tell the agent "run it" — either way, nothing consequential happens
without your word. `init` writes FORGE's configuration into the repository; `create` opens the
initiative and locks the workflow immutably. From this point the project is governed.

## Step 4 — Daily work, and how to read a receipt

Day to day, you steer in conversation and the agent handles the mechanics: it begins steps,
writes and registers artifacts, records claims and checks, and asks you for the decisions that
are yours. Every governed change prints a canonical receipt:

```text
Recorded -> step-transitioned (initiative=...; step_id=discover; ...) [sequence 2-2]
Means    -> ...; step=discover:in_progress; blockers=none; legal_actions=complete:discover
```

`Recorded` and `Means` come from FORGE and state what was committed and what is now possible.
If the agent adds `Read ->` or `Next ->` lines, those are its own fallible judgment and plan —
useful, but not record. When the agent finishes a step's outputs, it records a **claim** — and a
claim is just "the agent says it did the work." Checks test it, evidence preserves it, FORGE
verifies the records line up, and then the step waits for the only word that advances it:

```console
forge acceptance record <step-id> --scope "<exactly what you accept>"
```

That command is yours. Run it (or explicitly direct it) only when you are satisfied.

## Step 5 — Leaving and coming back

Stop whenever you want — there is no farewell ceremony. When you come back, in a fresh session:

```console
forge recap
```

The first part is derived from the validated record: where the project stands and what is legally
possible next. The second part is the agent's local scratchpad — unofficial working notes, marked
as such. For deliberate long pauses there is `forge pause --reason "..."` and `forge resume`,
which also checks whether files drifted while you were away.

If anything ever looks wrong, `forge doctor` diagnoses without changing anything, and the
[troubleshooting guide](troubleshooting.md) maps every error to a procedure.

## Step 6 — Finishing

When every step of the workflow is accepted, closing the initiative creates a hardened,
immutable archive:

```console
forge close --summary "<what was delivered>"
```

If the project stops being worth finishing, `forge abandon` records an honest terminal archive
instead — abandonment never pretends unfinished work was accepted. Either way the archive is
inspectable forever (`forge status --archive <id>`), and a future initiative can build on it as a
**successor**, referencing the archive and reusing exact artifact revisions without inheriting
any unearned acceptance.

## Where to go next

- [User guide](user-guide/README.md) — the same journey in full detail.
- [Glossary](glossary.md) — every term, defined once, used consistently.
- [Constitution](constitution.md) — the rules FORGE holds itself to.
- [Documentation index](README.md) — everything else, routed by audience.
