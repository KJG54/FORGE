# ADR-0048: Canonical Long-Gap Resumption Summaries

**Status:** Accepted

**Milestone:** M5 Increment 5

## Context

M2 pause and resume already preserve workflow position and record a short sentence containing the
objective, pause reason, step states, and restored actions. The Production-v1 roadmap requires a
long-paused initiative to resume without chat history and calls for compact summaries derived from
canonical state, open decisions, artifacts, evidence, and next actions.

A summary must not become a second authority source. It must also avoid repository-wide discovery,
embedding artifact content, reviving stale evidence, or changing the workflow merely because it
describes the workflow.

## Decision

Derive one deterministic, human-readable resumption summary from the validated paused initiative:

- objective and current effective scope;
- governing pause reason;
- locked workflow step, purpose, state, and all step-state projections;
- every current open decision by ID, type, question, and chosen outcome;
- every current artifact by role, repository-relative path, logical ID, exact revision ID and
  number, content digest, and working-copy current/changed observation;
- every non-stale evidence packet by ID, purpose, reference counts, and packet digest; and
- the exact legal workflow actions preserved by the governing pause event.

The summary includes references and digests, never artifact content. It reads only validated
FORGE-managed records and the already registered artifact paths needed for the existing
current/changed check. It performs no unrelated filesystem discovery.

Paused `forge status` derives and displays the summary without mutation. `forge resume` derives the
same text before appending the resume event. New resume events declare the
`canonical-records-v1` profile, include a canonical summary digest, and bind that digest plus the
referenced artifact, decision, and evidence identities and digests into the hash-sealed event.
Replay verifies the summary text against its recorded digest.

Evidence already marked stale by canonical state is omitted. Current artifact revisions replace
superseded revisions in the summary. Missing, corrupt, inconsistent, or mismatched canonical
records fail closed through existing active-state and record validation.

The summary is a derived explanation, not a governance record or permission. It cannot satisfy a
claim, check, evidence requirement, verification transition, gate, or acceptance requirement.

## Consequences

An owner returning after a long gap can inspect the paused status, understand the current governed
position and exact references, and then resume without depending on prior chat history. The resume
event preserves what was shown at the transition boundary.

Existing M2 resume events remain valid: replay applies the new digest rule only when the event
declares the canonical summary profile. No persisted model changes, migration, new file, or public
schema are required; the export remains at 51 models.

Summaries may report that a registered working copy changed, but they do not register a revision or
repair the drift. Bounded filesystem discovery, semantic relevance selection, search indexing,
shared pack conformance, and later M5 work remain separate increments.
