# ADR-0002 — Embedded Project Repositories

- **Status:** Accepted
- **Date:** 2026-07-13

## Decision

FORGE-enabled projects store governed configuration and records in ordinary files under
`forge.yaml` and `.forge/`. Local locks, secrets, caches, verbose runs, and staging remain under
ignored `.forge/local/` paths.

## Consequences

Projects remain portable and inspectable without hosted infrastructure. Initialization must be
non-destructive and preserve unrelated repository and vendor-file content.

