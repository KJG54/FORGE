# M2 Increment 5 — Explicit Pause and Resume

## Authorized scope

- owner-only `forge pause --reason` and `forge resume` commands;
- pause only from healthy active state while the repository mutation lock is held;
- refusal while any governed run is active;
- exact digest binding of pre-pause resumable state and workflow position;
- paused lifecycle projection with inspection and recovery available but normal mutations blocked;
- resume bound to the active pause event with deterministic restoration of legal actions;
- durable long-gap resumption summary independent of chat history;
- restart, authorization, active-run, mutation-refusal, inspection, and idempotency coverage.

## Explicit exclusions

This increment does not generate full agent context, delete stale locks, migrate schemas or legacy
journals, harden archive promotion, resolve unrelated interrupted commands, abandon initiatives,
or create successors. Those remain separately authorized later increments.
