# M3 Increment 8 — Owner-Controlled Pack Data Trust

## Authorized scope

- read-only `forge pack inspect` for exact available or active locked pack identity and trust
  history;
- preview-first, owner-only `forge pack trust` and `forge pack untrust` for the active locked pack;
- immutable later `PackTrustDecision` records and `pack-trust-changed` journal events;
- effective trust derived from the creation decision and append-only decision chain;
- fail-closed workflow-dependent mutation while the pack is untrusted;
- preserved inspection, retrust, capability governance, run cancellation, recovery, and owner
  abandonment paths; and
- archive preservation plus cross-record and inventory validation of the full trust history.

## Explicit exclusions

Executable pack providers, validator execution, provider APIs, background services, cross-process
live cancellation, implicit cancellation on untrust, automatic verification/evidence/acceptance,
automatic Git operations, and M4 work are not implemented. `trusted-data` remains unable to grant
executable capability approval.

## Design evidence

[ADR-0033](../adr/ADR-0033-owner-controlled-pack-data-trust-lifecycle.md) records the append-only
decision chain, effective-state derivation, fail-closed service boundary, recovery routes, and
continued separation from executable authorization. [Packs, initiatives, and manual
runs](../workflows.md) documents the operator workflow, and [Persistence](../persistence.md)
documents the durable layout and validation rules.

## Test evidence

Tests cover owner-only and exact-pack scope, non-mutating CLI preview, applied untrust and history,
workflow mutation refusal, status guidance, duplicate-state refusal, restart-safe retrust,
paused-initiative trust changes, decision tamper detection, and abandonment plus archive reload
while the final effective state is untrusted. Interrupted receipt recovery proves that a committed
trust event remains duplicate-free and retryable. Existing creation-time trust, capability
separation, run cancellation, archival, migration, CLI, and lifecycle coverage remains green.

Final Windows validation recorded:

- 220 tests passed with 6 expected Windows symlink-privilege skips;
- Ruff and strict Pyright passed with no findings; and
- Hatchling produced both the Increment 8 source distribution and wheel, and an isolated local
  wheel-target smoke test loaded the packaged CLI and reported `0.1.0a0`.

## Stop point

Stop after the owner-controlled data-only pack trust lifecycle, history, enforcement, safe recovery
paths, archival, and validation are implemented. Do not implement validators, executable pack
providers, background execution, provider APIs, automatic cancellation, or Milestone 4 behavior.
