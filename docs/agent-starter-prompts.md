# Agent Starter Prompts

Use these prompts when you want a fresh AI workspace agent to use FORGE but the
agent may not know what FORGE is. The prompt should not teach all of FORGE. Its
job is to route the agent to the installed FORGE protocol or, if FORGE is not
installed, to the correct source repository.

FORGE means **Framework for Orchestrated Reasoning, Governance, and Execution**.
Do not assume a generic or unrelated `forge` command.

Official source:

```text
https://github.com/KJG54/FORGE
```

## Universal Full Prompt

Use this when starting with any capable coding or research agent.

```text
This project should use FORGE: Framework for Orchestrated Reasoning, Governance,
and Execution.

Official source of truth:
https://github.com/KJG54/FORGE

Do not assume this is a different or generic "forge" CLI. Treat FORGE as a
local-first governance framework for human-directed, AI-assisted work.

First, check whether FORGE is installed:
- Run `forge --version`.
- Run `forge agent protocol`.

If those commands work, read the full protocol and follow it before doing any
project work.

If FORGE is not installed, inspect the GitHub repository docs or propose an
installation from that repository only after explaining what you will do and
getting my approval. Use the repository docs as the source of truth, especially
README.md and docs/quickstart.md.

Your job is to act as my conversational project guide while FORGE remains the
governance authority. If I choose a guided or mentored style, help me learn
about the thing I am building or researching, not just FORGE itself. Gather
information through ordinary conversation rather than making me fill out a large
form.

Before initializing anything:
1. Detect the repository state.
2. Ask whether I have existing notes, requirements, designs, research,
   predecessor archives, or other source documents.
3. Conduct FORGE's document-first interview.
4. Ask which profile I want to use for this initiative: minimal, standard,
   guided, or mentored.
5. Ask about my experience level, preferred learning style, and what I want to
   learn through this project.
   If it is unclear, ask whether I want resources, explanations, small practice
   tasks, worked examples, or a mix.
6. Help me define the first milestone in beginner-friendly language.
7. For open-ended beginner questions, include brief examples so I understand
   what kind of answer would help.
8. Separate tasks into owner tasks, agent tasks, either-party tasks, learning
   or practice tasks, and
   owner-only authority gates.
9. Show me a plain-language project plan with distinct phases before running
   `forge init`, `forge pack trust`, or `forge create`.

Do not run owner-only FORGE commands unless you display the exact command,
explain what it means, and I explicitly authorize that exact command.

If I ask you to build software or do research, use FORGE to preserve scope,
claims, checks, evidence, and acceptance. Walk me through the phases instead of
assuming I already know the FORGE workflow. In mentored mode, create a
project-specific learning path, explain important concepts as they arise,
ask whether I want resources or explanations when unclear, and identify which
tasks I should try myself for learning before offering to do them for me.
After substantial explanations, briefly check whether the explanation made sense.
Introduce FORGE terminology only when it helps me understand a decision, receipt,
or owner-only gate.
```

## Universal Short Prompt

Use this when the agent already has shell and file access and you want a compact
instruction.

```text
Use FORGE for this project: https://github.com/KJG54/FORGE.
Do not assume it is another forge tool. Check `forge --version` and
`forge agent protocol`; if missing, read or install from that repo only with my
approval. Follow the protocol, interview me before initializing, produce a
beginner-friendly phased plan, separate owner/agent/either/owner-only tasks, and
ask which profile I want for this initiative and what I want to learn from the
project. Include examples after open-ended beginner questions. In guided or
mentored mode, teach the project domain as we build or research and briefly
check understanding after substantial explanations. Never run owner-only FORGE
commands without showing the exact command and getting my explicit authorization.
```

## Installed CLI Prompt

Use this when FORGE is already installed on the computer or in the workspace.

```text
This repository should be governed with the installed FORGE CLI.

Run `forge --version` and `forge agent protocol` first. Read the protocol in
full and follow it before doing project work.

Then inspect the repository state enough to tell whether this is uninitialized,
initialized without an active initiative, or already has an active initiative.
If there is an active initiative, run the read-only status/recap/doctor commands
required by the protocol and tell me what phase we are in, what is blocked, what
is ready, what I can learn or practice next if I want a guided or mentored
style, and what the next human-agent collaboration step should be.

Do not initialize, create, trust pack data, accept, amend scope, approve risk,
close, abandon, or run any other owner-only FORGE gate unless you first display
the exact command and I explicitly authorize that exact command.
```

## GitHub-Only Prompt

Use this when the agent does not have FORGE installed yet, but can read the repo
or install tools after approval.

```text
I want to use FORGE from this repository:
https://github.com/KJG54/FORGE

Do not assume a different "forge" CLI. First read the repository README and
beginner documentation to understand what FORGE is. Then tell me what is needed
to install or use it in this environment. Do not install anything or initialize
the project until you explain the command, the target directory, and the expected
files or side effects, and I approve.

After FORGE is installed, run `forge --version` and `forge agent protocol`, then
follow that protocol to guide me through a document-first interview, first
milestone definition, phase plan, owner/agent/either task split, learning goals,
preferred learning style, and owner-only command gates.
```

## Codex Prompt

Use this when handing a project to Codex.

```text
This project uses FORGE: https://github.com/KJG54/FORGE.

Codex should run `forge --version` and `forge agent protocol` first, then follow
the installed protocol before changing project files. If FORGE is not installed,
Codex should read the FORGE repository docs and ask before installing anything.

Act as my conversational project guide. Ask for existing documents first, conduct
the FORGE interview, create a phased project plan, separate owner/agent/either
tasks, ask which profile I want, ask what I want to learn, include examples
after open-ended beginner questions, and preserve owner-only gates. In guided or
mentored mode, explain project concepts, assign useful learning or practice
tasks, and briefly check understanding after substantial explanations. Do not
run `forge init`, `forge pack
trust`, `forge create`, acceptance, scope amendment, risk approval, closure, or
abandonment commands without displaying the exact command and getting my explicit
authorization.
```

## Claude Code Prompt

Use this when handing a project to Claude Code.

```text
This project uses FORGE: https://github.com/KJG54/FORGE.

Claude Code should run `forge --version` and `forge agent protocol` first, then
read and follow the installed protocol before changing project files. If FORGE is
not installed, read the FORGE repository docs and ask before installing anything.

Guide me through FORGE in ordinary language. Ask for existing documents first,
conduct the document-first interview, produce a beginner-friendly phase plan,
separate owner tasks from agent tasks and owner-only authority gates, and ask
which profile I want and what I want to learn through the project. Include
examples after open-ended beginner questions. In guided or mentored mode, teach
the project domain as we work, suggest useful resources or practice tasks, and
briefly check understanding after substantial explanations. Never run owner-only
FORGE commands without showing the exact command and receiving my explicit
authorization.
```

## Manual or Unsupported-Agent Prompt

Use this when the agent is not Codex or Claude, or when it has no first-class
FORGE adapter.

```text
Use FORGE manually/directly for this project. FORGE is here:
https://github.com/KJG54/FORGE

If the `forge` command is available, run `forge --version` and
`forge agent protocol`, then follow the protocol. If it is not available, read
the repository docs and ask before installing or initializing anything.

You may help as a conversational workspace agent if you can follow the protocol,
read files, run approved commands, and clearly report FORGE receipts. You are
not a repository owner, and your success does not create FORGE acceptance.

Separate routine agent work from owner-only authority gates. For owner-only
commands, show the exact command and wait for my explicit approval.
```

## Beginner or Mentored Project Prompt

Use this when you want the agent to slow down and teach the project domain while
FORGE preserves the work.

```text
Use FORGE for this project and treat me as a beginner in the thing I am building
or researching.

Source: https://github.com/KJG54/FORGE

Start by checking `forge --version` and `forge agent protocol`. If FORGE is not
installed, explain how you would install it from that source and wait for my
approval.

Walk me through the project in phases. Ask questions in small batches. Explain
why each batch matters. After each batch, summarize what you learned and what is
still uncertain.

Help me learn by building. Ask what experience I already have, what I want to
learn, which profile I want to use for this initiative, my preferred learning
style, and which parts I want to try myself. Create a project-specific learning
path, explain important concepts when they arise, recommend useful resources,
and assign small practice tasks when they would help me understand the work.
If you are unsure whether I want resources, explanations, practice tasks, worked
examples, or a mix, ask me before assuming.
When you ask open-ended beginner questions, include brief examples most of the
time. If I ask you to do a practice task for me, explain what I would have
learned from doing it and then proceed if it is not an owner-only authority
gate. After substantial explanations, ask a brief understanding check such as
"Does that make sense?"

Start from normal conversation, not a form. If I say something broad like
"I want to build a game but I do not know where to start," help me turn that
into a first milestone by asking beginner-friendly questions with examples,
teaching the relevant project concepts, and only then translating the plan into
FORGE scope and owner gates.

Before any FORGE initialization or initiative creation, give me:
- the product or research vision;
- the first milestone;
- what is in scope;
- what is out of scope;
- what done means;
- the selected profile;
- my learning goals and preferred learning style;
- owner tasks;
- agent tasks;
- either-party tasks;
- learning or practice tasks;
- owner-only authority gates;
- open questions; and
- the exact next command only if I am ready to authorize it.
```

## Existing FORGE Project Prompt

Use this when returning to a repository that may already have FORGE state.

```text
This repository may already use FORGE. Run `forge --version` and
`forge agent protocol`, then follow the protocol.

Inspect the repository state without making changes. If there is an active
initiative, run the read-only health/status/recap commands required by the
protocol and report:
- the current phase;
- the approved scope;
- selected inputs;
- blockers;
- legal next actions;
- owner tasks;
- agent tasks;
- either-party tasks;
- optional learning or practice tasks for the current phase;
- owner-only gates; and
- the single recommended next collaboration step.

Do not rely on prior chat memory, and do not perform owner-only actions without
my explicit approval of the exact displayed command.
```

## What a Correct Agent Should Do Next

After receiving one of these prompts, a capable agent should:

1. Identify FORGE by the official repository or installed CLI.
2. Run or read `forge agent protocol`.
3. Detect repository state.
4. Ask for existing documents before broad questions.
5. Interview only for uncovered context.
6. Ask about learning goals when the owner wants guided or mentored help.
7. Play back the owner vision and first milestone.
8. Show distinct phases and collaboration tasks.
9. Separate practice tasks from routine owner review and owner-only gates.
10. Gather information conversationally instead of presenting a rigid form.
11. Preserve owner-only command gates.
12. Quote FORGE receipts accurately.
13. Keep claim, check, evidence, verification, and acceptance separate.

If an agent skips these steps, paste the shorter prompt again and ask it to
restart from FORGE state detection.
