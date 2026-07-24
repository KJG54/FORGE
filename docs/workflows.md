# Packs, Initiative Creation, and Manual Runs

M1 Increment 3 adds the first domain-neutral workflow services. M1 Increment 4 supplies worker
claims, checks, and evidence through the separate services documented in
[`artifacts-and-evidence.md`](artifacts-and-evidence.md). M1 Increment 5 supplies owner acceptance,
revocation, decisions, and invalidation.
M1 Increment 7 adds successful terminal closure after every declared step is complete and currently
accepted.

## Declarative pack loading

FORGE discovers the bundled `software-basic` pack and repository-local pack paths configured in
`forge.yaml`. Every candidate is treated as untrusted input and must pass bounded safe-YAML parsing,
strict Pydantic contracts, workflow reachability checks, supported authority rules, file declaration
checks, and a deterministic SHA-256 digest.

Increment 3 pack digests bind the manifest and workflow definitions. Additional template,
explanation-file, and data-resource bytes are rejected until a later increment includes those exact
bytes in the lock digest. Stray files, executable suffixes, symbolic links, YAML aliases, invalid
schemas, duplicate identities, and digest mismatches are refused. Pack loading never imports or
executes pack content.

Inspecting a pack does not trust it:

```console
forge pack list
forge pack validate software-basic
```

## Owner-authorized initiative creation

One active initiative is allowed. The configured owner must explicitly confirm data-only trust for
the exact selected pack version:

```console
forge create "Deliver the approved change" \
  --scope "Only the declared local change" \
  --trust-pack-data
```

The option does not approve any executable capability. Creation writes immutable initiative,
pack-trust, pack-lock, and workflow-lock records before committing the `initiative-created` journal
event and its reconstructable snapshot. If a failure occurs before the journal commit, newly created
records are removed. If the journal commits first, it remains authoritative and any incomplete
snapshot is reported as an integrity error under the Increment 2 transaction model.

## Transitions and manual runs

The locked workflow determines step order, states, actor classes, authority requirements,
conditions, and events. Replay validates those rules again from the journal; `state.json` cannot
authorize a transition by itself.

`forge begin <step>` starts a `ready` step or explicitly reworks an `invalidated` step, records a
durable manual `RunRecord`, and moves the step to `in_progress`. A running process or manual effort
is not a claim, check, evidence packet, or acceptance decision.

Conditioned transitions cannot be asserted by a caller. FORGE derives `claim-recorded`,
`required-checks-passed`, `required-evidence-registered`, and `owner-acceptance-recorded` from
governed records.

Use read-only commands after any process restart or to inspect a closed archive:

```console
forge status
forge next
forge history
forge status --archive <initiative-id>
forge history --archive <initiative-id>
```

Both commands reload locked records, replay the complete journal, compare `state.json`, and report
integrity errors without silently repairing them.

`forge recover --reason "..."` rebuilds a damaged snapshot from a complete valid journal and, as
of Increment 12, can recover one
unambiguously EOF-truncated final record after preserving the complete source. It never guesses a
missing event or selects among ambiguous histories; see [`recovery.md`](recovery.md).

`forge recover-command <interrupted-key>` is the distinct Increment 13 path for one provably
complete active command whose receipt is missing. It records owner provenance but does not perform
the command again or invent a missing transition. Partial command patterns remain blocked.

## Explanation profiles and run cancellation

M1 supports Standard and Guided presentation. The selected profile chooses only locked pack
explanation text; transition definitions, authority, record requirements, and materialized next
actions are identical.

Run records remain immutable. `forge run list|show` derives effective `running`, `succeeded`, or
`cancelled` state from the journal. `forge run cancel` records a terminal cancellation event and
never implies step completion: safe work may return to `ready`, while the workflow's stricter
cancellation rule or external/sensitive side effects move the step to `blocked` for owner review.

## Atomic successful closure boundary

Successful closure is owner-only and derives readiness from the locked workflow, current
acceptances, exact artifact revisions, and preserved objects. M2 Increment 6 adds validated atomic
archive promotion and resumable active-state retirement. Repeating an interrupted close with the
same idempotency key completes the existing terminal transaction rather than creating a new event.
Closed archives never reopen through supported commands. Continued work uses a fresh successor;
unrelated interruption recovery stays deferred.

## Explicit active-state migration

`forge migrate` previews the next registered source/target edge. Increment 10 implements explicit
owner-authorized `--apply` for complete legacy M1 active journals, preserves their exact source
bytes, atomically commits the M2 hash chain and migration event, and supports same-key retry. See
[`migrations.md`](migrations.md). Immutable archives are validated but never migrated.

## Atomic abandonment boundary

Abandonment is a separate owner-only terminal decision. `forge abandon` requires a reason, an
unfinished-work summary, and at least one unresolved-risk statement. It may start from active or
paused state, but never while a governed run remains active. The owner must cancel such runs first,
making their outcome explicit in history.

Abandonment does not require passed checks, completed steps, or current acceptances. Its event and
record preserve the unfinished step set and current governed artifact revisions, then use the same
validated resumable archive transaction as closure. Its manifest is terminal `abandoned`, carries
only abandonment IDs, and marks every object reference unaccepted. Abandoned archives never reopen.

## Successor initiatives

After terminal archival, continued work uses a new initiative rather than reopening history:

```console
forge create "Continue the objective" --scope "Fresh bounded scope" \
  --predecessor <archive-id> --trust-pack-data
```

Repeat `--predecessor` to merge lineage from multiple valid closed or abandoned archives. FORGE
validates every repository archive before mutation, rejects duplicate, unknown, self, or noncanonical
references, and binds sorted predecessor links into both the new initiative and creation event.

The successor gets a new immutable ID, pack trust decision, workflow lock, journal, snapshot, and
initial step state. It inherits no artifact records, claims, checks, evidence, decisions, stale
state, or acceptance. Predecessor archives are read and validated but never modified.

To reuse a terminal predecessor artifact, keep or restore its exact bytes at a project path and run:

```console
forge artifact add path/to/file --role <role> --title "Reused input" \
  --predecessor-revision <terminal-revision-id>
```

FORGE requires an exact digest and size match, then creates a new successor artifact and revision
whose provenance identifies the predecessor initiative and revision. This is reuse, not inherited
approval; the new revision must pass the successor workflow's checks and acceptance independently.

## Canonical neutral agent context

M3 Increment 1 derives `.forge/active/context/current.json` and `current.md` from the current active
step without changing lifecycle state. `forge agent context --target neutral` selects only current
governed input metadata for roles declared in the step's `required_inputs`, includes active owner
decisions and the normal claims/checks/evidence/acceptance boundary, and removes worker permissions
when the selected inputs or state are blocked.

The context is the neutral source for later integrations, not an adapter or a run. Existing manual
handoffs and staged imports remain unchanged. It does not perform installed-tool discovery, process
execution, capability handling, or executable pack trust.

M3 Increment 2 adds only managed vendor references. A Codex or Claude target previews a bounded
marker block in `AGENTS.md` or `CLAUDE.md`; `--apply` regenerates neutral context and confirms the
vendor change. The block grants no workflow permission and does not create a run. Existing user
content remains byte-for-byte outside the managed span. Installed-tool discovery and all process or
capability behavior remain deferred.

M3 Increment 3 routes portable handoff preparation through the neutral `AgentAdapter` interface.
The built-in manual implementation is always available, starts no process, and requires the same
untrusted `AgentResult` return path. `forge agent doctor` makes selection and fallback visible.
Adapter preparation is transient and does not create a governed run or change workflow authority.

M3 Increment 4 registers a Codex adapter for bounded executable, stable-feature, and persisted-auth
diagnostics. A compatible adapter can prepare a digest-bound, read-only, ephemeral `codex exec`
plan, but FORGE does not start it. `forge handoff` remains manual, and no workflow transition, run,
worker claim, or result import can be implied by adapter availability.

M3 Increment 5 registers a Claude Code adapter under the same selection and fallback rules. A
compatible adapter can prepare a digest-bound `claude --print` plan with streaming JSON, plan-mode
permissions, disabled session persistence and extensions, no MCP or browser integration, and only
read-oriented built-in tools. FORGE does not start it, and manual handoff remains the only worker
transfer path.

M3 Increment 6 advances the bundled `software-basic` pack and workflow to `0.3.0`, adding
`agent_adapter` to each step's allowed actors. Existing locked initiatives retain their original
pack bytes and authority rules. `forge agent run <step> --adapter codex|claude` creates a normal
governed run, moves an eligible step to `in_progress`, and audits the provider execution separately
from output import and completion. Failure or timeout records `run-cancelled` and follows the
locked cancellation behavior. Success leaves the run active until the owner explicitly imports
the staged files and submits the worker claim with `forge complete --run-id <run-id>`.

Adapter execution does not satisfy any transition condition. Claims, declared checks, evidence,
and owner acceptance retain their existing records and authority requirements.

M3 Increment 7 places a fail-closed executable capability gate before adapter run creation.
`forge capability approve` previews the exact current invocation profile and requires `--apply`
before owner authorization is persisted. Every adapter run binds the selected approval; one-time
approval is consumed by run creation, and later revocation prevents future invocation without
rewriting history. Pack-data trust remains unable to grant executable authority.

M3 Increment 8 makes pack data trust reversible without rewriting the creation decision.
`forge pack inspect <pack-id>` displays the exact locked ID, version, digest, declared executable
capabilities, effective trust, and immutable history. `forge pack untrust` and `forge pack trust`
preview the proposed state and require `--apply` before the configured owner's decision is
persisted.

An untrusted pack blocks new workflow-dependent mutations, including manual and adapter run starts,
transitions, verification, imports, pause/resume, and successful closure. Read-only status,
history, pack inspection, capability governance, run inspection/cancellation, schema recovery, and
owner abandonment remain available. Restoring `trusted-data` trust re-enables the locked workflow;
it does not approve any declared executable capability.

M4 Increment 2 allows one required check on a step already `awaiting_verification` to be attempted
with `forge check run <step> <check> --validator <id>`. The validator attempt is state-neutral:
it does not move the step to `in_progress`, join workflow `active_run_ids`, or apply cancellation
transitions. Its exact approval-bound run and terminal check result are durable, while evidence,
`forge verify`, and owner acceptance remain later explicit commands.

M4 Increment 3 adds `forge scope amend` for a material owner change to initiative scope. The owner
declares the complete new effective scope, affected locked-workflow requirements and current
logical artifacts, plus the workflow step where work must restart. FORGE derives downstream stale
support and gates. A ready or worked return step becomes `invalidated`; a never-eligible return
step and untouched descendants remain or reset to `pending`. Any affected active run must be
cancelled first so the amendment never fabricates a terminal run outcome. Restarted work follows
the ordinary claim, check, evidence, verification, and acceptance sequence in full.
