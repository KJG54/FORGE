# Canonical authority and specification lifecycle requirements

## Acceptance boundary

These requirements define the candidate outcome for this bounded framework change. Passing checks
or satisfying a worker claim does not establish FORGE verification or owner acceptance. The owner
must review and accept the exact registered revisions separately.

## Required outcomes

### R1 — Historical specification identity

The repository contains
`docs/history/specifications/FORGE-Production-v1-Master-Implementation-Specification.md` with
SHA-256 `ec0da4a895dd762e49746c6f029f6bfca251825e011363c53438e5034ccd764a` and the same
byte length as the owner-supplied source. A byte comparison with that source passes. No content was
inserted into or removed from the preserved file.

### R2 — Historical provenance and status

`docs/history/specifications/README.md` identifies the source filename and owner-supplied origin,
records the preserved digest, distinguishes the document's original declared status from its
current historical status, names the current governing reference, and warns agents that the
preserved implementation instructions are not current permission.

### R3 — Typed authority ADR

ADR-0062 defines all five authority types and their boundaries:

1. normative design authority;
2. persisted runtime/history authority;
3. active locked-rule authority;
4. reference content; and
5. derived advisory views.

It preserves ADR-0004's runtime ordering, distinguishes precedence within a type from conflicts
across types, identifies explicit supersession relationships, and states that integrity conflicts
fail visibly rather than being silently reconciled.

### R4 — Owner-decision applicability

ADR-0062 and the governing reference state that a recorded owner decision is authoritative only
within its recorded applicability. An initiative-scoped decision cannot amend global architecture
unless the record explicitly has that scope and the Constitution's required change control is
satisfied. The documents do not treat chat history, an operator label, or a command receipt as
authenticated owner identity.

### R5 — One current governing entry point

`docs/governing-specification.md` is linked from `docs/README.md`, `docs/constitution.md`, and
`docs/architecture.md`. It concisely states FORGE's purpose, primary audience, public-source and
unreleased-development posture, core authority invariant, typed authority map, lifecycle/trust
boundaries, and change-control route. It links to detailed authority instead of contradicting or
silently replacing it.

### R6 — Durable Constitution

`docs/constitution.md` no longer points to an absent master specification or describes completed
Milestone 1 mechanics as a current constitutional process. The removed milestone text is preserved
with provenance in a new historical note. The twelve principles, security limitations, and ADR
change-control requirements remain present and semantically consistent.

### R7 — Consistent architecture and documentation navigation

`docs/architecture.md`, `docs/README.md`, the Constitution, the governing reference, the ADR index,
and the historical specifications index use the same authority-type names and do not publish a
single blended hierarchy. A beginner or fresh agent can reach the current governing reference from
the documentation front door and can identify historical material before following instructions
inside it.

### R8 — Machine-readable ADR effective status

`docs/history/adr/index.json` parses deterministically and contains exactly one catalog entry for
every ADR file through ADR-0062. Each entry has a unique ADR number and path, valid recorded and
effective statuses, a real date and title, and explicit `supersedes` and `superseded_by` arrays.
Relationships are reciprocal, references resolve, and partial supersession is represented without
falsely changing the entire ADR's historical status.

`docs/history/adr/README.md` explains the metadata fields, allowed values, immutability boundary,
and which surface answers "what was recorded then" versus "what is effective now."

### R9 — Semantic checks fail closed

The new documentation-consistency check:

- passes against the intended repository state without network access;
- verifies the historical specification digest and expected path;
- verifies ADR catalog coverage, uniqueness, statuses, paths, and reciprocal supersession;
- verifies required links to the governing reference and the shared five-stage authority
  invariant; and
- emits actionable failures for each tested negative case.

Focused tests cover at least a missing ADR entry, invalid status, broken/nonreciprocal supersession,
historical-specification digest drift, and a missing governing-reference link.

### R10 — Dogfood closure status is factual and narrow

The roadmap and friction register state that the separate Project-Basic-Test initiative closed and
was archived after all workflow steps were accepted. They do not claim its friction is resolved,
import its progress into this initiative, or change unrelated entries.

### R11 — Preservation and scope containment

- Existing accepted ADR bodies and existing files under `docs/history/` remain unchanged except
  for the expressly allowed ADR README update and newly added files.
- Existing `.forge/archive/` and `.forge/objects/` bytes remain unchanged.
- No runtime source, contract, workflow, pack, protocol, version, installation, security, GitHub
  setting, or release-publication behavior changes.
- The final changed-file inventory fits the implementation surface in `change-scope.md`; any
  exception received owner-visible review before mutation.

## Required validation

The verification report must identify the exact candidate revisions and record, at minimum:

1. byte length, SHA-256, and direct byte comparison for the recovered specification;
2. the deterministic documentation-consistency check;
3. focused positive and negative documentation-consistency tests;
4. repository Markdown link/navigation validation for all changed living documents and new
   historical indexes;
5. the existing local quality gate, including the new semantic check;
6. `git diff --check` and an explicit changed-file inventory;
7. `forge doctor`, reported separately as repository-integrity evidence; and
8. the full local test suite unless a specific limitation is recorded and reviewed.

Remote GitHub Actions, if publication is separately authorized later, must be observed against the
exact commit and reported separately. Local results must not be described as remote CI evidence.

## Owner review questions

Before accepting implementation, the owner should be able to answer yes to all of the following:

- Can I find one current governing entry point without treating the historical master
  specification as present-day instructions?
- Can I tell which rule applies when persisted bytes, an active lock, an ADR, a guide, generated
  context, and chat disagree?
- Does the model preserve owner authority without allowing an initiative-local choice to mutate
  global architecture implicitly?
- Are historical bytes and historical decision text preserved honestly?
- Do the checks detect the specific authority drift this phase is intended to prevent?
- Did the change remain inside Phase 1 and leave later roadmap decisions open?

## Stop condition

After the exact registered outputs satisfy these requirements and receive independent checking and
FORGE verification, stop for explicit owner acceptance. Do not progress into release identity,
installation, product-default, UX, security, cleanup, CLI, or performance work.

