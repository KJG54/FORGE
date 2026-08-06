# ADR-0030: Claude Code Discovery and Safe Preparation

**Status:** Accepted

**Milestone:** M3 Increment 5

## Context

After the provider-neutral and Codex adapter baselines, FORGE needs the approved parallel boundary
for a separately installed Anthropic Claude Code CLI. Official Claude documentation defines
non-interactive print mode, text stdin, streaming JSON output, plan-mode permissions, persisted
authentication status, session suppression, extension-minimal bare startup, built-in tool
restriction, strict MCP configuration, and browser disabling.

Claude Code can also discover hooks, skills, plugins, MCP servers, memory, browser integration,
user settings, and project instructions. Those extension surfaces may produce external effects or
change behavior before FORGE has a governed adapter-run transaction and isolated result capture.
Starting Claude in this increment would therefore cross the same unsafe boundary recorded for
Codex.

## Decision

Factor the provider-independent executable resolution, bounded probes, environment allowlisting,
exact canonical-payload validation, deterministic plan construction, and explicitly unsupported
process operations into an internal local-CLI adapter base. Preserve the public Codex behavior and
register `ClaudeAgentAdapter` beside `manual` and `codex`.

Discover `claude` from `PATH` or an absolute process-local `FORGE_CLAUDE_EXECUTABLE` override.
Continue to support Windows command shims through the native command processor and reject implicit
PowerShell-script execution. Run only these bounded diagnostics:

- `claude --version` for availability and Claude-labelled version reporting;
- `claude --help` for evidence of the required non-interactive safety flags; and
- `claude auth status` for persisted-authentication state.

Use the established five-second default timeout, 64 KiB combined-output limit, and normalized
diagnostics that never echo provider output. Allow `CLAUDE_CONFIG_DIR` for persisted credential
discovery, but do not forward API keys, OAuth-token environment variables, or cloud-provider
credentials. Anthropic notes that help may omit supported flags; FORGE nevertheless requires the
flags to be visible because it cannot safely prove the preparation profile otherwise. This is a
fail-closed compatibility rule, not a vendor minimum-version commitment.

After availability, compatibility, and authentication succeed, validate the exact canonical JSON
against its SHA-256 digest and prepare this stdin-driven command:

```text
claude --print --input-format text --output-format stream-json
  --permission-mode plan --no-session-persistence --bare
  --tools Read,Glob,Grep --strict-mcp-config --no-chrome
```

The plan uses only read-oriented built-in tools. Bare startup disables normal hooks, skills,
plugins, memory, MCP, and instruction discovery; strict MCP mode supplies no replacement MCP
configuration; browser integration and session persistence are disabled. No process starts, no
output directory is assigned, and cancellation, output capture, and automatic `AgentResult`
production remain explicitly unsupported. `forge handoff` remains explicitly manual.

No persisted contract, journal, snapshot, run, configuration, archive, handoff, result, or schema
format changes.

## Consequences

Operators can distinguish missing, incompatible, unauthenticated, and usable Claude Code
installations without exposing environment credentials or changing governed state. Codex and
Claude share the same tested local-process safety mechanics while retaining provider-specific
compatibility profiles.

The prepared plan intentionally omits normal Claude project instructions, including the managed
`CLAUDE.md` reference, because the exact neutral context is supplied directly and startup
extensions are not yet trustworthy execution inputs. Claude model execution, costs, provider
output parsing, durable runs, cancellation, staged result generation, capabilities, and executable
pack trust remain deferred.
