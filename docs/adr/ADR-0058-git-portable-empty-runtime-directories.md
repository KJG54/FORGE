# ADR-0058: Git-Portable Empty Runtime Directories

**Status:** Proposed

**Date:** 2026-07-29

**Boundary:** Pre-M7 Production-v1 prerequisite P0

## Context

Successful closure and abandonment retire terminal active state only after a hardened archive
validates. The transaction then recreates an empty `.forge/active/` directory as the local
no-active-initiative marker. Initialization also creates empty `.forge/local/` runtime
directories.

Git transports files, not empty directories, and `.forge/local/` is intentionally ignored.
Consequently, a clean checkout of a repository whose only initiative is archived has neither the
empty active marker nor the local runtime directories. Treating that absence as an interrupted
terminal transaction makes a valid archive-only repository unhealthy and prevents successor
creation even though no governed or recovery evidence is missing.

## Decision

Absence of `.forge/active/` represents the normal no-active-initiative state only when:

- every archive validates completely;
- no deterministic archive-staging directory exists; and
- no closed- or abandoned-active retirement marker exists.

Read-only status and diagnostics do not recreate missing directories. They continue to fail closed
for invalid archives, staging or retired markers, symbolic paths, non-directory paths, unexpected
active content, or terminal records still under `.forge/active/`.

The Git-ignored `.forge/local/` tree and its empty subdirectories are also recreatable runtime
structure rather than transported governance. Read-only inspection treats their absence as empty
local state while refusing irregular or symbolic replacements. Before a governed mutation acquires
the repository lock, FORGE safely creates the missing local lock directories. Successor creation
validates all archives and terminal markers first, then safely creates a missing empty active
directory immediately before writing new governed state.

Archive manifests, terminal events, completion receipts, preserved objects, archive digests, and
interruption-specific retry behavior remain unchanged. A staging or retired marker still requires
the exact terminal command and idempotency key; directory absence never clears or substitutes for
that evidence.

Selected archive status may reuse the already fully validated archive view produced while building
repository-wide summaries. This removes duplicate validation work without caching across commands
or weakening any archive check.

## Consequences

A clean Git checkout containing only valid archives is healthy, diagnosable, and capable of
creating a successor without a tracked placeholder. Git collaboration no longer depends on
untrackable empty directories.

Read-only commands remain read-only. The first later mutation recreates only the runtime
directories it requires. Unexpected active content and real interrupted terminal transactions
remain integrity errors, and immutable archive bytes are never repaired or rewritten.
