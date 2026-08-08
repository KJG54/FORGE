# ADR-0053: Audience-Oriented Documentation Map

**Status:** Accepted

**Milestone:** M6 Increment 4

## Context

M1 through M5 produced detailed references organized around implementation increments. The
release-candidate roadmap requires complete user, pack-author, adapter-author, architecture,
security, troubleshooting, and recovery documentation. Copying detailed rules into seven new
manuals would create competing descriptions of authority, persistence, and recovery.

## Decision

FORGE will keep accepted ADRs, strict contracts, and the existing feature references as canonical
detail. A documentation index and audience guides provide stable task-oriented paths into those
sources:

- the user guide connects installation, initialization, lifecycle, continuity, terminal outcomes,
  and failure handling;
- pack and adapter author guides state their distinct supported extension boundaries;
- architecture and security guides explain cross-cutting structure and trust;
- troubleshooting routes stable error categories to read-only diagnosis and exact recovery; and
- the recovery reference remains the sole procedural authority for active-state repair.

Guides must state explicit non-claims and link to the canonical source instead of weakening or
silently generalizing it. Repository-local tests verify the audience inventory and local links.

## Consequences

Readers gain one discoverable entry point without a new documentation generator, hosted service,
runtime dependency, public contract, or CLI behavior. Maintainers must update both the canonical
feature page and affected audience routes when behavior changes.

Documentation conformance proves inventory and navigation, not technical correctness, usability,
fresh-user success, security completeness, or owner acceptance. Human walkthrough and
distribution-based rehearsal remain M6 closeout evidence.

## Rejected alternatives

- **Rewrite every feature as a standalone audience manual.** This would duplicate precise
  compatibility, persistence, and recovery semantics and increase drift risk.
- **Treat the chronological README and milestone records as the user manual.** They are valuable
  evidence, but they do not provide task-oriented reader journeys.
- **Adopt a documentation framework in this increment.** A generator, theme, hosted deployment, or
  new dependency is unnecessary for the repository-local release-candidate boundary.
