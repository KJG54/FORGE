# Profile-Aware Facilitation Friction Report

Initiative: `fb1e3732-334f-4bb1-9e51-40dad0e9521b`
Step: `review-risk`
Source: owner-supplied dogfooding handoff in conversation on 2026-08-12

## Boundary

This report records owner-supplied dogfooding findings and successor-work direction for the
profile-aware facilitation initiative. It is not owner acceptance, closeout approval, scope
approval for a successor initiative, or permission to implement `project-basic`.

The handoff states that successor implementation must wait until the current dogfooding and
profile-aware initiative is closed out and the owner creates or authorizes successor work.

## Dogfooding Synthesis

The profile-aware work improved FORGE's direct-agent collaboration model, but the dogfooding
finding is that FORGE still reads too much like a governed software implementation workflow and
not enough like a start-to-finish project companion.

The desired product direction is broader: FORGE should help a human and agent move from initial
vision to completed project by capturing intent, researching context, planning, creating,
evaluating, revising when needed, teaching along the way, and preserving governed records. Target
domains include software, scientific research, beginner game projects, physical making, songs,
writing, and other guided human-agent projects.

## Owner-Observed Criteria Dispositions

The supplied handoff did not include complete per-run dogfood metadata for every O1-O9 item. The
dispositions below therefore distinguish direct findings from items that were not specifically
recorded in the handoff.

| ID | Disposition | Noted finding |
|---|---|---|
| O1 | Not specifically recorded | The handoff did not state whether a fresh agent with one starter prompt routed itself to FORGE rather than an unrelated `forge` tool. |
| O2 | Partially met | Document-first intake and milestone playback remain important; the handoff recommends asking for existing documents before broad questions and playing back the human vision before planning. |
| O3 | Not specifically recorded | The handoff does not report whether every current workflow step was presented as a distinct phase, but it recommends phase guidance for every `project-basic` step. |
| O4 | Partially met | Delegation is useful, but the handoff says owner practice tasks must be identified separately from review tasks. |
| O5 | Partially met | Guided review surfaced a product-level tradeoff: keep narrow workflows only when their use case is clearer than `project-basic`. |
| O6 | Not met for the intended experience | Mentor mode can still feel like normal chat plus audit logging, so the learning-by-building experience is not yet strong enough. |
| O7 | Not specifically recorded | The handoff did not include minimal-versus-mentored token-use comparison. |
| O8 | Not specifically recorded | The handoff did not include a successful capable non-Codex/non-Claude universal or manual prompt run. |
| O9 | Partially met | The handoff says the interview should ask small question batches with examples for beginners, implying the current experience is not consistently conversational enough. |

## Friction Findings

| ID | Severity | Finding | Suggested disposition |
|---|---|---|---|
| F1 | High | Approval flow can be too granular. | Use bounded authorization envelopes for coherent low-risk batches in successor design without weakening owner-only gates. |
| F2 | High | Human-facing artifacts, especially plans, need explicit owner review checkpoints before the agent proceeds. | Make major artifact confirmation a first-class expected behavior in `project-basic`. |
| F3 | High | Mentor mode can still feel like ordinary chat plus audit logging. | Strengthen `mentored` behavior around project-specific learning paths, examples, owner practice tasks, and understanding checks. |
| F4 | Medium | `software-basic` biases agents toward implementation and compliance. | Position it as a fast path for clear software work where vision and context already exist. |
| F5 | Medium | `research-basic` has research stages but lacks rich `interview_guidance` and `phase_guidance`. | Treat as related product debt; consider after or alongside `project-basic` only if the successor scope allows it. |
| F6 | Medium | Existing docs contain pieces of the broader vision but no canonical statement that FORGE is a general start-to-finish project companion. | Add a canonical product vision statement in successor scope. |
| F7 | Medium | New, vague, learning-heavy, creative, hands-on, and cross-domain projects need a default workflow. | Create an experimental bundled `project-basic` workflow in successor scope. |
| F8 | Medium | Revision flow is an open design question. | Decide whether revision should be explicit or handled through existing rework/invalidation; avoid forcing fake revision when evaluation passes. |

## Successor Workflow Direction

Recommended experimental workflow:

```text
intake -> research -> plan -> create -> evaluate -> review -> close
```

The intake stage is the highest-value proposed addition. It should capture vision, intended
audience, success criteria, constraints, human ability, learning goals, desired involvement, and
whether the project belongs in `project-basic` or a narrower workflow.

Recommended artifact roles for successor design:

- `human-vision-brief`
- `owner-context-and-learning-profile`
- `context-readiness-report`
- `project-research`
- `project-plan`
- `task-map`
- `acceptance-criteria`
- `created-work`
- `evaluation-report`
- `review-report`
- `lessons`
- `closure-record`

## Workflow Positioning

- `project-basic`: default for new, vague, learning-heavy, creative, hands-on, or cross-domain projects.
- `software-basic`: fast path for clear software work where vision and context already exist and governed implementation/verification is the main need.
- `research-basic`: appropriate when research itself is the final deliverable, such as evidence synthesis, literature review, a scientific question, or a decision memo.

If a narrow workflow cannot clearly justify when it is better than `project-basic`, treat that as
product debt.

## Required Successor UX Behavior

- Ask for existing documents before broad questions.
- Ask small batches of questions with examples for beginners.
- Play back the human vision before planning.
- State what is known, uncertain, and blocked.
- Recommend profile and workflow fit before creation where possible.
- Teach project and domain concepts in `guided` or `mentored` mode.
- Identify owner practice tasks separately from owner review tasks.
- Ask the human to confirm major artifacts before proceeding.
- Use bounded batch approvals for coherent low-risk action groups.

## Recommended First Successor Scope

1. Product vision statement for general project companionship.
2. Experimental `project-basic` workflow.
3. Interview and phase guidance for every step.
4. Basic templates for key artifacts.
5. Docs explaining when to use `project-basic`, `software-basic`, and `research-basic`.
6. Tests proving no authority drift.
7. Dogfood guide for owner-observed evaluation.
