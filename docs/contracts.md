# Versioned Contracts

M1 Increment 1 defines the Production-v1 data vocabulary without implementing the services that
act on those records. This separation keeps persisted shapes inspectable while preventing model
validation from becoming hidden lifecycle orchestration.

## Contract rules

Every independently persisted contract:

- carries `schema_version: "1.0"`,
- rejects unknown fields and unsupported future versions,
- uses UUIDs for immutable record identity,
- requires aware timestamps where time is recorded,
- uses portable repository-relative paths,
- remains provider-neutral,
- exports a self-contained JSON Schema.

Initiative-scoped governance facts also carry their actor ID, UTC timestamp, initiative-local
event sequence, authorization basis, optional correlation and run IDs, tool version where
applicable, and affected records or digests. M1 Increment 2 persists audit events in validated
sequence and rebuilds `state.json` through an injected reducer. Workflow-specific reduction and
authorization remain assigned to Increment 3.

## Schema inventory

The public registry covers identity and authority, initiatives, workflows and gates, artifacts
and revisions, provenance, decisions and governance changes, claims, checks, evidence,
acceptance, runs, handoffs and returned files, packs, capabilities, audit events, idempotency
receipts, recovery records, materialized state, and project configuration.

Run:

```console
forge schema export --output schemas
```

The command writes one deterministic `*.schema.json` file per public model plus `index.json`.
Existing identical files are accepted. Changed generated files are not overwritten unless the
caller supplies `--force`; unrelated files in the destination are preserved.

Pre-v1 schemas may change only through the accepted ADR and migration policy. Exporting a schema
does not create public semantic-version compatibility before v1.0.0.

## Increment 4 and 5 record services

M1 Increment 4 persists `ArtifactRecord` snapshots and immutable `ArtifactRevision`, `Claim`,
`CheckResult`, and `EvidencePacket` records. Each record is cross-checked against its exact journal
event during restart. Artifact revision digests bind preserved bytes; check and evidence digests
bind canonical semantic content. Transition conditions cite governed supporting record IDs and are
re-derived before the CLI service advances a step.

M1 Increment 5 persists and validates `AcceptanceRecord`, `ApprovalRevocation`, `DecisionRecord`,
and `DecisionSupersession`. Their source files remain immutable: effective revocation,
supersession, and staleness are derived from append-only records and journal events.

M1 Increment 6 uses `AgentHandoff`, `AgentResult`, and `ReturnedFile` at the manual worker boundary.
Handoffs remain disposable local views. A validated `AgentResult` is persisted only when its staged
files are explicitly applied; the result and every imported artifact revision are then cross-checked
against one `result-imported` event. Import records acknowledge provenance, not approval.

M1 Increment 7 adds `ClosureRecord`, `ArchiveManifest`, `ArchivedFile`, and
`ArchivedObjectReference`. The owner closure record is journal-bound governance. The archive
manifest is a read-only preservation index whose digest covers its semantic fields and whose file
entries cover the exact archived bytes. This is preliminary M1 tamper evidence, not the external
hash-chain root or corruption-hardening guarantee assigned to M2.

M2 Increment 3 adds `IdempotencyReceipt` and its exact event references. Each receipt binds one
repository-wide command key and request digest to the IDs, initiative IDs, sequences, and hashes
of every event committed by the completed command.

M2 Increment 4 adds `RecoveryRecord`. It binds one owner-attributed reconstruction to the prior
journal head, observed snapshot condition, exact preserved bytes when present, and its committed
`integrity-recovered` event.

M2 Increment 13 adds `CommandRecoveryRecord`. It binds the owner reason, interrupted request
identity, exact original event references, reconstructed receipt digest and completion time, and
the distinct `command-recovered` provenance event.

M2 Increment 5 extends `MaterializedState` with the active pause-event identity. Pause and resume
remain journal events rather than mutable records: the pause event binds the exact resumable state
digest and the resume event binds its governing pause plus a durable resumption summary.

M2 Increment 6 keeps `ClosureRecord` stable and makes `ArchiveManifest.preliminary` an explicit
compatibility flag. Existing M1 manifests remain `true` with declared limitations; newly hardened
archives are `false` with no preliminary limitations. The closure event, record, manifest, file
inventory, and preserved-object references must identify the same terminal transaction.

M2 Increment 7 adds `AbandonmentRecord`. It binds the owner, terminal event, explicit reason,
unfinished-work summary, unresolved risks, unfinished step IDs, current governed artifact
revisions, and archive destination. `ArchiveManifest` now identifies exactly one terminal record
kind: closure fields for `closed`, or abandonment fields for `abandoned`. Abandoned object
references are always marked unaccepted so archive inspection cannot imply closure success.

M2 Increment 8 activates the existing `InitiativeReference` contract for canonical `successor-of`
links. Each link binds an archived initiative UUID to `.forge/archive/<initiative-id>` and is also
embedded in the successor creation event and affected-record sets. Successor artifact reuse creates
a new `ArtifactRecord` and `ArtifactRevision`; its `ProvenanceRecord` binds the predecessor
initiative, terminal revision, content digest, and archived revision reference.

M2 Increment 10 adds `MigrationRecord`. It binds configured-owner authorization and the stable
migration service actor to one registered source/target edge, the exact preserved source path,
size and digest, the source event count, and the single `schema-migrated` commit event. The first
edge changes the event-journal format while retaining contract schema version `1.0`.
