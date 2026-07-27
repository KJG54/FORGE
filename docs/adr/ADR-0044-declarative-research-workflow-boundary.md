# ADR-0044: Declarative Research Workflow and Epistemic Boundary

**Status:** Accepted

**Milestone:** M5 Increment 1

## Context

The Production-v1 roadmap requires a bundled `research-basic` pack covering question framing,
planning, evidence collection, synthesis, verification, review, and closure. FORGE must demonstrate
that this domain uses the existing core without introducing research-specific lifecycle state or
allowing structural automation to claim factual truth.

Research sources, citations, and internally consistent claims may still be inaccurate, incomplete,
biased, outdated, or unsuitable for the declared purpose. A workflow check therefore cannot turn
source presence or traceability into semantic or factual authority.

## Decision

Ship `research-basic` as one bundled, declarative, data-only pack with a seven-step workflow:
`frame`, `plan`, `collect`, `synthesize`, `verify`, `review`, and `close`.

The workflow uses only the existing domain-neutral pack, workflow, artifact, claim, check, evidence,
verification, acceptance, run, journal, recovery, and archive contracts and services. It introduces
no new persisted model, event type, transition, authority class, executable capability, migration,
or recovery procedure.

Every research check requirement is explicitly structural. Passing one may establish that declared
records are present or traceable, but it does not establish source quality, citation correctness,
methodological validity, privacy compliance, semantic accuracy, or factual truth. Current governed
evidence, the normal verification transition, and configured-owner acceptance remain separately
required.

The owner must explicitly trust the exact validated pack bytes as data when creating an initiative.
That trust never grants process execution. Human contributors and agent adapters may perform
declared work and submit claims under the locked workflow, but only the configured owner may record
acceptance or terminal decisions.

Pack templates, executable structural validators, shared conformance infrastructure, Minimal and
Mentored presentation, long-gap resumption changes, and filesystem context discovery remain later
M5 increments.

## Consequences

Research initiatives can use the same supported command and persistence surface as software
initiatives, while existing initiatives retain their exact locked pack and workflow bytes. Pack
inventory, safe-YAML, digest, reachability, authority, journal, restart, and archive validation
apply unchanged.

The first research pack is intentionally usable without a template or validator executable. Owners
must create and review its declared artifacts and checks explicitly. Later templates or validators
must preserve the non-truth boundary and require their own bounded design and validation.
