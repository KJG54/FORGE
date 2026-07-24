# Canonical Agent Context

M3 Increment 1 adds the provider-neutral source for future manual and adapter integrations. It does
not install or invoke Codex, Claude, or any other worker.

Run:

```console
forge agent context --target neutral
```

FORGE validates the active initiative and writes deterministic views to:

- `.forge/active/context/current.json`;
- `.forge/active/context/current.md`.

These files are generated and tracked by the hybrid Git policy. They are not journal events,
decisions, evidence, or acceptance, and they never replace the authoritative governed records from
which they are derived.

## Included information

The context contains only the objective, active step, approved scope, relevant workflow selection
constraints, active decisions, worker permissions and prohibitions, required outputs, expected
claims/checks/evidence/acceptance boundary, return contract, and known blockers.

The approved scope is the immutable initiative creation scope until an owner records a validated
M4 scope amendment. Thereafter newly generated context uses the complete scope from the latest
amendment; it does not merge prose heuristically or include a stale prior scope as worker authority.

The active step lists only governed artifacts whose roles are declared in that step's
`required_inputs`. Each selected input exposes its role, repository-relative path, current digest,
and media type. File content is not copied into the context. A worker may use those paths, but the
digest makes stale working bytes detectable before execution.

If a selected input is absent or no longer matches its registered revision, FORGE still generates
an inspectable context, records the condition under `known_blockers`, and emits no permitted worker
actions. The owner must register the missing or changed artifact through the normal workflow before
using the context for work.

## Leakage boundary

Generation is allowlist-based. It does not crawl or include:

- ordinary unrelated project files or directories;
- `.env` or environment dumps;
- `.forge/local/`, including `.forge/local/secrets/`;
- archived initiatives;
- ignored content;
- non-selected artifact paths or content;
- superseded decisions.

The JSON contract is public and exported as `canonical-agent-context.schema.json`. Both generated
views are replaced atomically one file at a time while the repository mutation lock prevents a
concurrent supported mutation. Re-run the command to regenerate both views after any interruption or
governed state change.

## Managed vendor references

M3 Increment 2 supports optional root vendor references:

```console
forge agent context --target codex
forge agent context --target codex --apply
forge agent context --target claude
forge agent context --target claude --apply
```

The first command is always a read-only preview. It reports whether FORGE would create, append,
replace, or leave the target unchanged, displays exact current/proposed/context digests, and shows
only the managed reference block. It never echoes existing user content. `--apply` explicitly
confirms the displayed plan, regenerates neutral `current.json` and `current.md`, and updates
`AGENTS.md` or `CLAUDE.md` atomically.

FORGE owns only the span between these standalone markers:

```text
<!-- BEGIN FORGE MANAGED CONTEXT -->
<!-- END FORGE MANAGED CONTEXT -->
```

All bytes outside that span are preserved. With no block, existing content remains an exact prefix.
Malformed or duplicate markers, symbolic links, non-UTF-8 files, oversized results, and any file or
neutral-context change after preview are refused. The block contains references and the exact
canonical JSON digest rather than embedding the assignment.

M3 Increment 3 adds the neutral adapter interface, a process-free manual implementation, and
read-only `forge agent doctor` selection diagnostics. `forge handoff` derives this same canonical
context in memory and binds the manual plan to its exact JSON digest; it does not replace the
tracked current views as a side effect. Installed-tool discovery, external invocation, capability
approval, and executable pack trust remain deferred.

M3 Increment 4 can validate this exact JSON payload and prepare it as stdin for a compatible,
persistently authenticated Codex CLI. The prepared command is forced to read-only, ephemeral JSONL
mode and cannot be started yet. Manual handoff remains the only execution path until isolated
adapter output and governed run orchestration are implemented.

M3 Increment 5 applies the same exact-payload and digest boundary to a compatible, persistently
authenticated Claude Code CLI. Its prepared stdin plan uses non-interactive streaming output,
plan mode, no session persistence, bare startup, no MCP or browser integration, and only the
`Read`, `Glob`, and `Grep` built-in tools. It also cannot be started yet.

M3 Increment 6 starts an explicitly selected compatible Codex or Claude adapter only after creating
a governed run and a disposable local workspace. It writes the exact canonical JSON used for that
run to `workspace/context.json` and copies only digest-verified `required_inputs` beneath
`workspace/inputs/`. The provider receives write access only for its disposable workspace and must
return an `AgentResult` bundle below `workspace/result/`; no tracked context view or project target
is changed by execution. Returned bytes remain untrusted and require explicit import application,
claim, checks, evidence, and owner acceptance.
