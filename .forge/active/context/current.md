# FORGE Canonical Agent Context

## Objective

Deliver and validate a feature-complete personal/local FORGE Production-v1 candidate with an intuitive conversational layer for direct Codex and Claude Code workspace agents, ready for extended owner testing without public publication

## Active step

- ID: `implement`
- State: `in_progress`
- Purpose: Produce the bounded framework change.
- Instructions: Change only what the accepted scope authorizes and preserve governed compatibility boundaries.
- Context selection rules: accepted-scope, release-requirements

### Selected required inputs

- `change-scope`: `release/local-production-v1/change-scope.md` (sha256:ea7cdca17591cc8ac0a8075faf149271ea42a6849bca6e6a356d359632c5b102, text/markdown)
- `release-requirements`: `release/local-production-v1/release-requirements.md` (sha256:4346c90eba0856ece1bc524c7a3097ab54c2d3098a0d7033a2665e7c24b3d94c, text/markdown)

## Approved scope

Design, implement, document, package, and validate the local FORGE 1.0.0 candidate: document-first conversational bootstrap, canonical transaction receipts, a safe local scratchpad and warm recap, per-step mentoring, honest authority/operator provenance, explicit owner-only command ceremony, rejection and plan-change handling, and archive-derived successor briefs. Preserve existing compatibility, security, recovery, exact-byte, replay, idempotency, and archive invariants. Build and test one exact local wheel and sdist, then stop at extended owner testing. Exclude public naming clearance, tags, PyPI/TestPyPI, GitHub Releases, public support channels, publication automation, hosted or multi-user operation, and final owner acceptance.

## Relevant constraints

- Context selection rule: accepted-scope
- Context selection rule: release-requirements

## Relevant decisions

- `0b29f759-667c-492d-a45b-a0526f84eaa2` (local-production-v1-conversational-contract): Deliver a personal local 1.0.0 candidate with the approved conversational contracts, preserve existing integrity boundaries, and stop at extended owner testing without public publication
  - Question: What outcome, channels, interaction contracts, compatibility boundary, and stop point govern local Production v1?
  - Rationale: Owner testing established that daily conversational usability is mandatory and public release ceremony is not the current objective; the local candidate preserves engineering rigor without falsifying the abandoned public workflow

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
