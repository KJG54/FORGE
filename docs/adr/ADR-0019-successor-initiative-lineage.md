# ADR-0019: Successor Initiative Lineage

- Status: Accepted
- Date: 2026-07-14

## Context

Terminal initiatives cannot reopen, but governed work may legitimately continue, branch, or merge.
Reusing the terminal identity would make history mutable; copying its state would falsely inherit
checks and approval. The existing `InitiativeReference` contract anticipated explicit lineage.

## Decision

When archives exist, initiative creation requires one or more explicit predecessor IDs. FORGE
validates every archive, canonicalizes selected links as `successor-of`, and binds them into the new
initiative record, creation event metadata, and affected-record sets. The successor receives a new
identity, journal, snapshot, workflow lock, pack-trust decision, and initial state.

No governed state or approval is inherited. Exact terminal artifact bytes may be reused only by a
new artifact registration naming the predecessor revision. FORGE verifies the revision against a
declared predecessor's archive manifest and requires the working bytes to match before recording
new provenance.

## Consequences

Lineage is durable and inspectable while predecessor archives remain immutable. Multi-predecessor
successors are supported, and successors can form an acyclic history because only existing archives
may be referenced. Reused bytes still require all checks and acceptance in the new initiative.

Expanded archive views, schema migration, damaged-journal repair, stale-lock removal, unrelated
interruption recovery, and hybrid Git policy remain outside this decision.
