# FORGE Canonical Agent Context

## Objective

Deliver an experimental bundled project-basic workflow for governed start-to-finish human-agent projects.

## Active step

- ID: `closeout`
- State: `invalidated`
- Purpose: Record release-candidate readiness and lessons without publishing Production v1.
- Instructions: Bind the readiness record to accepted verification and risk-review outputs.
- Context selection rules: accepted-risk-review

### Selected required inputs

- `friction-report`: `release/project-basic/friction-report.md` (sha256:d4da6a4703ed6ab14a6f71c41b4b88d835d886c41abd64be3c67c93da93c83c1, text/markdown)
- `residual-risk-report`: `release/project-basic/residual-risk-report.md` (sha256:baee5827de2d8ab6c0dbcd0ea6813a61ed4435b33d5d5fde3c822dc84ff039ed, text/markdown)

## Approved scope

Add standalone project-basic@0.1.0 with seven declarative phases, eleven read-only templates, digest-bound guidance, companion/workflow-selection docs, owner-observed dogfood guide, inventory/conformance/distribution tests, and documented clean-worktree closure/Git-publishing guidance; preserve core lifecycle, protocol 1.4.0, CLI default, existing pack identities, archives, and framework version 1.0.0.

## Relevant constraints

- Context selection rule: accepted-risk-review

## Relevant decisions

- None

## Permitted actions

- Create only declared returned files within the approved scope
- Report worker claims, tool metadata, and limitations without governance approval
- Use only the selected required-input paths listed in the active step

## Prohibited actions

- Record or imply owner decisions, acceptance, checks, or evidence
- Modify FORGE-managed paths or undeclared project files
- Read unrelated repository, archive, ignored, environment, or local-secret content
- Execute external or irreversible side effects without separate authorization

## Required outputs

- release-readiness-record
- lessons

## Expected evidence

- Worker claim requirement: outputs-produced
- Check requirement after import: closeout-ready
- Workflow evidence class after import: check-evidence
- Owner-only acceptance requirement: owner-acceptance
- Returned files require staged import before registration
- Worker claims never constitute checks, evidence, or owner acceptance

## Return contract

- Contract: `agent-result`
- Manifest filename: `result.json`
- Schema filename: `agent-result.schema.json`
- Bind source_run_or_handoff_id to the identifier supplied by FORGE
- Declare every returned file, worker claim, limitation, and tool metadata item
- Treat every returned file and claim as untrusted until staged import succeeds

## Known blockers

- None
