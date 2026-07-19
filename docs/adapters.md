# Agent Adapters

M3 Increment 3 introduces the neutral adapter boundary and its always-available manual baseline.
Increment 4 adds bounded discovery, diagnostics, and safe preparation for a separately installed
Codex CLI. FORGE still does not start Codex or another external worker.

## Inspect selection

Run the read-only diagnostic from an initialized FORGE repository:

```console
forge agent doctor
forge agent doctor --adapter manual
forge agent doctor --adapter codex
```

Without `--adapter`, FORGE uses `agents.preferred_adapter` from `forge.yaml`, then defaults to
`manual`. An unregistered, unavailable, or incompatible preference selects the manual adapter and
prints the fallback reason. `manual` and `codex` are registered; Claude remains deferred.

The manual diagnostic reports that it is built in and requires no authentication. The Codex
diagnostic uses bounded local commands to report executable availability, parsed version, required
stable non-interactive flags, and persisted-login state. Neither adapter reports process start,
cancellation, or output capture as supported. The command does not generate context, write a
handoff, or change the journal.

## Codex discovery and preparation

FORGE resolves `codex` from the current process `PATH`. For an installation outside `PATH`, set an
absolute path for only the current process:

```console
FORGE_CODEX_EXECUTABLE=/absolute/path/to/codex forge agent doctor --adapter codex
```

On PowerShell:

```powershell
$env:FORGE_CODEX_EXECUTABLE = "C:\absolute\path\to\codex.exe"
forge agent doctor --adapter codex
```

The override is not written to `forge.yaml`. Diagnostics run `codex --version`,
`codex exec --help`, and `codex login status` with a five-second default timeout, a bounded output
limit, and an allowlisted environment that excludes API keys and Codex access-token variables.
FORGE checks for the documented stable `--json`, `--ephemeral`, `--sandbox`, and
`--ask-for-approval` flags instead of declaring an arbitrary minimum version.

When those checks and persisted authentication succeed, the adapter can prepare a deterministic
`codex exec` plan. It binds the exact canonical JSON digest, sends the context through stdin, uses
JSONL and ephemeral mode, and forces `--sandbox read-only --ask-for-approval never`. Increment 4
does not start that plan. Direct execution remains unsafe until FORGE can provide an isolated
output workspace, governed run lifecycle, cancellation, and staged result capture. The supported
execution path therefore remains `forge handoff` plus `forge import-result`.

The Codex flags and behavior above follow the official
[Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) and
[CLI reference](https://developers.openai.com/codex/cli/reference/).

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

The interface objects are transient Python data structures. They are not persistence formats or
exported schemas. Future increments must add isolated execution, bounded process supervision, and
untrusted-result capture without moving governance authority into provider code.
