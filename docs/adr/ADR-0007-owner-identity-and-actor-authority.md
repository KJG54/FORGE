# ADR-0007 — Owner Identity and Actor Authority

- **Status:** Accepted
- **Date:** 2026-07-13

## Decision

Every governed action carries an actor and authorization basis. Consequential owner actions are
available only through owner-authorized service paths. Adapter and imported content cannot
assert owner authority.

## Consequences

FORGE enforces governance within supported commands but does not claim cryptographic identity or
same-user process isolation.

