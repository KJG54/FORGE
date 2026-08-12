# Profile-Aware Facilitation Residual Risk Report

Initiative: `fb1e3732-334f-4bb1-9e51-40dad0e9521b`
Step: `review-risk`
Source: owner-supplied dogfooding handoff in conversation on 2026-08-12

## Boundary

This report classifies residual risk for closing the current profile-aware facilitation initiative.
It does not accept the current initiative, close it, authorize successor scope, or implement
`project-basic`.

## Closeout Recommendation

The current initiative can reasonably proceed toward owner review and closeout if the owner accepts
that the profile-aware work is an enabling layer, not the final product answer for broad
start-to-finish project companionship.

The next product move should be a successor initiative focused on an experimental `project-basic`
workflow and supporting documentation/tests. That successor should not be implemented inside this
initiative.

## Residual Risks

| ID | Severity | Risk | Mitigation or successor action |
|---|---|---|---|
| R1 | High | The current profile-aware layer may still feel like normal chat with audit logging, especially in `mentored` mode. | Address through richer `project-basic` intake, learning-path, phase, and artifact-review behavior. |
| R2 | High | Bounded authorization envelopes could accidentally weaken FORGE's owner authority model if implemented loosely. | Successor tests must prove claim/check/evidence/verification/owner-acceptance boundaries remain unchanged. |
| R3 | Medium | The supplied dogfooding handoff gives strong product direction but not complete O1-O9 per-run metadata such as exact prompt, agent identity, exact revision, and token-use comparison. | Treat this as enough directional evidence for successor scoping only; do not present it as exhaustive validation. |
| R4 | Medium | `software-basic` remains biased toward implementation/compliance and may not serve vague, creative, hands-on, or learning-heavy projects well. | Reposition it as the clear-software fast path rather than the default for all projects. |
| R5 | Medium | `research-basic` lacks rich `interview_guidance` and `phase_guidance`. | Keep it as the research-final-deliverable workflow and handle guidance upgrades as product debt unless successor scope includes them. |
| R6 | Medium | FORGE lacks one canonical product vision statement for general start-to-finish project companionship. | Add the vision statement in the successor initiative before or alongside workflow data changes. |
| R7 | Medium | The revision step design is unresolved. | Decide in successor design whether revision is explicit or uses existing rework/invalidation mechanics; avoid requiring fake revision after passing evaluation. |
| R8 | Low | Workflow selection could confuse users if `project-basic`, `software-basic`, and `research-basic` overlap without clear guidance. | Document when each workflow is the best fit and treat unjustified overlap as product debt. |

## Constraints To Preserve

- Workflows remain declarative and domain-neutral.
- Packs may use domain-specific step and artifact names.
- `interview_guidance` and `phase_guidance` remain presentation-only and do not alter authority.
- Profiles remain locked at initiative creation unless a separate future change revises that rule.
- Existing governance sequence remains: claim, check, evidence, FORGE verification, owner acceptance.
- Pack changes require version and digest updates.

## Successor Validation Targets

Machine checks should cover:

- workflow load and validation;
- correct pack version and digest identity;
- guidance fields present and digest-bound;
- no governance authority drift;
- required inputs and outputs reachable;
- unchanged existing `software-basic` and `research-basic` behavior unless explicitly scoped.

Owner-observed dogfood scenarios should cover:

- beginner game project;
- scientific or evidence research project;
- physical or hands-on project;
- creative song or writing project;
- small clear software change.

For each dogfood run, record whether FORGE captured vision, improved context, asked useful
questions, taught appropriately, supported delegation, reduced confusion, and felt meaningfully
better than regular chat.

## Recommended Successor Boundary

The first successor should deliver only:

1. Product vision statement for general project companionship.
2. Experimental `project-basic` workflow.
3. Interview and phase guidance for every step.
4. Basic templates for key artifacts.
5. Docs explaining when to use `project-basic`, `software-basic`, and `research-basic`.
6. Tests proving no authority drift.
7. Dogfood guide for owner-observed evaluation.

The successor should not redesign all workflows at once.
