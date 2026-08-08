# ADR-0016 — Explicit Pause and Resume

- **Status:** Accepted
- **Date:** 2026-07-14

## Decision

Only the configured repository owner may pause or resume an initiative. Pause is allowed only
from healthy active state while the repository mutation lock is held and no governed run remains
active. The owner supplies a non-empty reason.

The `initiative-paused` event binds the exact pre-pause materialized-state digest, current workflow
position, and legal next actions. Replay preserves those projections, sets lifecycle state to
`paused`, records the active pause-event identity, and permits only `resume`. Read-only status,
history, artifact, evidence, acceptance, decision, and run inspection remain available; normal
governed mutations are rejected before journal append.

The `initiative-resumed` event must reference the active pause event and contains a generated
summary of the objective, pause reason, workflow position, step states, and restored next actions.
Replay validates the reference, restores `active`, clears the pause identity, and deterministically
re-derives legal workflow actions.

## Consequences

Stopping a terminal or process never requires a lifecycle event, but an intentional governance
pause is explicit, attributable, restart-safe, and independent of chat history. Active runs must be
completed or cancelled before pause, preventing FORGE from presenting in-flight work as quiescent.

This decision does not add agent context generation, archive hardening, stale-lock removal,
migration, abandonment, or successor initiatives.
