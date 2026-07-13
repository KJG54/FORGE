# ADR-0009 — Pack Trust and Capability Trust

- **Status:** Accepted
- **Date:** 2026-07-13

## Decision

Pack trust has only untrusted and trusted-data states. Executable capabilities have separate,
explicit approval scopes and remain disabled by default. Pack data never executes merely because
the owner trusts its declarations.

## Consequences

Domain extension remains data-driven without becoming an implicit code-execution channel.

