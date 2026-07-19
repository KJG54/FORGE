# M3 Increment 5 — Claude Code Discovery and Safe Preparation

## Authorized scope

- a registered provider-specific Claude Code adapter;
- shared provider-independent local-CLI discovery and preparation mechanics;
- a non-persisted absolute process-local executable override;
- bounded Claude-labelled version, stable-feature, and persisted-authentication diagnostics;
- visible manual fallback for missing, non-runnable, incompatible, or unauthenticated Claude;
- exact canonical-context digest validation and deterministic read-only invocation preparation; and
- preservation of the existing explicitly manual portable-handoff path.

## Explicit exclusions

Claude or Codex model execution, writable permissions, interactive approvals, environment-provided
API/OAuth/cloud credentials, provider extensions, governed adapter runs, process supervision or
cancellation, streaming-output capture, automatic `AgentResult` generation, capabilities,
executable pack trust, and M4 work are not implemented. Existing persistence and public schema
formats are unchanged.

## Design evidence

[ADR-0030](../adr/ADR-0030-claude-code-discovery-and-safe-preparation.md) records the official CLI
surface, bounded-probe and credential-environment policies, fail-closed compatibility profile,
extension suppression, exact digest binding, shared local-CLI mechanics, and no-execution stop
point. [Agent Adapters](../adapters.md) documents operator behavior and the process-local override.

## Test evidence

Cross-platform fake-CLI tests cover runtime protocol conformance, both documented Claude-labelled
version shapes, unrelated-version rejection, required safety flags, persisted authentication,
environment credential exclusion, missing and incompatible executables, exact canonical-payload
digest binding, deterministic plan-mode arguments and stdin, disabled process operations, registry
selection, visible fallback diagnostics, and manual portable-handoff preservation. Existing Codex
tests exercise the factored shared mechanics without behavior changes.

Final validation on Windows recorded:

- 204 tests passed with 6 expected symlink-privilege skips;
- Ruff and strict Pyright passed with no findings;
- isolated source and wheel builds passed with Hatchling 1.31.0; and
- a fresh environment installed the wheel and passed version/help, initialization, configuration,
  bundled-pack validation, initiative creation, manual diagnostics, compatible persisted-auth
  diagnostics against the installed Claude Code 2.1.207 CLI, deterministic missing-Claude manual
  fallback, explicitly manual handoff, and 45-schema export smoke checks.

## Stop point

Stop after Claude discovery, diagnostics, and safe invocation preparation are implemented and
validated. Do not start either provider, create adapter runs, capture provider output, or implement
capabilities without the next explicit increment authorization.
