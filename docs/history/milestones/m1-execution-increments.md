# Milestone 1 Internal Execution Increments

These increments make the approved M1 vertical slice observable and reviewable without creating
additional owner gates. A material scope, architecture, persistence, or trust change still stops
work for owner review.

1. **Contracts and repository initialization:** versioned contracts, schemas, configuration,
   owner bootstrap, non-destructive initialization, and safe paths.
2. **Journal and state:** atomic primitives, ordered events, replay, materialized snapshots, and
   integrity mismatch detection.
3. **Workflow transitions and authority:** pack loading/locking, initiative creation, actor
   authorization, transitions, manual runs, status, and next actions.
4. **Artifacts and evidence:** immutable revisions, content preservation, claims, basic checks,
   evidence registration, and dependency references.
5. **Acceptance and invalidation:** owner-only acceptance/revocation and stale propagation after
   revisions, supersession, or revocation.
6. **Handoff and safe import:** neutral handoffs, staged results, path/size/schema/secret
   safeguards, previews, collision handling, and atomic registration.
7. **Preliminary closure and preservation:** lifecycle closure, exact accepted-byte preservation,
   archive inspection, and command-level immutability. Documentation must label this preliminary;
   M2 owns hash chains, interruption safety, recovery, concurrency, and corruption hardening.
8. **End-to-end acceptance:** restarted-process software walkthrough plus the unchanged-core
   synthetic non-software workflow and full M1 evidence report.

Secret detection throughout M1 is explicitly heuristic: known secret locations and recognizable
patterns are blocked or warned on, while owner review remains required.

