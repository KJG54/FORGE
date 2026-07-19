# Journal and Materialized State

M1 Increment 2 establishes the preliminary filesystem persistence boundary without claiming the
M2 guarantees that do not yet exist.

## Authority and transaction order

`events.jsonl` is the mutation commit point. Each schema-versioned event is deterministic JSON,
occupies exactly one newline-terminated record, belongs to one initiative, and has a sequence
number exactly one greater than the preceding event. M1 rejects duplicate event IDs, mixed
initiative IDs, partial records, invalid schemas, and event hashes that would falsely imply M2
hash chaining.

A governed mutation follows this order:

1. Read and validate the existing journal and snapshot.
2. Refuse the mutation when replay and `state.json` disagree.
3. Validate the candidate event as the next record.
4. Append, flush, synchronize, and reread the journal record. At this point the event is committed.
5. Replay the full journal through the caller-supplied state reducer.
6. Write `state.json` to a temporary file beside the destination.
7. Validate and synchronize the temporary snapshot, atomically replace the destination, and
   verify its exact bytes.
8. Compare the resulting snapshot with deterministic replay.

This ordering cannot make two files atomically durable as one operation. If a process stops after
the journal commit but before snapshot replacement, the journal remains authoritative and the
missing or stale snapshot is reported as `integrity_error`. FORGE does not silently normalize the
snapshot.

## Replay boundary

The storage layer owns sequence validation, replay mechanics, journal-head projection, snapshot
serialization, and comparison. It accepts a reducer function rather than interpreting workflow
events itself. The domain-neutral lifecycle reducer and authorization rules belong to M1
Increment 3.

## M2 Increment 1 integrity chain

New journals use the canonical serialization and SHA-256 chain defined by
[ADR-0012](adr/ADR-0012-canonical-event-hash-chain.md). Every read validates event content hashes,
previous-hash links, sequence and initiative identity, and complete-record termination. Replay
binds `state.json` to the exact journal-head sequence and hash.

Complete M1 journals with empty hash fields remain readable but are read-only until an explicit
registered migration preserves the original bytes and records provenance. Active-snapshot recovery
requires a fully hash-chained journal. Increment 14 handles stale locks through a separate explicit
operation that never changes the journal.

## M2 Increment 2 mutation locking

Supported governed mutations acquire the repository-wide lock defined by
[ADR-0013](adr/ADR-0013-cross-process-mutation-lock.md). Exclusive creation prevents overlapping
processes, ownership metadata makes contention inspectable, and token verification prevents one
owner from releasing another owner's lock. Stale status is diagnostic only: this increment never
silently removes a lock.

## M2 Increment 3 idempotency

Supported governed CLI mutations use the journal-bound protocol in
[ADR-0014](adr/ADR-0014-journal-bound-command-idempotency.md). Reserved metadata is applied before
event hash sealing. On successful command completion, `.forge/idempotency/` stores one validated
receipt binding the request to every exact committed event hash. The key namespace spans active
and archived initiatives, so successful closure remains safely replayable after active-state
retirement.

An identical retry returns the existing event references. Different parameters with the same key
are rejected. If events exist without their completion receipt, mutation stops with an explicit
recovery requirement. Increment 13 can reconstruct a receipt only after proving a registered
complete command pattern and its exact active-state effects.

## M2 Increment 4 active-snapshot recovery

The owner may run `forge recover --reason "..."` when the active `state.json` is missing, invalid,
or disagrees with deterministic replay. [ADR-0015](adr/ADR-0015-explicit-active-snapshot-recovery.md)
requires the entire journal to validate as one complete canonical hash chain before any recovery
write. FORGE also validates all governed records and content-addressed objects referenced by that
history.

If an observed snapshot exists, FORGE preserves its exact bytes and digest under
`.forge/active/recovery-snapshots/`. It writes an immutable recovery record, appends an
owner-attributed `integrity-recovered` event as the commit point, and only then atomically rebuilds
`state.json`. A retry using the same idempotency key may finish this recovery event's snapshot and
receipt without appending another event.

Recovery refuses healthy snapshots, legacy M1 journals, damaged or truncated journals, ambiguous
history, missing governed records, and missing preserved objects. It does not truncate history,
repair journal bytes, resolve unrelated incomplete commands, retire archives, or remove locks.

## M2 Increment 14 explicit stale-lock remediation

The owner-only `forge remediate-lock` operation implements the explicit diagnostic remediation
required by [ADR-0025](adr/ADR-0025-explicit-stale-lock-remediation.md). It runs outside the ordinary
mutation wrapper, proves a strictly valid mutation lock belongs to a dead same-host PID, and uses a
second exclusive guard that ordinary mutations check both before and after lock acquisition.

The operation writes its key-bound authorization record before atomically renaming the exact stale
lock into `.forge/local/lock-remediations/`. That rename is the removal commit point and retains the
source bytes, digest, size, owner metadata, owner reason, and request identity for local inspection.
Same-key retry resumes only the matching prepared operation or replays validated evidence. It never
appends an initiative event or changes a journal, snapshot, receipt, archive, or governed record.

## M2 Increment 5 pause and resume

The owner-only lifecycle events defined by
[ADR-0016](adr/ADR-0016-explicit-pause-and-resume.md) preserve workflow position without copying or
rewriting state. `initiative-paused` binds the complete pre-pause materialized-state digest,
current step, and legal next actions. Replay retains the step, artifact, decision, evidence, and
acceptance projections while changing lifecycle state to `paused` and limiting the next action to
`resume`.

`initiative-resumed` must reference the active pause event. Replay restores the active lifecycle
and re-derives legal workflow actions. Both events use the existing journal commit, snapshot,
locking, and idempotency protocols.

## M2 Increment 6 atomic closure layer

Successful closure appends an owner-authorized terminal event and writes the final snapshot before
building a complete archive in a deterministic sibling staging directory. The manifest covers each
archived file by digest and size and references content-addressed artifact objects. The staging tree
is validated before atomic promotion, and the promoted archive is validated before active state is
atomically renamed and retired.

The event is the governance commit point; the overall multi-directory operation is resumable rather
than falsely presented as one filesystem primitive. A retry with the same close parameters and
idempotency key rebuilds staging or finishes retirement without duplicating the terminal event. The
completion receipt is written only after the archive is valid and `.forge/active` is empty.

## M2 Increment 7 atomic abandonment layer

The owner-authorized `initiative-abandoned` event is the abandonment commit point. It binds a
durable `AbandonmentRecord` containing the reason, unfinished work, unresolved risks, unfinished
step IDs, current governed artifact revisions, and destination. Replay transitions either healthy
active or paused state to terminal `abandoned`; active runs make the event invalid.

Abandonment reuses deterministic staging, manifest validation, atomic promotion, and active-state
retirement. A matching retry can rebuild staging or finish retirement without appending a second
terminal event. The manifest and archive validator require abandonment-specific IDs and prohibit
closure IDs, so this path cannot be confused with successful closure.

## M2 Increment 10 schema migration framework

The registered framework in [ADR-0021](adr/ADR-0021-explicit-schema-migration-framework.md) selects
only explicit directed source/target edges. Its first edge preserves a valid legacy M1 journal
byte-for-byte, records its digest and owner authorization, deterministically seals the existing
events, and adds one `schema-migrated` event attributed to the stable migration service.

The whole migrated journal is validated before one atomic replacement. That replacement commits
the migration; snapshot reconstruction and idempotency receipt completion are safely resumable.
Restart validation compares the preserved source with the unsealed semantic form of every migrated
prefix event. Archives are validated but never rewritten.

## M2 Increment 11 hybrid Git boundary

Git is an optional collaboration and transport layer, not persistence authority. Initialization
preserves existing `.gitignore` content and adds root-scoped negations for `forge.yaml` and
governed `.forge/**` data followed by an exclusion for `.forge/local/`.

Diagnostics validate the effective ignore result and read-only index state. Ignored governed paths
and already tracked local-only paths fail closed; visible but untracked governed files are owner
action warnings. Without Git, FORGE retains identical filesystem lifecycle behavior. The optional
clean-close configuration first validates this hybrid policy so ignored authority-bearing files
cannot make a dirty repository appear clean.

## M2 Increment 12 conservative journal recovery

`forge recover` may now replace a damaged active journal only when the final non-empty record is
mechanically identifiable as JSON truncated at end-of-file and every preceding record forms a
complete valid M2 hash chain. Complete records missing a newline, malformed or schema-invalid
records, invalid hashes or ordering, legacy history, and damage without a complete prefix remain
immutable because their intended history is ambiguous.

Before replacement, FORGE preserves the exact damaged journal under
`.forge/active/recovery-journals/`, records the exact tail and snapshot identities, and validates
all governance supported by the valid prefix. The atomic replacement contains that prefix plus one
`journal-recovered` event; it is the commit point. Snapshot and receipt completion are resumable
with the same idempotency key. Preserved recovery evidence remains governed and is revalidated on
restart and archival.

## M2 Increment 13 interrupted-command recovery

The owner-only `forge recover-command` path handles one exact event group that committed before its
receipt. It requires a contiguous active-journal tail, a registered complete event-type pattern,
one incomplete target, valid governed records and objects, and an atomic pre-command or current
snapshot observation. This prevents a single event from falsely completing a command that requires
two events.

One `command-recovered` event commits an immutable `CommandRecoveryRecord`; snapshot refresh and
the reconstructed target receipt follow. The receipt remains bound only to the original command
events, while the recovery event is bound to a distinct recovery idempotency key. Same-key retry
finishes post-commit writes without duplication. Partial transactions and specialized archive,
migration, or journal-recovery operations are preserved for their own recovery paths.

## M3 Increment 1 generated agent context

`.forge/active/context/current.json` and `current.md` are deterministic tracked projections of the
validated active initiative. They are regenerated under the repository mutation lock but append no
journal event and carry no independent governance authority. The JSON contract contains only the
approved canonical-context categories; selected artifact inputs are represented by bounded role,
path, digest, and media-type metadata rather than copied bytes.

Each file is replaced atomically. The pair is intentionally regenerable rather than a multi-record
transaction: if interruption leaves one view newer, `forge agent context --target neutral` derives
both again from authoritative governed state. Archive retirement naturally preserves the last
generated context with the active tree; generation never reads unrelated archives.

## M3 Increment 2 root vendor references

`AGENTS.md` and `CLAUDE.md` remain ordinary project files outside `.forge/`. FORGE manages only one
standalone marker span after a read-only preview and explicit `--apply`. The managed bytes reference
the active canonical files and bind the exact canonical JSON digest; all bytes outside the span are
preserved exactly.

Vendor references are derived, not journaled, replayed, or archived with an initiative. Apply runs
under mutation exclusion, binds the previewed vendor and context digests, regenerates canonical
context, rechecks the vendor bytes, and atomically replaces the one selected root file. A terminal
archive does not silently edit or remove a root vendor reference.

## M3 Increment 6 adapter-run execution

The normal `step-transitioned` begin event and immutable `RunRecord` remain the durable start of an
adapter attempt. A later state-neutral `adapter-run-executed` event binds the run, adapter identity,
step, exit status, normalized execution state, canonical-context digest, and optional local staged
result ID. Replay requires the referenced run to be active. Expected failures are followed by the
existing `run-cancelled` event; successful execution remains associated with the active run until a
claim transition ends it.

Provider workspace, raw stdout/stderr, and import staging remain below `.forge/local/` and are not
governance authority. The event records identities and outcomes, not provider bytes. After explicit
import, ordinary artifact revisions and content-addressed objects preserve accepted project bytes
under the existing transaction rules. The synchronous command uses normal mutation locking and
idempotency receipts, but an unexpected interruption is diagnosed rather than automatically
restarting a model process.

## M3 Increment 7 capability authorization

`.forge/active/capability-approvals/<approval-id>.json` stores the configured owner's immutable
authorization of one exact inspected capability profile. `.forge/active/capability-revocations/`
retains later immutable revocations. Their `capability-approved` and `capability-revoked` events are
state-neutral governance history and are included in terminal archives.

An executable adapter `RunRecord` now binds matching `capability_ids` and
`capability_approval_ids`. One-time use is derived from the existence of that immutable run record,
so no mutable counter can be rolled back or reused after a failed launch. Replay and cross-record
validation require approval events to precede the run, reject prior revocation, and reject a second
use of `approved-once`. Local provider output remains below `.forge/local/` and outside authority.
