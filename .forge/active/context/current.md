# FORGE Canonical Agent Context

## Objective

Prepare the FORGE M6 release candidate through governed framework-change review

## Active step

- ID: `scope`
- State: `awaiting_acceptance`
- Purpose: Define the framework change, constraints, compatibility impact, and acceptance criteria.
- Instructions: Register the exact scope and release requirements before implementation authority is accepted.
- Context selection rules: initiative-objective

### Selected required inputs

- None

## Approved scope

M6 Increment 7 dogfooding and Increment 8 validation, friction, residual-risk, and closeout evidence only; no M7 publication

## Relevant constraints

- Context selection rule: initiative-objective

## Relevant decisions

- None

## Permitted actions

- No worker action is currently permitted

## Prohibited actions

- Record or imply owner decisions, acceptance, checks, or evidence
- Modify FORGE-managed paths or undeclared project files
- Read unrelated repository, archive, ignored, environment, or local-secret content
- Execute external or irreversible side effects without separate authorization

## Required outputs

- change-scope
- release-requirements

## Expected evidence

- Worker claim requirement: outputs-produced
- Check requirement after import: scope-reviewed
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

- Active step is awaiting configured-owner acceptance
