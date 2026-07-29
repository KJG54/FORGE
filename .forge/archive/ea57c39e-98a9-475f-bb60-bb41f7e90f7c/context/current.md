# FORGE Canonical Agent Context

## Objective

Prepare the FORGE M6 release candidate through governed framework-change review

## Active step

- ID: `closeout`
- State: `in_progress`
- Purpose: Record release-candidate readiness and lessons without publishing Production v1.
- Instructions: Bind the readiness record to accepted verification and risk-review outputs.
- Context selection rules: accepted-risk-review

### Selected required inputs

- `friction-report`: `release/dogfood/friction-report.md` (sha256:8c2f7d83a1e98df23ecb5601e4fdf7fdf93367909791a9752714b31480c4cb69, text/markdown)
- `residual-risk-report`: `release/dogfood/residual-risk-report.md` (sha256:da0cbe066fb4249821b9be09bf8dfa563f521002553f58f7751fdb0acaddf54a, text/markdown)

## Approved scope

M6 Increment 7 dogfooding and Increment 8 validation, friction, residual-risk, and closeout evidence only; no M7 publication

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
