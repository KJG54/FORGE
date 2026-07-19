# Agent Adapters

M3 Increment 3 introduces the neutral adapter boundary and its always-available manual baseline.
Increment 4 adds bounded discovery, diagnostics, and safe preparation for a separately installed
Codex CLI. Increment 5 adds the symmetric Claude Code boundary. FORGE still does not start either
external worker.

## Inspect selection

Run the read-only diagnostic from an initialized FORGE repository:

```console
forge agent doctor
forge agent doctor --adapter manual
forge agent doctor --adapter codex
forge agent doctor --adapter claude
```

Without `--adapter`, FORGE uses `agents.preferred_adapter` from `forge.yaml`, then defaults to
`manual`. An unregistered, unavailable, incompatible, or unauthenticated preference selects the
manual adapter and prints the fallback reason. `manual`, `codex`, and `claude` are registered.

The manual diagnostic reports that it is built in and requires no authentication. Provider
diagnostics use bounded local commands to report executable availability, parsed version, required
stable non-interactive flags, and persisted-login state. No adapter reports process start,
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

## Claude Code discovery and preparation

FORGE resolves `claude` from the current process `PATH`. A separately located native executable or
command shim can be selected for only the current process:

```console
FORGE_CLAUDE_EXECUTABLE=/absolute/path/to/claude forge agent doctor --adapter claude
```

On PowerShell:

```powershell
$env:FORGE_CLAUDE_EXECUTABLE = "C:\absolute\path\to\claude.exe"
forge agent doctor --adapter claude
```

Diagnostics run `claude --version`, `claude --help`, and `claude auth status` with the same
five-second timeout and bounded-output policy as Codex. The allowlisted environment permits
`CLAUDE_CONFIG_DIR` so persisted credentials can be found, but excludes `ANTHROPIC_API_KEY`,
`CLAUDE_CODE_OAUTH_TOKEN`, and cloud-provider credential variables. FORGE accepts only
Claude-labelled version output and requires the documented preparation flags to be visible in
help. Because Claude documents that help can omit supported flags, a missing flag means FORGE
cannot prove compatibility; it is a fail-closed profile rather than a claim that the installed CLI
lacks the feature.

After persisted authentication succeeds, preparation binds the exact canonical JSON and produces:

```console
claude --print --input-format text --output-format stream-json \
  --permission-mode plan --no-session-persistence --bare \
  --tools Read,Glob,Grep --strict-mcp-config --no-chrome
```

The canonical assignment is supplied through stdin. Plan mode and the explicit tool list prevent
project edits; bare mode disables project and user hooks, skills, plugins, memory, and instruction
discovery; strict MCP mode without an MCP configuration prevents MCP loading; browser integration
and session persistence are disabled. These controls narrow the future process surface but do not
make same-user execution a security sandbox, so Increment 5 still does not start the plan.

The flags and authentication probe follow Anthropic's official
[Claude Code CLI reference](https://code.claude.com/docs/en/cli-usage),
[non-interactive mode](https://code.claude.com/docs/en/headless), and
[permission modes](https://code.claude.com/docs/en/permission-modes).

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
