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

M4 Increment 11 additionally binds the complete canonical `Claim` digest into each new
`claim-recorded` event. Restart recomputes that digest so assertion, limitation, attribution, or
dependency tampering fails closed. Earlier claim events remain readable under their original
actor, sequence, run, step, exact-revision, and affected-digest bindings; they still cannot satisfy
verification or acceptance without independent current checks and evidence.

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

M2 Increment 14 adds `LockRemediationRecord`. It is a project-scoped, local-only authorization
record binding the configured owner, reason, idempotency request, exact stale-lock digest and size,
observed owner metadata, token digest, and preserved evidence path. It has a public schema but is
not an initiative governance event because mutation locks contain host runtime state.

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

M3 Increment 1 adds `CanonicalAgentContext`. Its strict top-level fields match the specification's
bounded context categories. Nested step, selected-input, decision, and return-contract shapes are
provider-neutral. The persisted JSON is a tracked generated view, not a governance record, and its
schema exports as `canonical-agent-context.schema.json`.

M3 Increment 3 adds frozen provider-neutral adapter request, plan, operation, manifest, and
diagnostic values plus the structural `AgentAdapter` protocol. These values are transient service
boundaries rather than persistence contracts, so they do not change the public schema bundle.
Existing handoff, result, run, event, snapshot, configuration, and archive models remain stable.

M3 Increment 4 extends only those transient adapter values with canonical context, working
directory, and standard-input fields needed for deterministic Codex preparation. It introduces no
new persisted model or exported schema; the public schema bundle remains unchanged.

M3 Increment 5 reuses those same transient values for Claude Code and factors provider-independent
local-CLI mechanics behind the adapter boundary. No persisted contract changes, and the public
schema bundle remains unchanged.

M3 Increment 6 extends the transient invocation request and plan with an isolated output directory,
source run ID, timeout, and captured exit status. The existing `RunRecord`, `AuditEvent`, and
`AgentResult` contracts represent the durable worker identity, execution event, and untrusted
return bundle without new fields. `adapter-run-executed` is a new journal event type interpreted by
the existing reducer and record validator. No public model or JSON Schema changes, so the exported
schema bundle count remains unchanged.

M3 Increment 7 adds `CapabilityApproval` and `CapabilityRevocation` public contracts. Approval binds
the capability definition digest, provider and detected version, resolved executable, exact fixed
arguments, working-directory rules, environment access, side-effect class, owner rationale, scope,
and approval event. Revocation binds a later owner event and reason to the retained approval.
`RunRecord.capability_approval_ids` makes executable authorization auditable at the attempt boundary.

M3 Increment 8 reuses the existing `PackTrustDecision` and `PackTrustState` public contracts. Later
trust and untrust records use the same immutable model as initiative creation and are linked through
state-neutral `pack-trust-changed` events. No public model or JSON Schema changes are required.

M3 Increment 9 adds no persisted contract or exported schema. Its acceptance scenario composes the
existing context, handoff, run, capability, result, artifact, claim, audit event, and materialized
state contracts to prove that all built-in workers share one governance boundary.

M4 Increment 1 adds the public `LocalValidatorDefinition` contract and nests those declarations
under `ProjectConfiguration.capabilities.local_validators`. The definition contains only an
executable plus ordered arguments—never a shell string—and binds working-directory, timeout,
expected-output, environment-name, and side-effect-risk metadata. Existing capability approval and
revocation contracts remain unchanged.

M4 Increment 2 reuses `RunRecord` for a validator attempt committed before process creation and
stores it separately from workflow work runs. `CheckResult` gains additive optional execution
bindings for approval, invocation digest, normalized execution state, and bounded local stdout and
stderr capture paths, sizes, and digests. Existing manual check records keep those fields empty and
retain their prior result-digest payload. The schema version and exported schema count remain
unchanged.

M4 Increment 3 activates the existing public `ScopeAmendment` contract without changing its schema.
`changed_scope` is the complete new effective scope. The record binds owner rationale, validated
workflow requirement IDs, current logical artifact IDs, derived invalidated check, gate, and
acceptance IDs, and the explicit workflow return step. Its inherited affected-record and digest
fields bind the complete derived stale set and current affected artifact content.

M4 Increment 4 activates the existing public `WorkflowDeviation` contract without changing its
schema. The record binds declared and actual behavior, owner rationale, an explicit review
requirement, and the exact locked-workflow digest. Review reuses `DecisionRecord` with the fixed
type `workflow-deviation-review` and exactly one affected deviation ID; no mutable reviewed flag or
second approval contract is introduced.

M4 Increment 5 activates the existing public `EmergencyOverride` contract without changing its
schema. The record binds one qualified locked-workflow requirement or gate, owner rationale,
residual risk, temporary/permanent status, review requirement, and the exact workflow digest. It
remains state-neutral and is not a substitute for the separate `RiskAcceptance` contract.

M4 Increment 6 activates the existing public `RiskAcceptance` contract without changing its
schema. The record binds exactly one current `EmergencyOverride`, copies that record's residual
risk, and preserves the exact override and workflow digests through inherited governance fields.
Rationale, residual impact, and an optional manual review condition remain explicit owner facts.
The record is state-neutral and grants no workflow progression authority.

M4 Increment 7 reuses the existing public `ApprovalRevocation` contract for risk-acceptance
withdrawal without changing its schema. `approval_id` identifies the exact `RiskAcceptance`;
inherited affected-record and digest fields bind that acceptance, its emergency override, and
their canonical digests. The immutable revocation is state-neutral and cannot alter the original
acceptance record.

M4 Increment 8 reuses the existing public `DecisionRecord` and `DecisionSupersession` contracts
without changing their schemas. A reserved `decision-withdrawal` replacement carries fixed
semantics, identifies the prior decision through supersession, and binds its canonical digest plus
inherited affected records and digests. Current, withdrawn, superseded, and stale status remains
derived from validated history rather than persisted by rewriting `DecisionRecord.status`. The
exported schema count remains unchanged.

M4 Increment 9 adds the public immutable `RunCancellationRecord`. It binds one exact `RunRecord`
through the inherited `run_id`, its canonical digest, the locked step cancellation policy,
side-effect class, actor, reason, and source/destination states. Adapter-attributed cancellations
also bind the preceding terminal execution event ID and hash. The public schema bundle now contains
49 models.

M4 Increment 10 adds the public `LocalAuditEvent` plus its category and severity enums. The record
contains project, optional initiative, configured-owner, operation, refusal, stable error, detail-
digest, and tool metadata. It deliberately has no raw-detail, argument, environment, content, or
governance fields. The public schema bundle now contains 50 models.

M5 Increment 2 uses the existing `PackManifest.template_paths` field without changing its schema.
Template bytes and their derived digests are internal validated pack values rather than independent
persisted contracts. The complete pack digest binds them, while exact copies under governed active
state and archive file inventories preserve the bytes. Explanation and general data-resource paths
remain unsupported. The exported schema bundle remains at 50 models.

M5 Increment 3 adds `StructuralValidatorDefinition`, with nested `StructuralTextRule`, as a strict
data-only pack-author contract. Definitions bind an ID, version, declared check, purpose, artifact
roles, allowed text media types, exact headings, non-empty field prefixes, and limitations. They
cannot express a process, command, hook, environment, network access, or arbitrary evaluation.
`PackManifest.data_resource_paths` now accepts only definitions satisfying this contract;
explanation resources remain unsupported. Existing persisted contracts do not change and require
no migration. The exported schema bundle now contains 51 models.
