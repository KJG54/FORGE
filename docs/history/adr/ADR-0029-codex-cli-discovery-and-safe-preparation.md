# ADR-0029: Codex CLI Discovery and Safe Preparation

**Status:** Accepted

**Milestone:** M3 Increment 4

## Context

The next provider-specific adapter must recognize a separately installed OpenAI Codex CLI without
making Codex authoritative or weakening the manual fallback. Current official Codex documentation
defines stable non-interactive execution through `codex exec`, JSON Lines output, ephemeral
sessions, explicit sandbox and approval flags, stdin prompts, and `codex login status`.

FORGE does not yet have the isolated output workspace, governed adapter-run transaction,
cancellation ownership, or staged automatic result capture required to let an external worker write
safely. Starting Codex directly in the project repository would allow worker writes to bypass the
existing untrusted-result import boundary.

## Decision

Register `CodexAgentAdapter` alongside the manual adapter. Discover `codex` from the process `PATH`
or an absolute process-local `FORGE_CODEX_EXECUTABLE` override. The override is not persisted in
tracked configuration. Windows command shims are launched through the native command processor;
PowerShell scripts are not invoked implicitly.

Run only bounded, non-interactive diagnostic probes in this increment:

- `codex --version` for availability and version reporting;
- `codex exec --help` for compatibility with the required stable `--json`, `--ephemeral`,
  `--sandbox`, and `--ask-for-approval` flags; and
- `codex login status` for persisted-login state.

Each probe has a five-second default timeout and 64 KiB combined-output limit. Diagnostics expose
normalized states and do not echo provider output. Their environment is allowlisted for operating
system, home, PATH, locale, and Codex state discovery; API keys and Codex access-token variables are
not forwarded. Compatibility is feature-based rather than tied to an owner-undeclared minimum
version. A missing, non-runnable, feature-incompatible, or unauthenticated CLI falls back visibly
to manual while retaining the requested adapter diagnostic.

Prepare a deterministic local-process plan only after availability, compatibility, and persisted
authentication succeed. Validate the exact canonical JSON payload against its SHA-256 digest, pass
it through stdin, use JSONL and ephemeral mode, and force `read-only` plus `never` approval. The plan
contains no output directory and cannot be started in this increment. Process start, cancellation,
output capture, and automatic result-manifest production report explicit unsupported/manual states.
`forge handoff` remains an explicitly manual operation even when Codex is usable.

The adapter request and plan extensions remain transient Python values. No journal, run, snapshot,
configuration, archive, handoff, result, or public schema format changes.

## Consequences

Owners can distinguish missing, incompatible, unauthenticated, and usable Codex installations with
`forge agent doctor --adapter codex`, while every unusable installation degrades without blocking
manual work. Invocation arguments are based on current documented stable flags and canonical
context bytes are digest-bound before they can reach the provider.

The adapter is intentionally preparation-only. It does not execute a model request, consume
credentials from environment variables, write to the project, create a governed run, capture JSONL,
generate an `AgentResult`, or grant a capability. Those operations require a later owner-authorized
increment that preserves the same isolation and staged-import boundary.
