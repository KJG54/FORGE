# Architecture

FORGE embeds governance state in an ordinary project repository. The CLI is the supported command
boundary; versioned records and a validated append-only journal provide durable authority. Project
artifacts remain ordinary files, while exact governed revisions are preserved by digest.

## Layered design

```text
CLI
 |
core services ---- adapters / pack validation / security policy
 |
contracts + canonical serialization
 |
storage: records -> event journal -> materialized snapshot
 |
ordinary repository + immutable object store + terminal archives
```

- `forge.cli` parses requests and maps stable error categories to exit codes.
- `forge.core` owns authorization, derived conditions, transitions, and transaction orchestration.
- `forge.contracts` contains strict schema-versioned public records.
- `forge.packs` loads untrusted declarative data and validates complete digests.
- `forge.adapters` isolates provider-specific worker preparation and process behavior.
- `forge.security` enforces path, import, and secret-screening policy.
- `forge.storage` supplies canonical bytes, atomic replacement, locking, records, journals,
  snapshots, receipts, migrations, and preserved objects.

Dependencies point inward toward contracts and storage primitives. Contract models contain no
workflow orchestration, and packs contain no Python execution.

## Source-of-truth hierarchy

For supported behavior, authority descends through:

1. accepted governing specification and explicit later owner decisions;
2. accepted ADRs;
3. validated versioned records and locked definitions;
4. the canonical hash-chained event journal;
5. reconstructable `state.json`;
6. caches, local diagnostics, generated context, and external tool views.

A snapshot, Git commit, chat, adapter, cache, or hosted service cannot overrule a valid journal and
its locked records. Git transports and reviews governed files but is not the governance ledger.

## Repository layout

```text
forge.yaml                         tracked project configuration and owner identity
.forge/
|-- active/
|   |-- events.jsonl               authoritative ordered active history
|   |-- state.json                 reconstructable materialized view
|   `-- ...                        locked definitions and immutable records
|-- objects/sha256/                preserved artifact bytes
|-- archive/<initiative-id>/       immutable closed or abandoned history
|-- idempotency/                   durable command receipts
`-- local/                         ignored locks, staging, captures, audit, cache, secrets
```

Exact subpaths are validated by the storage and record services. Operators should not repair them
manually. Governed state is Git-visible; machine-local and potentially sensitive diagnostics stay
under `.forge/local/`.

## Mutation transaction

The normal durable order is:

1. discover and validate the repository;
2. acquire the cross-process mutation lock;
3. validate configuration, locked records, preserved objects, the complete journal, and snapshot;
4. authorize the actor and derive the legal transition from current facts;
5. write immutable records and preserved objects;
6. append the canonical hash-chained event, which is the governance commit point;
7. atomically replace the reconstructable snapshot; and
8. persist the idempotency receipt.

An interruption before the event commit cannot authorize the intended mutation. An interruption
after it leaves authoritative history that narrow recovery or same-key retry can validate. FORGE
does not guess missing events or silently normalize unknown state.

Terminal closure, abandonment, migration, journal recovery, and stale-lock remediation use
specialized transactions documented in [persistence](persistence.md),
[closure and archives](closure-and-archives.md), [migrations](migrations.md), and
[recovery](recovery.md).

## Governance state machine

Packs declare workflow steps, but core services own the supported transitions:

```text
pending -> ready -> in_progress -> awaiting_verification
        -> awaiting_acceptance -> completed
```

Revision, revocation, or scope changes may move affected work to `invalidated` or reset untouched
descendants to `pending`. Cancellation can return safe work to `ready` or block it for owner
review. Pause changes initiative availability without changing completed facts. Closed and
abandoned initiatives are terminal.

Conditions are derived from current digest-bound records. Callers cannot assert that checks,
evidence, or acceptance exist.

## Trust boundaries

- The owner is the only authority for consequential owner decisions.
- Humans, agents, scripts, and validators are workers.
- Pack data trust authorizes exact declarative bytes only.
- Executable capabilities require separate exact owner approval.
- Imported output is untrusted until bounded staging and explicit application.
- A passing check supports review but cannot establish truth or acceptance.
- Same-user processes are outside FORGE's isolation claim.

See [the constitution](constitution.md), [security](security.md), and the accepted
[ADRs](history/adr/README.md) for decisions behind these boundaries.

## Compatibility and extension

Persisted contract schema compatibility and journal-format migration are explicit and separate.
The current pre-v1 inventory is documented in [compatibility](compatibility.md). Unknown fields,
future schema versions, mixed journals, and arbitrary development commits receive no implied
support.

Domain extension uses declarative packs. Worker integration uses the neutral in-tree adapter
protocol. New executable, storage, authority, trust, compatibility, or public CLI behavior
requires an ADR and owner-visible review.
