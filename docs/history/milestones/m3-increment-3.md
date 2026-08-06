# M3 Increment 3 — Neutral Agent Adapter and Manual Baseline

## Authorized scope

- a provider-neutral `AgentAdapter` interface covering the complete required lifecycle surface;
- a built-in manual adapter that exercises the interface without external process execution;
- configured or explicit adapter selection with visible manual fallback;
- read-only `forge agent doctor` diagnostics; and
- digest-bound routing of `forge handoff` through the manual adapter preparation path.

## Explicit exclusions

Codex and Claude executable discovery, vendor version policies, authentication probing, external
process invocation or supervision, durable adapter runs, automatic result manifests, capability
approval/revocation/execution, executable pack trust, context embedding, and M4 work are not
implemented. Existing persistence and public schema formats are unchanged.

## Design evidence

[ADR-0028](../adr/ADR-0028-neutral-agent-adapter-and-manual-baseline.md) records the isolation,
selection, fallback, digest-binding, and transient-contract decisions. [Agent Adapters](../adapters.md)
documents operator and adapter-author behavior. Existing handoff and staged-import trust boundaries
remain in [Manual Handoffs and Safe Result Import](../handoffs-and-imports.md).

## Test evidence

Focused tests cover runtime protocol conformance, availability/version/compatibility diagnostics,
process-free operation results, manifest hand-back requirements, exact canonical-context digest
binding, non-governing handoff creation, absence of generated context side effects, configured
missing-adapter fallback, read-only CLI diagnostics, and the existing handoff/import CLI baseline.

Final validation on Windows recorded:

- 196 tests passed with 6 expected symlink-privilege skips;
- Ruff and strict Pyright passed with no findings;
- isolated source and wheel builds passed with Hatchling 1.31.0; and
- a fresh environment installed the wheel and passed version/help, initialization, configuration,
  bundled-pack validation, initiative creation, manual and missing-Codex diagnostics, digest-bound
  manual handoff creation, and 45-schema export smoke checks.

## Stop point

Stop after the neutral interface and manual adapter baseline are implemented and validated. Do not
begin Codex or Claude discovery, external process behavior, capabilities, or executable pack trust
without the next explicit increment authorization.
