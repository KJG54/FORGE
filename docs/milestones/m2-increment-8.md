# M2 Increment 8 — Successor Initiative Creation

This increment adds successor creation and explicit predecessor artifact reuse only.

Implemented:

- owner-authorized successors with new immutable initiative IDs;
- one or more canonical closed/abandoned archive predecessor references;
- repository-wide archive validation before successor mutation;
- duplicate, unknown, self, tampered, and incomplete-transaction refusal;
- creation-event and affected-record binding for predecessor lineage;
- fresh pack trust, workflow, journal, snapshot, step state, and governance records;
- no inherited artifacts, checks, evidence, decisions, progress, staleness, or acceptance;
- exact terminal predecessor artifact reuse through new manifest-verified registrations;
- persisted provenance validation and predecessor archive immutability; and
- API, CLI, single-predecessor, multi-predecessor, tampering, and restart coverage.

This increment does not expand archived status/history presentation, migrate schemas, repair
damaged journals, delete stale locks, recover unrelated commands, or implement hybrid Git policy.
Those remain separately authorized later increments.
