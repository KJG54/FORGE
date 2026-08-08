# ADR-0011 — Pre-v1 Compatibility Policy

- **Status:** Accepted
- **Date:** 2026-07-13

## Decision

Before the release candidate, schemas may change only through recorded ADRs and migrations. Once
an approved milestone persists a schema, fixtures and migration tests accompany incompatible
changes. Unsupported future schemas are rejected. Public semantic-version stability starts at
v1.0.0.

## Consequences

Early contracts can improve without silent breakage or accidental public stability commitments.

