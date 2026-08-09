# Canonical Agent Context

M3 Increment 1 adds the provider-neutral source for future manual and adapter integrations. It does
not install or invoke Codex, Claude, or any other worker.

Run:

```console
forge agent context --target neutral
```

FORGE validates the active initiative and writes deterministic views to:

- `.forge/active/context/agent-protocol-1.3.0.md`;
- `.forge/active/context/current.json`;
- `.forge/active/context/current.md`.

These files are generated and tracked by the hybrid Git policy. They are not journal events,
decisions, evidence, or acceptance, and they never replace the authoritative governed records from
which they are derived.

## Direct workspace-agent protocol

Local Production-v1 L2 adds a repository-independent entry point:

```console
forge agent protocol
```

It prints the installed protocol version, SHA-256 digest, and exact content without looking for
`forge.yaml` or `.forge/`. Direct Codex and Claude Code workspace agents use that document for
first-contact state detection, document-first interviewing, coverage playback, draft vision and
milestone scope, separate initialization and creation confirmation, owner gates, daily labor
split, plan changes, delegation, Git/FORGE separation, and the same-user threat model.

The protocol is an exact packaged Markdown resource, not a public record, journal event, permission,
check, evidence packet, or acceptance. Generating canonical context copies the identical bytes
beside `current.json` and `current.md`. The managed vendor reference binds its version and digest so
the workspace agent can read the protocol before the repository-specific canonical context.

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
replace, or leave the target unchanged, displays exact current/proposed/context/protocol digests,
enumerates every persistent derived-file write and the temporary mutation lock, states the
zero-journal-event effect and owner-directed authority boundary, and shows only the managed
reference block. It never echoes existing user content. After that complete preview, the owner may
run `--apply` or explicitly direct the workspace agent to run it. Apply regenerates the installed
protocol copy plus neutral `current.json` and `current.md`, and updates `AGENTS.md` or `CLAUDE.md`
atomically.

FORGE owns only the span between these standalone markers:

```text
<!-- BEGIN FORGE MANAGED CONTEXT -->
<!-- END FORGE MANAGED CONTEXT -->
```

All bytes outside that span are preserved. With no block, existing content remains an exact prefix.
Malformed or duplicate markers, symbolic links, non-UTF-8 files, oversized results, and any file or
neutral-context change after preview are refused. The block contains the exact protocol version and
digest plus references and the canonical JSON digest rather than embedding either document.

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

## Bounded filesystem discovery

M5 Increment 6 adds a separate owner-review aid:

```console
forge agent discover
forge agent discover --max-candidates 16
```

It inventories only bounded path metadata and ranks filename matches using the objective, effective
scope, active-step instructions and context-selection rules, and declared input/output roles. It
does not read unregistered candidate content or return any file content. Existing governed
required inputs may be hashed through the ordinary currentness check so the command can report
whether they exist at their registered revisions.

The inventory never follows symbolic links. It excludes FORGE state, hidden paths, control files,
configured secret locations, common dependency/build directories, unsupported or oversized files,
and paths ignored by Git. If Git ignore rules cannot be enforced, the command withholds
unregistered suggestions and labels the result `indeterminate`.

`sufficient` is a structural result, not a semantic claim. It means current required inputs are
present and the bounded pass completed without exhausting a hard limit. A displayed candidate is
not registered, copied into canonical context, authorized for a worker, or accepted as relevant or
true. Those actions remain explicit and governed.
