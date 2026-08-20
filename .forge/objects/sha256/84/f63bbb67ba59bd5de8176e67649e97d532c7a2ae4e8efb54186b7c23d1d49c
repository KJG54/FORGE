# ADR-0062: Typed Authority and Specification Lifecycle

**Status:** Accepted

**Date:** 2026-08-17

## Context

ADR-0004 correctly ordered persisted artifact bytes, preserved bytes, binding digests, the
validated journal, locked rules, and materialized state. Later living documents reused the phrase
"source of truth" for normative design documents and blended the two questions into one list. The
Constitution also delegated to a Production-v1 Master Implementation Specification that was absent
from the repository and, once recovered, described an earlier pre-implementation planning phase.

That ambiguity creates two unsafe readings: a design document could appear to overrule a persisted
integrity fact, or an initiative-scoped owner decision could appear to amend global architecture.
Generated context, guides, and chat could also be mistaken for permission instead of orientation.

## Decision

### Five authority types

FORGE defines five separate authority types:

1. **Normative design** answers what FORGE is intended and permitted to do.
2. **Persisted runtime/history** answers what exact bytes, records, and governed events exist.
3. **Active locked rules** answer what one initiative may do under its exact pack and workflow
   locks.
4. **Reference content** explains supported behavior without creating permission.
5. **Derived advisory views** support orientation but remain disposable and non-authoritative.

Precedence applies within a type. Across types, FORGE classifies the disagreement and uses an
explicit supported mechanism; it never silently flattens the types into a universal ranking.

### Normative design precedence and applicability

Within normative design:

1. the Constitution supplies durable principles and the required change-control boundary;
2. an applicable recorded owner decision settles only its exact question, outcome, scope,
   initiative, and change-control context;
3. effective accepted ADRs state architecture, with a newer explicit supersession controlling
   only its declared scope;
4. machine-readable contracts control the exact fields and values they define;
5. the current governing specification is the maintained synthesis and navigation surface; and
6. feature references and guides explain the model without creating authority.

An initiative-scoped owner decision does not silently amend global FORGE architecture. A global
architectural decision must declare that applicability and satisfy every constitutional
change-control requirement, including an ADR where required. Owner ceremony and caller labels do
not authenticate identity.

### Persisted runtime/history

ADR-0004's persisted ordering is retained unchanged: current artifact bytes, preserved historical
bytes, binding digests, the validated journal, locked rules, and materialized state. Disagreement
is an integrity error and cannot be repaired by a document, generated context, Git commit, cache,
agent, or chat assertion.

This ADR partially supersedes ADR-0004 only where its title and terse wording can be read as one
untyped hierarchy for every kind of authority. It does not supersede ADR-0004's persisted ordering
or integrity consequence.

### Active locks and global change

Exact active pack and workflow locks govern the initiative that recorded them. A later global ADR
or guide does not mutate a lock mid-initiative. Affected work uses the supported scope amendment,
migration, terminal, or successor mechanism and preserves the earlier history.

### Current and historical specifications

`docs/governing-specification.md` is the current concise governing entry point. It is a maintained
synthesis, not a new authority above the Constitution, applicable owner decisions, effective ADRs,
or exact contracts.

The recovered Production-v1 Master Implementation Specification is preserved byte-for-byte under
`docs/history/specifications/`. Its original authority statement and agent instructions are
historical evidence. They do not authorize current implementation or publication.

### ADR recorded status and effective status

Accepted ADR text remains immutable. `docs/history/adr/index.json` records both:

- `recorded_status`, copied from the historical ADR; and
- `effective_status`, derived from explicit accepted supersession relationships.

The catalog records reciprocal full or partial supersession without rewriting the earlier ADR.
Semantic checks validate coverage, identities, allowed values, and relationships.

## Consequences

A beginner or agent receives one current front door and can determine which kind of authority is
relevant before applying precedence. Runtime integrity remains fail-closed. Active initiatives
remain protected from silent global-rule drift. Historical specifications and ADRs remain
inspectable without being mistaken for current instructions.

The ADR index becomes maintained machine-readable content. Any new ADR or explicit supersession
must update it and pass documentation consistency checks. The governing specification and
authority maps must change together when the model changes.

## Rejected alternatives

- **Keep one universal source-of-truth list.** It ranks design intent, persisted facts, locks, and
  disposable views as if they answered the same question.
- **Make the recovered master specification current again.** Its implementation-planning status,
  public-v1 assumptions, and receiving-agent instructions are historical.
- **Let the newest owner statement override globally.** A decision without recorded applicability
  and required change control cannot safely amend architecture.
- **Edit earlier accepted ADR status lines.** That would rewrite historical decision text instead
  of recording effective status and supersession separately.
- **Generate the governing specification from chat or agent memory.** Neither is authoritative or
  reproducible.

