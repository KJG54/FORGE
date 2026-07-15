# ADR-0017: Resumable Atomic Successful Closure

- Status: Accepted
- Date: 2026-07-14

## Context

M1 committed the terminal closure event before archive construction and active-state retirement.
That preserved governance truth but an interruption left terminal state under `.forge/active` and
required unsupported manual recovery. M2 already supplies hash chaining, cross-process locking,
and journal-bound idempotency.

## Decision

The `initiative-closed` event remains the irreversible governance commit point. After it commits,
FORGE builds a deterministically named same-filesystem staging tree, validates a hardened manifest,
atomically promotes the archive, then atomically renames and retires active state. The archive must
validate before active retirement begins.

`forge close` may resume its own incomplete idempotency key. A same-request retry validates the
committed closure record and event, rebuilds incomplete staging, accepts only an exactly matching
hardened archive, and finishes retirement before the idempotency receipt is written. Existing M1
manifests remain readable and explicitly preliminary; new manifests are non-preliminary.

## Consequences

No multi-directory filesystem primitive is claimed. Instead, each individual promotion is atomic
and the overall transaction is safely resumable from durable governed state. A committed closure
is never rolled back or duplicated. Temporary and retired trees are removed only during the
explicit matching close retry after their governed source or archive has validated.

Abandonment, successors, migrations, damaged-journal repair, stale-lock removal, and generic
interrupted-command recovery remain outside this decision.
