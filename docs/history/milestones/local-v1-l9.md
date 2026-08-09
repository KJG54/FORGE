# Local Production-v1 L9 - Candidate Validation

## Authorized boundary

L9 validates the exact local candidate and prepares the owner campaign. It does not tag, publish,
commercialize, create public support obligations, or record final Local Production-v1 acceptance.

## Candidate corrections discovered during validation

The security review found that mnemonic milestone idempotency keys were safe governed identifiers
but matched the generic API-key rule. The exception now requires the exact Gitleaks rule, exact
governed paths, and a bounded UUID or milestone-key shape.

The live dogfood requirements revision then exposed a lifecycle defect: invalidation removed a
descendant run from active state, but run inspection did not recognize the invalidation event as a
terminal outcome. The corrected view keeps the compatible `cancelled` status, explicitly explains
that invalidation ended the run, and never invents a formal cancellation record.

Both findings changed candidate inputs. The superseded artifacts and their install evidence were
discarded, one final candidate was rebuilt, and every exact-wheel check was repeated.

The replacement build also corrected distribution hygiene. The superseded sdist had captured 519
entries from local `.claude/worktrees` state. Build exclusions and regression coverage now keep
`.agents`, `.claude`, `.codex`, and `.forge/local` out of distributions; the final sdist contains
617 entries and none from those paths.

The root README now gives a direct fit test, role comparison, concrete software and research
examples, and a prominent same-user isolation boundary. Because README content is packaged into
distribution metadata, that documentation correction received a new exact candidate identity and
the complete automated validation was repeated.

## Automated evidence

- candidate wheel: `f047d25365534beafba29cf01ed6f7e82a9a72a8a90de9f85ca8172b3f8b682a`;
- candidate sdist: `882ddeecee77750dc2aec931d2e52df2e414f6449bc7bd68866ad4782786f9bc`;
- 409 tests passed and 9 Windows privilege-dependent symbolic-link cases skipped;
- Ruff, strict Pyright, version consistency, and exact candidate verification passed;
- fresh `venv` and isolated `pipx` installation passed on Windows/CPython 3.14.4;
- both bundled examples closed successfully with healthy archives;
- backup, restore, migration, snapshot recovery, abandonment, archive access, and successor
  procedures passed;
- all five maintained Windows performance budgets passed; and
- license, vulnerability, complete-history secret, and candidate-snapshot security review passed.

The detailed point-in-time evidence is in
`release/local-production-v1/validation-report.md`. Friction is kept separate in
`release/local-production-v1/friction-report.md`.

## Remaining boundary

Native Codex and Claude Code owner observations remain pending and cannot be manufactured by
automation. Extended real-project use and final Local Production-v1 acceptance also remain pending.
The bounded next phase is `release/local-production-v1/extended-testing-plan.md`.

The governed requirements revision intentionally invalidated earlier scope support. Current scope
rework is verified and awaiting a renewed exact configured-owner acceptance. Subsequent implement,
verify-release, risk-review, and closeout records must remain separate and must stop at their owner
gates. Framework closeout, when reached, records candidate readiness only.
