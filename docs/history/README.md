# Development record

This directory is FORGE's own development history: architecture decision records, milestone and
increment evidence reports, and the agent-to-agent handoff documents that carried work between
sessions. It exists for the people building FORGE. Nothing here is required reading for using
FORGE — start at the [documentation index](../README.md) or the repository README instead.

These documents are preserved records, not living documentation:

- **They are not rewritten.** Superseded decisions stay as evidence of what was true when they
  were recorded; later documents supersede them explicitly.
- **Paths inside older documents describe the repository layout at the time they were written.**
  This directory was created on 2026-08-06 by moving `docs/adr/`, `docs/handoffs/`, and
  `docs/milestones/` here; path references inside the moved documents were deliberately left
  unchanged.
- **One file did not move.** `docs/milestones/m6-report.md` remains at its original path because
  the immutable M6 initiative archive records that exact path for a registered artifact revision,
  and the working copy is kept byte-identical to the archived revision.

Contents:

- [`adr/`](adr/README.md) — architecture decision records ADR-0001 onward.
- [`handoffs/`](handoffs/) — session handoff documents, including the currently operative
  [Local Production-v1 closeout handoff](handoffs/local-production-v1-closeout-handoff.md).
- [`milestones/`](milestones/) — M0-M6 milestone and increment evidence reports and the Local
  Production-v1 L1-L9 boundary reports.
