# FORGE Canonical Agent Context

## Objective

Deliver and validate a feature-complete personal/local FORGE Production-v1 candidate with an intuitive conversational layer for direct Codex and Claude Code workspace agents, ready for extended owner testing without public publication

## Active step

- ID: `closeout`
- State: `in_progress`
- Purpose: Record release-candidate readiness and lessons without publishing Production v1.
- Instructions: Bind the readiness record to accepted verification and risk-review outputs.
- Context selection rules: accepted-risk-review

### Selected required inputs

- `friction-report`: `release/local-production-v1/friction-report.md` (sha256:d34aa1be12b458a5e90983a4dcaf1d7ecf36120485da20aabab09e0e4b12bdfe, text/markdown)
- `residual-risk-report`: `release/local-production-v1/residual-risk-report.md` (sha256:1641ffee5c283420177929d9d6a278d22870fa4ce6eb78d48effff2ac264abfb, text/markdown)

## Approved scope

Design, implement, document, package, and validate the local FORGE 1.0.0 candidate: document-first conversational bootstrap, canonical transaction receipts, a safe local scratchpad and warm recap, per-step mentoring, honest authority/operator provenance, explicit owner-only command ceremony, rejection and plan-change handling, and archive-derived successor briefs. Preserve existing compatibility, security, recovery, exact-byte, replay, idempotency, and archive invariants. Build and test one exact local wheel and sdist, then stop at extended owner testing. Exclude public naming clearance, tags, PyPI/TestPyPI, GitHub Releases, public support channels, publication automation, hosted or multi-user operation, and final owner acceptance.

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
