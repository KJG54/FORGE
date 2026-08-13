# FORGE Canonical Agent Context

## Objective

Repair project-basic CI contract and record CI-detection friction

## Active step

- ID: `closeout`
- State: `ready`
- Purpose: Record release-candidate readiness and lessons without publishing Production v1.
- Instructions: Bind the readiness record to accepted verification and risk-review outputs.
- Context selection rules: accepted-risk-review

### Selected required inputs

- `friction-report`: `release/project-basic-ci-repair/friction-report.md` (sha256:b2d996551f6ce3b47053bdba062ea60b741debcae0ea783ada034aaadf4b22d6, text/markdown)
- `residual-risk-report`: `release/project-basic-ci-repair/residual-risk-report.md` (sha256:ec1d4dcfca240bd34e03b49481a498d24b0c92bf11a2d5b6b3c3db6852cffb81, text/markdown)

## Approved scope

Repair the codex/project-basic CI failures only: restore README wording required by the historical protocol contract, wrap the two Ruff E501 violations, repair the six Pyright type errors in tests/test_project_basic_workflow.py exposed after Ruff passed, document the CI-detection friction, and validate/push the bounded fix; preserve project-basic behavior, framework version 1.0.0, protocol 1.4.0, existing pack identities, archives, release state, and publication boundaries.

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
