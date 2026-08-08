# M5 Increment 5 — Canonical Long-Gap Resumption Summaries

## Authorized scope

- derive one deterministic resumption summary from validated canonical records;
- include effective scope, pause reason, workflow position, all step states, open decisions,
  current artifact revision references, current non-stale evidence, and restored legal actions;
- expose the same read-only summary through paused `forge status`;
- bind new resume summaries and their referenced records/digests into the hash-sealed resume event;
- reject summary tampering during replay;
- exclude stale evidence and superseded artifact revisions; and
- preserve replay compatibility for earlier M2 resume events.

## Explicit exclusions

New authoritative records, summary files, schema migrations, artifact content embedding, unrelated
filesystem scanning, semantic ranking, search indexes, automatic artifact revision, workflow
mutation, decision making, evidence creation, verification, acceptance, shared pack conformance,
bounded filesystem discovery, and later M5 work are not implemented.

## Authority and trust

The summary is a presentation-only view of already validated governed state. It grants no
authority and cannot satisfy a workflow condition. Only the configured owner may pause or resume;
the existing reducer and authorization services remain unchanged except for verifying the new
summary digest when its explicit profile is present.

Artifact references expose repository-relative paths, IDs, revision numbers, and digests—not file
content. Evidence already marked stale has no current resumption role and is omitted.

## Persistence, compatibility, and failure semantics

Paused status derives the summary without writing anything. Resume stores the rendered text,
profile, and canonical digest in the existing `initiative-resumed` event and binds the referenced
records and digests through existing event fields. The journal hash seals the complete event.

Legacy resume events without the new profile continue under their accepted M2 validation rules.
No public model, schema version, file layout, or migration changes; the schema export remains 52.
Malformed canonical bindings, missing records, digest mismatches, and invalid pause metadata fail
closed before resume.

## Design evidence

[ADR-0048](../adr/ADR-0048-canonical-long-gap-resumption-summaries.md) records the derivation,
authority, event-binding, compatibility, and no-discovery decisions.

## Validation evidence

- focused canonical-summary, status/resume equivalence, staleness, tamper, and compatibility
  coverage: 3 passed;
- adjacent continuity, artifacts/evidence, decision, scope, journal/state, and CLI coverage:
  44 passed;
- cumulative M5 increment coverage: 22 passed;
- partitioned complete-suite coverage: 299 passed with 6 expected Windows privilege-based
  symlink skips and no failures;
- Ruff clean, strict Pyright clean with 0 errors and 0 warnings, and `git diff --check` clean;
- source distribution and wheel built successfully with Hatchling 1.31.0; and
- a clean Python 3.14 installed-wheel smoke proved paused status/resume summary identity,
  canonical digest binding, evidence-bearing replay/restart health, and all 52 schema exports;
- remote CI is intentionally not inspected or claimed until M5 closeout.

## Stop point

Stop after canonical long-gap summaries are available from paused status and hash-bound resume.
Do not implement filesystem discovery, semantic context ranking, indexing, shared conformance, or
later M5 behavior.
