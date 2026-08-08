# ADR-0006 — Artifact Revisions and Preservation Store

- **Status:** Accepted
- **Date:** 2026-07-13

## Decision

Artifacts have immutable SHA-256-bound revisions. Approval-, evidence-, acceptance-, and
closure-bound bytes are copied to `.forge/objects/sha256/` and archives reference preserved
objects rather than mutable paths alone.

## Consequences

Accepted history remains reproducible after working files change. M1 archival is explicitly
preliminary; production-grade integrity and interrupted-archive recovery arrive in M2.

