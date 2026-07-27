# M4 Increment 11 — Adversarial Acceptance and Closeout

## Authorized scope

- one cumulative adversarial acceptance suite covering every M4 exit criterion;
- seeded false-completion refusal across claim, check, evidence, verification, and acceptance;
- trusted-data and exact executable-capability authority separation;
- literal argument-vector execution with shell syntax treated only as data;
- revoked acceptance and superseded-decision authority removal;
- malicious-pack, hostile-import, path-escape, and forged-claim refusal;
- executable documentation checks for the same-user-process threat boundary;
- complete canonical digest binding for newly recorded claims;
- backward-compatible restart validation for earlier claim-event history;
- isolated source-distribution and wheel builds;
- clean installed-wheel acceptance; and
- the Milestone 4 evidence report and implementation stop point.

## Exit-criteria evidence

| M4 exit criterion | Closeout evidence |
|---|---|
| Seeded false-completion scenarios cannot reach acceptance | A claim plus a failed check remains `awaiting_verification`; early acceptance and verification are refused |
| Trusted-data packs cannot execute code without separate capability approval | A trusted initiative cannot start its configured validator until the owner approves the exact profile; execution creates no evidence or acceptance |
| Revoked acceptance and superseded decisions stop authorizing progression | Revocation invalidates the accepted step and downstream readiness; withdrawing the current deviation review reopens its blocker |
| Malicious packs, hostile imports, command injection, path escape, and forged claims are blocked | Executable pack content, unexpected or traversing import paths, shell syntax, repository traversal, and altered claim records all fail closed |
| Same-user malicious processes require external isolation | Security, constitution, and validator documentation preserve the explicit operating-system boundary and external-isolation requirement |

The focused controls remain covered by their dedicated pack, import, path, agent-run, capability,
validator, acceptance, decision, deviation, override, risk, cancellation, audit, and record-
integrity tests. The closeout suite composes those boundaries without creating another execution
or governance-authority path.

## Claim-integrity hardening

The closeout test initially demonstrated that changing only a claim's free-form assertion was not
detected because the original event bound its actor, step, run, and exact artifact revisions but
not the complete record bytes. New claim events now include the canonical record digest before the
revision digests. Restart recomputes it and refuses mutation.

Earlier event history remains readable under the original binding. This compatibility does not
make a legacy claim authoritative by itself: current passing checks, evidence, verification, and
configured-owner acceptance remain independent requirements.

This strengthens the existing hash-chain and record-validation decision rather than choosing a
new architecture, so no additional ADR is required and no public JSON Schema changes.

## Explicit exclusions

M5 behavior, executable pack providers, provider APIs, background execution, cross-process live
cancellation, automatic crash resume, automatic evidence, verification or acceptance, semantic
truth evaluation, network audit export, hostile-code isolation guarantees, and production-release
support are not implemented.

## Validation

Final Windows validation recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- all 283 tests were exercised: 277 passed and 6 Windows symlink-privilege cases skipped;
- Hatchling produced the source distribution and wheel;
- a clean environment installed the wheel and loaded version `0.1.0a0`;
- the installed-wheel CLI initialized a repository, created an initiative, refused premature
  acceptance with stable conflict exit 31, exposed its sanitized local audit event, and passed
  doctor; and
- the installed wheel exported all 50 public schemas.

## Stop point

Milestone 4 implementation and closeout evidence are complete. The repository owner formally
accepted M4 and authorized publication in the Codex task on 2026-07-27. M5 work must begin from a
separately defined incremental boundary.
