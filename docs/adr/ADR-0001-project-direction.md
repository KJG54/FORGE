# ADR-0001 — FORGE Project Direction and Governing Principles

- **Status:** Accepted
- **Date:** 2026-07-13
- **Provenance:** Reconstructed from the approved Production-v1 specification on 2026-07-13.
  This is the first authoritative FORGE ADR and is not represented as a recovered historical
  document.

## Decision

Build FORGE as a Python 3.12+ local CLI and repository-embedded governance framework. FORGE
governs how replaceable worker output becomes trusted project state; it does not perform the
work or own consequential decisions. The provisional source package and CLI are `forge`.

Public names, distribution names, domains, and marks remain provisional until the owner records
naming clearance. No package is published under production branding before that gate.

## Consequences

The product remains local-first, inspectable, provider-neutral, domain-neutral, and owner-led.
Hosted services, direct model APIs, autonomous coordination, and user interfaces are outside v1.

