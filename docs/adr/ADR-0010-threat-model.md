# ADR-0010 — Threat Model and Same-User Limitation

- **Status:** Accepted
- **Date:** 2026-07-13

## Decision

FORGE provides integrity checks, auditability, path and import controls, explicit trust, and
supported-command authorization. It does not defend against a malicious process with the owner's
filesystem permissions.

Secret screening blocks known locations and recognizable patterns as defense in depth, not as a
guarantee. Owners must review imported and governed content.

## Consequences

Documentation and errors must not imply sandboxing, complete secret discovery, multi-user
authentication, or adversarial same-account isolation.

