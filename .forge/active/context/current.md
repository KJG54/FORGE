# FORGE Canonical Agent Context

## Objective

Prepare the FORGE M6 release candidate through governed framework-change review

## Active step

- ID: `verify-release`
- State: `in_progress`
- Purpose: Validate the exact candidate change against its release requirements.
- Instructions: Preserve check and evidence results without treating process success as owner acceptance.
- Context selection rules: release-requirements, framework-changes

### Selected required inputs

- `release-requirements`: `release/dogfood/release-requirements.md` (sha256:8557669f290628c561996a456ab9bae6315f67cb8a3437956e99dc695a11434d, text/markdown)
- `framework-changes`: `release/dogfood/framework-changes.md` (sha256:69e206d415340fad0a5a1c89ed00fcc8b27aaac93e9290c6e9f61996f117c0be, text/markdown)

## Approved scope

M6 Increment 7 dogfooding and Increment 8 validation, friction, residual-risk, and closeout evidence only; no M7 publication

## Relevant constraints

- Context selection rule: release-requirements
- Context selection rule: framework-changes

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

- verification-report

## Expected evidence

- Worker claim requirement: outputs-produced
- Check requirement after import: release-checks-passed
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
