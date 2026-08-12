# FORGE Canonical Agent Context

## Objective

Deliver a beginner-centered, profile-aware collaboration and learning layer for FORGE direct workspace agents, comprising agent protocol 1.4.0, starter-prompt documentation, additive pack interview and phase guidance data, profile-differentiated agent behavior, and protocol/CLI version-skew detection, while preserving every existing governance, authority, compatibility, and append-only pack-identity boundary.

## Active step

- ID: `implement`
- State: `in_progress`
- Purpose: Produce the bounded framework change.
- Instructions: Change only what the accepted scope authorizes and preserve governed compatibility boundaries.
- Context selection rules: accepted-scope, release-requirements

### Selected required inputs

- `change-scope`: `release/profile-aware-facilitation/change-scope.md` (sha256:00f057a196ae55f9fd0f2557938a5ebed77c304101492d853a22d0cd123ae2ee, text/markdown)
- `release-requirements`: `release/profile-aware-facilitation/release-requirements.md` (sha256:ca3ec123632afc7c2939279eea39d12b5c7f60a68ebe98ee9c865e32718345d4, text/markdown)

## Approved scope

Introduce FORGE agent protocol 1.4.0 as a strict superset of 1.3.0 and regenerate its Codex/Claude managed references for profile-aware collaboration, learning goals, phase playback, and task delegation; add additive, default-empty interview-guidance and phase-guidance fields to the pack workflow contract with a mandatory software-basic minor-version bump, append-only (version, digest) identity, unchanged digests for every pack that supplies no guidance, and a matching release/version-contract.json update; populate that guidance for the bundled software-basic pack only; add profile-differentiated rendering rules for minimal, standard, guided, and mentored; add starter-prompt documentation for universal, short, installed-CLI, GitHub-only, Codex, Claude, manual, beginner, and existing-project cases plus the supporting README and docs-index entries; add a protocol/CLI version-skew check surfaced by forge doctor; and add tests for schema compatibility, pack validation, digest identity, context allowlisting, managed-reference byte preservation, and absence of authority drift.

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
