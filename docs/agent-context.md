# Canonical Agent Context

M3 Increment 1 adds the provider-neutral source for future manual and adapter integrations. It does
not install or invoke Codex, Claude, or any other worker.

Run:

```console
forge agent context --target neutral
```

FORGE validates the active initiative and writes deterministic views to:

- `.forge/active/context/current.json`;
- `.forge/active/context/current.md`.

These files are generated and tracked by the hybrid Git policy. They are not journal events,
decisions, evidence, or acceptance, and they never replace the authoritative governed records from
which they are derived.

## Included information

The context contains only the objective, active step, approved scope, relevant workflow selection
constraints, active decisions, worker permissions and prohibitions, required outputs, expected
claims/checks/evidence/acceptance boundary, return contract, and known blockers.

The active step lists only governed artifacts whose roles are declared in that step's
`required_inputs`. Each selected input exposes its role, repository-relative path, current digest,
and media type. File content is not copied into the context. A worker may use those paths, but the
digest makes stale working bytes detectable before execution.

If a selected input is absent or no longer matches its registered revision, FORGE still generates
an inspectable context, records the condition under `known_blockers`, and emits no permitted worker
actions. The owner must register the missing or changed artifact through the normal workflow before
using the context for work.

## Leakage boundary

Generation is allowlist-based. It does not crawl or include:

- ordinary unrelated project files or directories;
- `.env` or environment dumps;
- `.forge/local/`, including `.forge/local/secrets/`;
- archived initiatives;
- ignored content;
- non-selected artifact paths or content;
- superseded decisions.

The JSON contract is public and exported as `canonical-agent-context.schema.json`. Both generated
views are replaced atomically one file at a time while the repository mutation lock prevents a
concurrent supported mutation. Re-run the command to regenerate both views after any interruption or
governed state change.

## Deferred targets

`--target codex` and `--target claude` are deliberately recognized but refused in Increment 1.
Managed `AGENTS.md`/`CLAUDE.md` references, preview and confirmation, adapter diagnostics, adapter
invocation, capability approval, and executable pack trust belong to later bounded M3 increments.
The existing `forge handoff` and staged `forge import-result` workflow remains the manual baseline.
