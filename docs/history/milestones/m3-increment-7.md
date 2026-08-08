# M3 Increment 7 — Executable Capability Authorization

## Authorized scope

- a built-in registry for exact Codex and Claude executable capability profiles;
- read-only `forge capability list` and `forge capability inspect` commands;
- preview-first, owner-only `forge capability approve` with one-time, version, and project scopes;
- owner-only `forge capability revoke` with immutable retained history;
- durable capability approval and revocation records plus journal events;
- fail-closed `forge agent run` authorization bound into every adapter `RunRecord`; and
- one-time approval consumption at governed run creation, including failed attempts.

## Explicit exclusions

Pack trust/untrust lifecycle changes, executable pack providers, validator execution, provider APIs,
background services, cross-process live cancellation, hostile-code isolation claims, automatic
verification/evidence/acceptance, automatic Git operations, and M4 work are not implemented.
Trusted pack data remains unable to authorize executable capability use.

## Design evidence

[ADR-0032](../adr/ADR-0032-executable-capability-authorization.md) records the exact-profile binding,
approval-scope semantics, one-time consumption, revocation, pack-trust separation, and remaining
boundaries. [Agent Adapters](../adapters.md) documents the operator workflow.

## Test evidence

Deterministic fake-provider tests cover default-disabled execution, exact-profile preview and
approval, successful authorized execution, one-time consumption after a failed attempt, revoked
approval rejection, durable run binding, staged-but-unapplied output, timeout handling, and the
existing source-run and import boundaries. Cross-record validation runs during every active-state
load and rejects capability record/event drift.

Final Windows validation recorded:

- 213 tests passed with 6 expected Windows symlink-privilege skips;
- Ruff and strict Pyright passed with no findings; and
- Hatchling produced both the source distribution and wheel.

## Stop point

Stop after exact executable capability approval, revocation, history, and adapter-run enforcement
are implemented and validated. Do not implement pack trust commands, validators, executable pack
providers, background execution, or Milestone 4 behavior.
