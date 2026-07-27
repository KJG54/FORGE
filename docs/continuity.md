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

M5 Increment 5 makes the long-gap summary available before mutation through paused `forge status`.
It is derived only from validated canonical records and contains:

- objective and effective scope;
- pause reason, workflow position, purpose, and all step states;
- current open decisions;
- current artifact paths, IDs, exact revisions, digests, and working-copy observations;
- current non-stale evidence packet references and digests; and
- the legal workflow actions preserved at pause.

The summary never embeds artifact content or scans unrelated repository files. Stale evidence and
superseded artifact revisions are excluded. Resume derives the same summary, records its canonical
digest and exact record bindings in the hash-sealed `initiative-resumed` event, then restores
operation. This makes long-gap continuation independent of prior chat history without turning the
summary into authority.

Earlier M2 resume events remain replayable under their original rules. A summary does not satisfy
claims, checks, evidence, verification, gates, or owner acceptance.

An ordinary terminal or computer shutdown does not require `forge pause`; repository persistence
already survives process interruption. Pause expresses owner intent and temporarily disables
normal governed mutation.
