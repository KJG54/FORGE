# Project companion

`project-basic` is FORGE's recommended conversational starting point for work that is vague,
cross-domain, creative, hands-on, or learning-heavy. It is a recommendation for the interview and
documentation experience, not a changed command-line default: an unqualified `forge create` still
selects `software-basic` for backward compatibility.

## Choose the workflow that matches the work

| Workflow | Choose it when | Main outcome |
|---|---|---|
| `project-basic` | The vision, context, learning plan, or delivery medium is still being shaped. | A bounded project that moves from intake through research, planning, making, evaluation, review, and closure. |
| `software-basic` | The work is clearly software and the vision/context are already sufficiently defined. | A software implementation and its verification record. |
| `research-basic` | Research itself is the final deliverable. | A traceable research synthesis, limitations, verification, review, and closure. |

The recommendation never grants authority. Before an initiative is created, the owner still
reviews the displayed command and explicitly authorizes it. The selected pack is digest-bound and
its workflow retains the ordinary sequence: worker claim, check, evidence, FORGE verification, and
owner acceptance.

## A beginner-friendly project conversation

Start document-first. Ask for existing notes, sketches, photos, links, source material, constraints,
and a short description of what the owner hopes to make or learn before asking broad questions.
Use small batches of two to four beginner-friendly questions, then play back the emerging vision.
Keep a visible distinction between what is known, uncertain, and blocked.

The `project-basic` phases are:

1. **Intake** records a human vision brief and the owner's context and learning profile.
2. **Research** records readiness and project research. It is mandatory, but a readiness report may
   conclude that no new research is needed when it names the materials considered sufficient, why,
   and any remaining uncertainty.
3. **Plan** turns that material into a project plan, task map, and acceptance criteria.
4. **Create** produces the domain-specific work. FORGE deliberately supplies no generic template
   for it.
5. **Evaluate** records how the exact created-work revision was assessed against the exact
   acceptance-criteria revision.
6. **Review** records the owner-facing review result.
7. **Close** records lessons and closure.

Pause after each major artifact for an owner review checkpoint. The task map can distinguish an
owner's optional practice task from an agent's proposed review task, but the owner remains the only
authority for creation, verification gates, and acceptance. A bounded conversational authorization
envelope may describe the next small batch of routine work and can be revoked at any time; it is
presentation only and never creates a persisted approval or changes a FORGE gate.

If the created work changes, revise the artifact normally. FORGE invalidates its dependent work and
the participant reworks the affected steps. If scope or criteria change, use the normal scope
amendment path. An evaluation finding is information for the owner; it does not automatically move
the workflow.

## Templates and evidence

`project-basic` provides eleven read-only templates through `forge pack template list` and `forge
pack template show`. They are reference text, not auto-generated artifacts or approvals. The
evaluation report deliberately names the exact created-work and acceptance-criteria revision IDs
and digests it assessed, along with results, limitations, and any rework recommendation.

For a practical observation plan, see the [project-basic dogfood guide](project-basic-dogfood.md).
For formal workflow fields and transitions, see [packs and workflows](workflows.md).
