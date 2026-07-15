# ADR-0018: Resumable Atomic Abandonment

- Status: Accepted
- Date: 2026-07-14

## Context

Some governed initiatives must end without satisfying successful-closure gates. Treating that
outcome as closure would overstate checks and acceptance; deleting active state would lose owner
reasoning, unfinished work, risks, and history. Increment 6 already established a resumable atomic
archive transaction whose mechanics do not depend on success semantics.

## Decision

Add an owner-only `initiative-abandoned` terminal event and `AbandonmentRecord`. The record requires
a non-empty reason, unfinished-work summary, at least one unresolved-risk statement, the unfinished
step IDs, current governed artifact revisions, and archive destination. Abandonment is legal from
healthy active or paused state only when no governed run remains active. The owner must explicitly
cancel active runs first.

Abandonment does not require completed steps, passed checks, acceptance, clean Git, or unchanged
mutable working files. It preserves registered governed bytes and history as they stand. Its
manifest is terminal `abandoned`, references only abandonment IDs, and marks every object reference
unaccepted.

After the abandonment event commits, FORGE reuses the Increment 6 deterministic staging, hardened
manifest validation, atomic promotion, and active-state retirement phases. The same abandonment
request and idempotency key may resume a committed but incomplete transaction.

## Consequences

Closed and abandoned archives are mechanically consistent but semantically distinct. Neither can
reopen or accept later events. A committed abandonment is never rolled back or duplicated, and an
archive cannot validate if it mixes closure and abandonment identity fields.

Successor initiatives, migrations, damaged-journal repair, stale-lock removal, and generic
interrupted-command recovery remain outside this decision.
