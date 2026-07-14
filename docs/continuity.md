# Pause and Long-Gap Resume

Use an explicit pause when governed work should remain intentionally inactive across a review,
handoff, or substantial time gap:

```console
forge pause --reason "Waiting for owner review" \
  --idempotency-key pause-owner-review
```

Pause is owner-only and requires a healthy active initiative with no active governed runs. Complete
or cancel any active run first. FORGE records the exact resumable-state digest and keeps the current
workflow position, records, and evidence unchanged.

While paused, `forge status`, `forge next`, `forge history`, and record inspection commands remain
available. Normal work mutations are refused, and `resume` is the only lifecycle action:

```console
forge status
forge history --event-type initiative-paused
forge resume --idempotency-key resume-owner-review
```

Resume validates the journal, snapshot, governed records, and active pause identity before
restoring operation. The CLI prints a durable summary containing the objective, pause reason,
workflow position, step states, and restored legal actions so work can continue without prior chat
history.

An ordinary terminal or computer shutdown does not require `forge pause`; repository persistence
already survives process interruption. Pause expresses owner intent and temporarily disables
normal governed mutation.
