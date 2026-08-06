# M2 Increment 7 — Resumable Atomic Abandonment and Archival

This increment adds abandonment and only the terminal abandonment/archive boundary.

Implemented:

- owner-only abandonment from healthy active or paused initiatives;
- required reason, unfinished-work summary, and unresolved-risk statements;
- explicit refusal while governed runs remain active, with cancellation required first;
- no false dependency on completion, checks, acceptance, clean Git, or mutable working bytes;
- preserved current governed artifact revisions and complete governed history;
- a distinct `AbandonmentRecord`, event type, manifest identity, status, and history view;
- object references that never claim abandoned bytes were accepted;
- deterministic staging, atomic promotion, validated active-state retirement, and same-key retry;
- tamper detection and duplicate-free recovery across promotion and retirement interruptions; and
- Windows, macOS, and Linux-compatible contracts and tests.

The abandonment event remains the governance commit point. Recovery never deletes or rewrites
journal history and never appends a second terminal event.

This increment does not create successor initiatives, migrate schemas, repair damaged journals,
delete stale locks, recover unrelated commands, or implement the hybrid Git policy. Those remain
separately authorized later increments.
