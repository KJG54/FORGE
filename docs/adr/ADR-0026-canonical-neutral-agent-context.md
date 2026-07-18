# ADR-0026: Canonical Neutral Agent Context

**Status:** Accepted

**Milestone:** M3 Increment 1

## Context

External workers need one provider-neutral description of the current governed assignment. Existing
M1 handoffs are disposable local bundles, while vendor instruction files and future adapters need a
stable generated source that does not become another authority or leak unrelated repository state.

The master specification restricts canonical context to objective, active step, approved scope,
relevant constraints and decisions, permitted and prohibited actions, required outputs, expected
evidence, return contract, and known blockers. It also requires exclusion of ignored, secret,
archived, unrelated, and non-selected content.

## Decision

Generate strict `CanonicalAgentContext` JSON and a deterministic Markdown rendering at
`.forge/active/context/current.json` and `current.md`. The JSON object exposes only the specified
categories plus the standard contract schema version. It is derived from the validated active
initiative, locked workflow, active decision records, materialized step state, and exact metadata
for governed artifacts whose roles are declared as required inputs of the active step.

Selected input entries contain only role, repository-relative path, digest, and media type. FORGE
does not embed file bytes. This keeps the context bounded, makes the selection auditable, and lets a
worker verify exactly which project paths it may use without copying arbitrary project content into
tracked generated files. A missing or drifted selected input becomes a known blocker and removes
worker permissions from the generated view.

Generation never walks ordinary project directories, archives, ignored paths, `.forge/local/`,
environment variables, or secret locations. Active decisions are included by their current
effective identities and relevant semantic fields; superseded decisions are excluded. Generation
runs under the repository mutation lock so the two views are derived from a stable governed state,
then individually replaces each regenerable file atomically. It appends no event and changes no
governance record.

`forge agent context --target neutral` is the only successful target in this increment. The public
Codex and Claude target names are recognized but fail explicitly until managed vendor views are
implemented. No vendor file, adapter process, capability, or worker output is executed.

## Consequences

The tracked context is authoritative only as a generated integration view; the journal, locked
workflow, and governed records remain authoritative state. Git may transport the files but cannot
approve or mutate FORGE state. Re-running the command produces identical bytes for identical
governed inputs and safely repairs an interrupted or stale generated view.

Not embedding selected artifact bytes reduces leakage and churn but means workers must read only the
listed project paths when their task requires the content. Future vendor-view and adapter increments
must derive from this neutral contract and preserve that allowlist. Multi-file replacement cannot be
one filesystem-atomic operation; either valid file can therefore briefly be newer after a process or
hardware interruption, and deterministic regeneration is the explicit repair.
