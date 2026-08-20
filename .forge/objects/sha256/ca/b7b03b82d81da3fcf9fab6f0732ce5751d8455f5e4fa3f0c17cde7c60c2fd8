# Canonical authority and specification lifecycle change scope

## Objective

Establish one current and discoverable account of FORGE authority while preserving the recovered
Production-v1 Master Implementation Specification as byte-identical historical evidence. A human
or agent should be able to distinguish current design authority, active locked rules, persisted
runtime truth, reference documentation, and disposable advisory views without interpreting an
obsolete planning handoff as current permission.

This artifact defines the proposed implementation boundary. It is a worker-authored draft, not an
owner decision, check, verification result, or acceptance record.

## Problem being corrected

The living Constitution delegates to an absent Production-v1 master specification. That document
has now been recovered, but its own status and instructions describe an earlier implementation-
planning phase rather than the current framework. At the same time, ADR-0004, the architecture
reference, and the documentation index use one "source of truth" label for different questions.
The resulting blended hierarchy can make a design document appear capable of overruling persisted
bytes or make an initiative-scoped decision appear to amend global architecture.

The remedy is a typed authority model and a concise current governing reference. Historical
records remain immutable; effective status and supersession are expressed separately.

## In scope

### 1. Preserve the recovered specification

- Copy the owner-supplied file byte-for-byte to
  `docs/history/specifications/FORGE-Production-v1-Master-Implementation-Specification.md`.
- Preserve SHA-256
  `ec0da4a895dd762e49746c6f029f6bfca251825e011363c53438e5034ccd764a` and record the
  source filename, owner-supplied provenance, recovery date, original declared status, current
  historical status, and superseding current reference in
  `docs/history/specifications/README.md`.
- Do not add front matter, banners, corrected links, or line-ending changes to the preserved file.
  All current-status explanation belongs in the adjacent index.

### 2. Record the typed authority decision

- Add `docs/history/adr/ADR-0062-typed-authority-and-specification-lifecycle.md`.
- Preserve ADR-0004's persisted-runtime ordering while defining separate authority types:
  normative design, persisted runtime/history, active locked rules, reference content, and
  derived advisory views.
- Define precedence only within a type and define how conflicts across types are classified. A
  document never silently repairs or overrules a persisted integrity fact.
- State that an owner decision applies only to its recorded question, outcome, scope, initiative,
  and required change-control context. An initiative-scoped decision does not silently amend
  global FORGE architecture; a global architectural change must say that it is global and satisfy
  the Constitution's ADR/change-control requirement.
- Identify exactly which earlier authority interpretation the ADR supersedes. Do not rewrite an
  accepted ADR merely to change its displayed historical status.

### 3. Create the current governing reference

- Add `docs/governing-specification.md` as the concise current entry point for FORGE purpose,
  invariants, typed authority, lifecycle boundaries, trust boundaries, compatibility/publication
  posture, and change control.
- Treat it as a maintained synthesis and navigation surface. It must point readers to the
  Constitution, effective ADR metadata, machine-readable contracts, and feature references rather
  than duplicating their full detail or creating new permissions.
- State the common invariant identically and prominently:
  `worker claim -> check -> evidence -> FORGE verification -> owner acceptance`.

### 4. Make the Constitution durable

- Update `docs/constitution.md` so its Authority section names the typed model and current
  governing reference rather than the missing master specification.
- Remove finished Milestone 1 mechanics from the living constitutional contract.
- Preserve those removed words and their provenance in a new historical note under
  `docs/history/milestones/`; do not modify existing historical milestone or ADR records.
- Keep the constitutional principles, security limitations, and change-control boundary intact
  unless ADR-0062 explicitly explains a narrowly necessary clarification.

### 5. Align architecture and documentation navigation

- Replace the blended source-of-truth list in `docs/architecture.md` with the same typed authority
  map and clear cross-type conflict rules.
- Align `docs/README.md` with that map and make `docs/governing-specification.md` the obvious
  maintainer/agent entry point.
- Add navigation from the historical specifications index and ADR index without presenting
  historical content as current instruction.

### 6. Add machine-readable ADR effective status

- Add `docs/history/adr/index.json` as the machine-readable catalog for every ADR through ADR-0062.
- For each ADR, record at least its number, title, path, date, recorded status, effective status,
  `supersedes`, and `superseded_by`. Keep the historical status written inside each ADR unchanged.
- Define and document the allowed values and relationship rules in
  `docs/history/adr/README.md`. The JSON catalog, not edits to historical ADR text, carries current
  effective status.
- Record partial supersession explicitly instead of falsely marking an entire ADR ineffective.

### 7. Add semantic documentation checks

- Add a deterministic documentation-consistency check under `tools/` with focused tests under
  `tests/`, and wire it into the existing local quality gate.
- The check must validate the governing-reference links and required authority vocabulary, the
  historical specification digest, complete ADR catalog coverage, valid ADR paths/status values,
  and reciprocal supersession relationships.
- Negative tests must demonstrate that missing catalog entries, invalid status or relationship
  metadata, a changed historical specification digest, and missing governing-reference links fail
  clearly.
- The check must not infer owner acceptance, rewrite documents, access the network, or inspect
  chat/local-secret content.

### 8. Record the already-completed dogfood closure status

- Update only the stale terminal-status statements and corresponding checkboxes in
  `docs/forge-improvement-roadmap.md` and `docs/friction-register.md` so they report that the
  separate Project-Basic-Test initiative closed and archived.
- Do not reinterpret that run as acceptance of this initiative or as proof that its observed UX
  friction has been fixed.

## Expected implementation surface

The implementation may create or modify only the following project targets, plus a narrowly
required existing quality-gate registration file if the repository's check architecture requires
it:

- `docs/governing-specification.md`
- `docs/constitution.md`
- `docs/architecture.md`
- `docs/README.md`
- `docs/history/specifications/README.md`
- `docs/history/specifications/FORGE-Production-v1-Master-Implementation-Specification.md`
- one new provenance-preserving note under `docs/history/milestones/`
- `docs/history/adr/ADR-0062-typed-authority-and-specification-lifecycle.md`
- `docs/history/adr/README.md`
- `docs/history/adr/index.json`
- `docs/forge-improvement-roadmap.md`
- `docs/friction-register.md`
- one documentation-consistency tool under `tools/`
- focused documentation-consistency tests under `tests/`
- the existing local quality-gate registration file, only if needed to invoke the new check

Any additional target requires owner-visible scope review before it is changed.

## Compatibility and preservation boundaries

- This phase changes documentation authority and its validation, not FORGE runtime contracts,
  record schemas, journal format, state machines, CLI commands, exit meanings, pack identities,
  protocol version, or framework version.
- Existing `.forge/archive/`, `.forge/objects/`, accepted ADR bodies, milestone reports, handoffs,
  and digest-bound release evidence remain byte-identical.
- Active workflow and pack locks continue to govern the initiative that locked them. A later
  global document does not silently change those rules mid-initiative.
- The repository remains public source with an unreleased development-project posture. This phase
  neither authorizes publication nor resolves release/version/install language assigned to a later
  roadmap phase.
- Git history, FORGE governance, remote CI, and owner acceptance remain distinct facts.

## Explicit exclusions

- `project-basic` workflow, facilitation, profile, prompt, or approval-batching changes
- selecting or changing the CLI default workflow
- release/version identity, installation routes, tags, packages, or public-release authorization
- CLI decomposition, private Typer imports, machine-readable CLI output, or startup optimization
- journal validation or persistence optimization
- security defaults, CI security jobs, branch protection, GitHub metadata, or repository settings
- cleanup of branches, distributions, caches, virtual environments, or `.forge/local/`
- changelog reconstruction, broad documentation reorganization, broad link repair, or unrelated
  friction-register maintenance
- mutation of terminal archives or existing historical records

## Stop condition

Stop after the exact authority documents, ADR and ADR metadata, navigation updates, semantic
checks, and dogfood closure-status corrections have been imported, independently checked,
verified, and presented for explicit owner acceptance. Do not begin Phase 2 or any excluded work.

