# ADR-0061: Local Production-v1 Conversational Candidate

**Status:** Accepted

**Date:** 2026-08-01

**Milestone:** Local Production v1, L1

## Context

ADR-0059 selected public identity and publication channels for M7. ADR-0060 froze useful
`1.0.0` compatibility boundaries while that public-release initiative was active. Owner testing
subsequently showed that FORGE's governance mechanisms were sound but that routine use exposed too
much command ceremony. The owner also replaced the public-release objective with a personal,
local release for direct Codex and Claude Code workspace sessions on Windows.

The locked public workflow could not truthfully be reinterpreted because it required publication
approval, public publication, and public verification. That initiative was cancelled and archived
as abandoned. Its history remains evidence, not progress imported into this successor.

## Decision

### Release and identity boundary

- Production v1 is a feature-complete personal/local candidate for extended owner testing.
- `FORGE`, `forge-governance`, the `forge` package, and the `forge` command remain provisional
  local identifiers.
- The distribution and runtime remain `1.0.0` candidate inputs. They do not assert a public release.
- No public tag, PyPI or TestPyPI upload, GitHub Release, trusted publisher, public support channel,
  or formal naming clearance is required for local-v1 completion.
- Naming and legal review must reopen before commercialization, hosted operation, active marketing,
  public package or GitHub Release publication, or meaningful third-party adoption.
- Windows and the owner's intended Python environment are the primary acceptance boundary.
  Existing cross-platform checks remain supplementary engineering evidence, not a public support
  promise.

This decision supersedes ADR-0059's current public-release direction and the public tag, channel,
and support-commitment portions of ADR-0060. It retains ADR-0060's independent version domains,
`1.0.0` candidate identity, historical immutability, and backward-compatibility constraints.

### Conversational operating model

The default operator is a direct Codex or Claude Code workspace agent acting within the same-user
filesystem boundary. The owner speaks in ordinary language, reviews concise proposals and FORGE
receipts, and personally authorizes consequential owner actions. FORGE remains the authority for
its records; Git remains the authority for project file history; neither the agent nor FORGE
becomes an autonomous owner.

Owner ceremony is a procedural speed bump, not authentication or hostile-agent isolation. The
system must distinguish the authority authorizing a mutation from the operator that invoked it,
without claiming a security boundary that does not exist.

### Canonical transaction receipts

One receipt represents one command or atomic transaction. It contains:

- `Recorded ->` FORGE-rendered committed facts with the exact journal sequence range and all event
  IDs;
- `Means ->` FORGE-derived state, blockers, and legal next actions;
- optional `Read ->` agent judgment; and
- optional `Next ->` agent or owner action.

`Recorded` is never printed for an uncommitted refusal. An idempotent replay identifies the
original committed transaction and states that no new event was appended. Detailed history remains
the event-level inspection route. Agents quote `Recorded` and `Means` verbatim.

### Local scratchpad and recap

The advisory scratchpad is `.forge/local/conversation/scratchpad.md`. It is UTF-8 Markdown, at most
65,536 bytes, ignored by Git, mutable, and never a governance act, evidence source, permission
grant, or automatic archive input. It stores only non-derivable in-flight reasoning, discarded and
current hypotheses, unresolved owner questions, and explicitly ungoverned conversational
decisions. FORGE refuses symbolic, irregular, malformed, and oversized scratchpads when reading.

`forge recap` is a read-only warm-resume view. It derives authoritative position from validated
state, labels the repository-directory name as a non-canonical friendly label, reports governed
and scratchpad times separately, reconciles scratchpad initiative and journal metadata, labels all
local notes as mutable and ungoverned, and reports blockers and legal next actions. Formal
pause/resume remains the drift-aware long-gap mechanism.

### Protocol and mentoring

A versioned, repository-independent `forge agent protocol` view makes the protocol available before
initialization. After initiative creation, FORGE generates the same versioned protocol beside the
canonical context and references it from the managed `AGENTS.md` or `CLAUDE.md` marker block.
Owner-authored bytes outside that block remain unchanged.

`StepDefinition` may gain optional, default-empty per-profile explanation content. The active step's
content takes precedence, with existing workflow-level content as fallback. This additive change
must preserve old locks and update schemas, exports, pack validation, compatibility checks, and
tests. Mentoring is advisory, skippable, and cannot change authority or transitions.

### Operator provenance

Persisted mutation and claim records gain only the smallest additive, optional operator provenance
needed to distinguish owner shell, direct Codex, direct Claude, manual contributor, and registered
adapter operation. Existing authority identity and authorization checks remain intact. Missing
operator provenance preserves old-record compatibility, but newly agent-authored claims must not
be rendered as human-authored. Session references are local attribution, not authentication.

### Owner actions, plan changes, and successor briefs

Owner-personal actions include initialization, pack trust changes, initiative and successor
creation, acceptance and revocation, scope and governance decisions, capability and risk approval,
recovery or migration authorization, and terminal close or abandonment. Agents may perform routine
mechanics only within the accepted scope and must present exact owner commands and consequences at
owner gates.

Steering before a claim is ordinary conversation. After a claim, changes use supported append-only
revision, invalidation, revocation, cancellation, decision, or scope-amendment mechanisms. The
accepted implementation plan is stable; daily position belongs in the local scratchpad.

Milestone transition uses a separate `forge successor brief --archive <id>` view rather than
changing worker `forge handoff`. The brief derives terminal facts and lineage from the archive,
labels fresh Git observations separately, and includes only durable governed carryover. It is a
human-readable view, not a source of truth or imported acceptance.

## Compatibility and migration

The implementation may add optional fields with defined defaults to schema-`1.0` models when the
accepted design requires them. It must continue to read valid old locks and records and must not
rewrite either predecessor archive. No current archive, event, acceptance, or historical
`0.1.0a0` reference is migrated merely to support the conversational layer.

## Consequences

Local-v1 completion is measured by a conversationally usable exact local candidate and a practical
extended-testing campaign, not external publication. The scope retains demanding integrity,
security, compatibility, recovery, and exact-artifact checks while removing unrelated public
release ceremony.

The direct-agent experience becomes simpler, but same-user agents remain capable of invoking local
commands and editing files. Receipts and operator provenance improve honesty and reviewability;
they do not create cryptographic separation.

## Rejected alternatives

- **Finish the public workflow but skip publication.** Its locked steps would become false records.
- **Rewrite ADR-0059 or ADR-0060.** Historical decisions remain evidence of what was accepted then.
- **Reuse worker handoff as a milestone brief.** Its active-step assignment contract has different
  semantics and cannot operate on terminal archives.
- **Persist a mutable second state database for conversation.** Governed position remains derived
  from the journal; the scratchpad stores only non-derivable local reasoning.
- **Treat direct workspace agents as authenticated owners.** The local threat model cannot support
  that claim.
- **Create a new nine-step workflow solely to mirror implementation increments.** The existing
  framework-change workflow already provides the required scope, implementation, verification,
  risk, and closeout gates.
