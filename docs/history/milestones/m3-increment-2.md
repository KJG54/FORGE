# M3 Increment 2 — Managed Vendor Context References

## Authorized scope

- optional managed reference blocks in root `AGENTS.md` and `CLAUDE.md`;
- neutral-context digest binding and target-specific regeneration commands;
- read-only create/append/replace/no-change preview;
- explicit `--apply` confirmation with vendor and context race detection;
- exact preservation of every user byte outside the managed span;
- bounded UTF-8, regular-file, marker, symbolic-link, and atomic-write safety.

## Explicit exclusions

The `AgentAdapter` interface, manual adapter baseline, installed Codex or Claude discovery, version
compatibility, authentication diagnostics, process invocation, cancellation, output capture,
capability approval/revocation/execution, executable pack trust, vendor-block removal, and M4 work
are not implemented.

## Design evidence

[ADR-0027](../adr/ADR-0027-managed-vendor-context-references.md) records the digest-bound reference,
byte-preservation algorithm, preview/apply binding, refusal rules, and terminal-reference tradeoff.
[Canonical Agent Context](../agent-context.md) documents the current CLI workflow.

## Test evidence

Focused tests cover missing and empty targets, exact LF/CRLF prefix and suffix preservation,
independent Codex/Claude files, context-driven block replacement, idempotent no-change apply,
non-mutating preview, preview-output privacy, malformed/duplicate/inline markers, non-UTF-8 and size
limits, vendor/context races, CLI confirmation, canonical digest agreement, journal non-mutation, and
symbolic-link refusal where the platform permits link creation.

Final validation on Windows recorded:

- 192 tests passed with 6 expected symlink-privilege skips;
- Ruff and strict Pyright passed with no findings;
- isolated source and wheel builds passed with Hatchling 1.31.0; and
- a fresh environment installed the wheel and passed version/help, initialization, configuration,
  bundled-pack, initiative creation, non-mutating Codex/Claude previews, explicit managed-reference
  apply, repeat no-change behavior, canonical-file generation, and 45-schema export smoke checks.

## Stop point

Stop after managed vendor references are implemented and validated. Do not begin adapter
interfaces, tool discovery, external processes, or capability execution without the next explicit
increment authorization.
