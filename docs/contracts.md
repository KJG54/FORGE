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
acceptance, runs, handoffs and returned files, packs, capabilities, audit events, materialized
state, and project configuration.

Run:

```console
forge schema export --output schemas
```

The command writes one deterministic `*.schema.json` file per public model plus `index.json`.
Existing identical files are accepted. Changed generated files are not overwritten unless the
caller supplies `--force`; unrelated files in the destination are preserved.

Pre-v1 schemas may change only through the accepted ADR and migration policy. Exporting a schema
does not create public semantic-version compatibility before v1.0.0.

## Increment 4 record services

M1 Increment 4 persists `ArtifactRecord` snapshots and immutable `ArtifactRevision`, `Claim`,
`CheckResult`, and `EvidencePacket` records. Each record is cross-checked against its exact journal
event during restart. Artifact revision digests bind preserved bytes; check and evidence digests
bind canonical semantic content. Transition conditions cite governed supporting record IDs and are
re-derived before the CLI service advances a step.

The existing contracts intentionally keep acceptance separate. Increment 4 does not create or
interpret `AcceptanceRecord`, and revision events do not populate stale-dependency effects. Those
behaviors remain assigned to M1 Increment 5.
