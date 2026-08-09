# FORGE Canonical Agent Context

## Objective

Deliver and validate a feature-complete personal/local FORGE Production-v1 candidate with an intuitive conversational layer for direct Codex and Claude Code workspace agents, ready for extended owner testing without public publication

## Active step

- ID: `verify-release`
- State: `ready`
- Purpose: Validate the exact candidate change against its release requirements.
- Instructions: Preserve check and evidence results without treating process success as owner acceptance.
- Context selection rules: release-requirements, framework-changes

### Selected required inputs

- `release-requirements`: `release/local-production-v1/release-requirements.md` (sha256:624f02aa9fc5cbc9f871c7761810450698a5e51ac57c977f9951ad76666bf3b8, text/markdown)
- `framework-changes`: `release/local-production-v1/framework-changes.md` (sha256:97a6b96771f375d21f74aebe875eb720334ca49cb8bef26f9669e19e021728b0, text/markdown)

## Approved scope

Design, implement, document, package, and validate the local FORGE 1.0.0 candidate: document-first conversational bootstrap, canonical transaction receipts, a safe local scratchpad and warm recap, per-step mentoring, honest authority/operator provenance, explicit owner-only command ceremony, rejection and plan-change handling, and archive-derived successor briefs. Preserve existing compatibility, security, recovery, exact-byte, replay, idempotency, and archive invariants. Build and test one exact local wheel and sdist, then stop at extended owner testing. Exclude public naming clearance, tags, PyPI/TestPyPI, GitHub Releases, public support channels, publication automation, hosted or multi-user operation, and final owner acceptance.

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
