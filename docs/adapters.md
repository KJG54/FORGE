# Agent Adapters

M3 Increment 3 introduces the neutral adapter boundary and its always-available manual baseline.
It does not discover or run Codex, Claude, or another external executable.

## Inspect selection

Run the read-only diagnostic from an initialized FORGE repository:

```console
forge agent doctor
forge agent doctor --adapter manual
forge agent doctor --adapter codex
```

Without `--adapter`, FORGE uses `agents.preferred_adapter` from `forge.yaml`, then defaults to
`manual`. An unregistered, unavailable, or incompatible preference selects the manual adapter and
prints the fallback reason. In this increment only `manual` is registered, so `codex` and `claude`
preferences intentionally fall back.

The manual diagnostic reports that it is built in, version-compatible with the running FORGE,
requires no authentication, and does not support process start, cancellation, or output capture.
The command does not generate context, write a handoff, change the journal, or inspect external
executables.

## Manual handoff through the adapter boundary

The existing command remains the portable execution baseline:

```console
forge handoff discover --constraint "Do not modify unrelated files"
```

FORGE derives the canonical context in memory, binds the adapter plan to the SHA-256 digest of its
exact deterministic JSON, verifies that the requested step is current, and writes the existing
disposable handoff bundle under `.forge/local/handoffs/`. It does not write the tracked canonical
context views or mutate governed initiative history. The worker still returns an `AgentResult` for
`forge import-result` preview and explicit application.

## Adapter-author boundary

`forge.adapters.AgentAdapter` requires:

- availability detection and version reporting;
- compatibility assessment and diagnostics;
- invocation preparation;
- process start and cancellation operations;
- output capture; and
- result-manifest production.

An adapter receives frozen request and plan values, not FORGE repository or mutation services.
It must report unsupported operations explicitly. Core orchestration remains responsible for
context derivation, governance checks, handoff materialization, future run records, and staged
imports. Adapter output is never a decision, check, evidence, acceptance, or trusted project state.

The interface objects are transient Python data structures in this increment. They are not new
persistence formats or exported schemas. Future external adapters must add executable discovery,
version policy, authentication diagnostics, bounded process supervision, and untrusted-result
capture without moving governance authority into provider code.
