# M2 Increment 11 — Hybrid Git Policy

This increment completes the M2 Git collaboration and transport boundary.

Implemented:

- a root-scoped hybrid `.gitignore` block that exposes `forge.yaml` and governed `.forge/**`
  records while excluding `.forge/local/`;
- byte-preserving, newline-preserving, idempotent initialization and legacy-policy upgrade;
- safe re-append when later user rules effectively hide governed paths;
- read-only effective-policy diagnostics using Git ignore and index state;
- integrity refusal for ignored governed paths and already tracked local-only paths;
- non-blocking warnings for untracked governed files, unavailable Git, and non-Git repositories;
- no automatic staging, commits, index cleanup, history mutation, or remote operation;
- clean-closure validation that cannot pass by hiding governed paths; and
- real-Git, CRLF, conflicting-rule, local-leak, clean-worktree, and filesystem-only tests suitable
  for Windows, macOS, and Linux.

No persisted FORGE schema changed. Git remains optional infrastructure and never replaces the
governed filesystem source-of-truth hierarchy.

This increment does not repair damaged journals, remove stale locks, reconstruct unrelated
idempotency receipts, recover unrelated transactions, generate agent context, invoke adapters, or
execute capabilities. Those remain separately bounded later work.
