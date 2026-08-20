# FORGE Canonical Agent Context

## Objective

Establish one current, discoverable FORGE authority and specification lifecycle while preserving the recovered Production-v1 master specification as historical evidence

## Active step

- ID: `implement`
- State: `ready`
- Purpose: Produce the bounded framework change.
- Instructions: Change only what the accepted scope authorizes and preserve governed compatibility boundaries.
- Context selection rules: accepted-scope, release-requirements

### Selected required inputs

- `change-scope`: `release/authority-specification-lifecycle/change-scope.md` (sha256:cab7b03b82d81da3fcf9fab6f0732ce5751d8455f5e4fa3f0c17cde7c60c2fd8, text/markdown)
- `release-requirements`: `release/authority-specification-lifecycle/release-requirements.md` (sha256:6fb33ba226c98b4575be807b07385444b30584d7b3409c97e304b532a527c702, text/markdown)

## Approved scope

Preserve the owner-supplied Production-v1 Master Implementation Specification byte-for-byte under historical specifications with provenance, historical status, and SHA-256 ec0da4a895dd762e49746c6f029f6bfca251825e011363c53438e5034ccd764a; write a superseding ADR defining normative design, persisted runtime-history, locked-rule, reference-content, and derived-advisory authority types; explain the applicability boundary between initiative-scoped owner decisions and global FORGE architecture; create one concise current governing specification; update the Constitution authority section and move finished milestone mechanics out of the living constitutional contract without rewriting historical records; correct the blended hierarchy in docs/architecture.md; align docs/README.md; define machine-readable ADR effective-status and supersession metadata; add semantic documentation checks; and update only the dogfood closure status in the roadmap and friction register. Exclude project-basic UX or profile changes, release/version and installation changes, CLI or journal refactors, security or GitHub settings, cleanup, default-workflow changes, and publication or release authorization. Stop after the authority documents, ADR, status metadata, navigation, and checks are reviewed and accepted.

## Relevant constraints

- Context selection rule: accepted-scope
- Context selection rule: release-requirements

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

- framework-changes

## Expected evidence

- Worker claim requirement: outputs-produced
- Check requirement after import: implementation-validated
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
