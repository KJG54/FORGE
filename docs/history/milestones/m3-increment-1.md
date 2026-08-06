# M3 Increment 1 — Canonical Neutral Agent Context

## Authorized scope

- strict provider-neutral canonical context generation;
- deterministic JSON and Markdown at `.forge/active/context/current.*`;
- exact required-input metadata selection from the active locked workflow;
- effective active-decision projection, worker authority boundaries, evidence expectations, return
  contract, and actionable blockers;
- allowlist-based leakage prevention and safe regeneration;
- `forge agent context --target neutral` and the public schema export.

## Explicit exclusions

Managed `AGENTS.md` or `CLAUDE.md` content, vendor preview/apply, the `AgentAdapter` interface,
manual-handoff refactoring, Codex or Claude discovery and invocation, adapter compatibility,
capability approval/revocation/execution, pack executable trust, raw-output handling, and M4 work are
not implemented. The recognized `codex` and `claude` context targets fail explicitly.

## Design evidence

[ADR-0026](../adr/ADR-0026-canonical-neutral-agent-context.md) records the neutral contract,
selected-input metadata boundary, tracked-derived persistence policy, mutation-lock usage, and
regeneration tradeoff. [Canonical Agent Context](../agent-context.md) documents the CLI and leakage
boundary.

## Test evidence

Focused tests cover deterministic bytes, exact top-level categories, active decisions, selected and
non-selected artifact behavior, required-input drift, journal non-mutation, local/environment/archive
leakage sentinels, deferred targets, CLI output, schema registration, and symbolic-link refusal where
the platform permits link creation.

Final validation on Windows recorded:

- 179 tests passed with 5 expected symlink-privilege skips;
- Ruff and strict Pyright passed with no findings;
- isolated source and wheel builds passed with Hatchling 1.31.0; and
- a fresh environment installed the wheel and passed version/help, initialization, configuration,
  bundled-pack, initiative creation, neutral context generation, generated-file existence, and
  45-schema export smoke checks.

## Stop point

Stop after canonical neutral context is implemented and validated. Do not begin managed vendor
views, adapters, or capability execution without the next explicit increment authorization.
