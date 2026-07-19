# M3 Increment 4 — Codex CLI Discovery and Safe Preparation

## Authorized scope

- a registered provider-specific Codex adapter;
- process-local executable discovery with a non-persisted absolute override;
- bounded version, stable-feature compatibility, and persisted-authentication diagnostics;
- visible manual fallback for missing, non-runnable, incompatible, or unauthenticated Codex;
- exact canonical-context digest validation and deterministic read-only invocation preparation; and
- preservation of the existing explicitly manual portable-handoff path.

## Explicit exclusions

Codex model execution, writable sandboxes, interactive approvals, environment-provided API/access
tokens, governed adapter runs, process supervision or cancellation, JSONL/output capture, automatic
`AgentResult` generation, Claude support, capabilities, executable pack trust, and M4 work are not
implemented. Existing persistence and public schema formats are unchanged.

## Design evidence

[ADR-0029](../adr/ADR-0029-codex-cli-discovery-and-safe-preparation.md) records the official stable
CLI surface, bounded-probe policy, feature-based compatibility, credential-environment boundary,
digest binding, and no-execution stop point. [Agent Adapters](../adapters.md) documents operator
behavior and the process-local executable override.

## Test evidence

Cross-platform fake-CLI tests cover runtime protocol conformance, version parsing, required stable
flag detection, persisted-login success and failure, missing executables, feature incompatibility,
exact canonical-payload digest binding, deterministic read-only arguments and stdin, disabled
process operations, registry selection, visible diagnostics, and manual portable-handoff fallback.

Final validation on Windows recorded:

- 200 tests passed with 6 expected symlink-privilege skips;
- Ruff and strict Pyright passed with no findings;
- isolated source and wheel builds passed with Hatchling 1.31.0; and
- a fresh environment installed the wheel and passed version/help, initialization, configuration,
  bundled-pack validation, initiative creation, compatible fake-Codex diagnostics through the
  process-local override, deterministic missing-Codex manual fallback, explicitly manual handoff,
  and 45-schema export smoke checks.

## Stop point

Stop after Codex discovery, diagnostics, and safe invocation preparation are implemented and
validated. Do not start Codex, create adapter runs, capture output, add Claude, or implement
capabilities without the next explicit increment authorization.
