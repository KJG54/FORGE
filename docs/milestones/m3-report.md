# Milestone 3 Evidence Report

**Milestone:** M3 — Replaceable Worker Integration

**Implementation state:** complete and owner-accepted

**Owner acceptance:** accepted in the Codex task by the repository owner on 2026-07-23

**Authorized boundary:** M3 only; M4 had not begun when this gate was accepted

## Outcome

M3 makes workers replaceable without making them authoritative. Manual handoff, Codex CLI, and
Claude Code receive the same bounded provider-neutral assignment, return the same `AgentResult`
contract, enter the same untrusted staging and explicit import path, and use the same claim,
verification, and acceptance lifecycle. Provider integration changes how bounded work is attempted,
not how project truth is established.

Provider availability is optional. Diagnostics fail closed on missing stable features or persisted
authentication and select the process-free manual handoff with a visible reason. Executable
providers additionally require an owner approval bound to the exact detected executable profile;
trusted pack data never supplies that authority.

## Increment inventory

| Increment | Delivered boundary |
|---|---|
| 1 | Deterministic, allowlisted, provider-neutral canonical agent context |
| 2 | Digest-bound managed references in `AGENTS.md` and `CLAUDE.md` |
| 3 | Neutral `AgentAdapter` lifecycle and always-available manual baseline |
| 4 | Bounded Codex CLI discovery, compatibility, authentication, and preparation |
| 5 | Symmetric Claude Code discovery, compatibility, authentication, and preparation |
| 6 | Explicit synchronous governed adapter execution and untrusted result staging |
| 7 | Exact owner-controlled executable capability approval and revocation |
| 8 | Owner-controlled trust lifecycle for the active locked data-only pack |
| 9 | Cross-adapter acceptance, compatibility matrix, exit audit, and milestone evidence |

## Architecture and authority evidence

| Boundary | M3 implementation | Evidence |
|---|---|---|
| Context | Deterministic JSON/Markdown derived from governed state and selected inputs only | context leakage, digest, regeneration, and blocker tests |
| Vendor references | Optional managed spans bound to the exact context digest | byte-preservation, stale-plan, and no-change tests |
| Selection | Registered adapters with explicit diagnostics and manual fallback | manual, Codex, and Claude adapter tests |
| Execution | Disposable per-run workspace, bounded environment, timeout, and output capture | governed execution and cancellation tests |
| Return | Source-bound `AgentResult` copied into existing untrusted import staging | execution, import-security, and acceptance tests |
| Authority | Worker claim, checks, evidence, verification, and owner acceptance remain separate facts | run-attribution, acceptance-refusal, and lifecycle tests |
| Executable trust | Exact profile approval, scoped duration, consumption, drift refusal, and revocation | capability registry tests |
| Pack trust | Append-only owner trust decisions for locked data, separate from process authority | pack-trust lifecycle and archive tests |

The detailed built-in adapter comparison is recorded in the
[compatibility matrix](../adapters.md#built-in-compatibility-matrix).

## Exit-criteria assessment

- Manual, Codex, and Claude converge on identical artifact roles, untrusted provenance, and
  lifecycle state in the executable M3 acceptance scenario.
- Missing, incompatible, and unauthenticated provider installations visibly fall back to manual
  handoff during selection. Explicit execution never silently substitutes another provider.
- Canonical context and managed vendor references are deterministic and regenerable from governed
  repository state.
- Executable approval binds the exact capability, provider/version, resolved executable,
  invocation profile, environment, permissions, side effects, duration, owner, and rationale.
- Revocation, one-time consumption, or invocation-profile drift prevents a future process start.
- Adapter output cannot apply files, record checks or evidence, verify work, accept gates, or
  mutate lifecycle directly. The core owns all durable transitions.

## Validation results

The final Increment 9 validation records:

- Ruff passed with no findings.
- Strict Pyright passed with 0 errors and 0 warnings.
- Pytest passed with 221 tests and 6 expected Windows symlink-privilege skips.
- Isolated source-distribution and wheel builds passed.
- A clean target installed-wheel smoke loaded the packaged CLI, reported `0.1.0a0`, initialized a
  repository, and exercised the packaged adapter diagnostic surface.
- Remote Windows, macOS, and Linux results for this exact closeout change are not claimed until the
  owner authorizes publication and the corresponding CI run completes.

## Known limitations and deferred work

- Provider APIs and background execution are not implemented.
- Provider processes run with bounded profiles and disposable workspaces, but same-user execution
  is not a hostile-code security boundary.
- Cancellation is synchronous within the executing process; cross-process live cancellation and
  automatic crash resume remain deferred.
- Pack trust is data trust only. Executable pack providers and trusted local validator execution
  belong to M4 and require a distinct authority model.
- Worker output remains untrusted until explicit import and still requires independent checks,
  evidence, verification, and owner acceptance.
- Git staging, commits, pushes, synchronization, and conflict resolution remain owner-controlled.
- Naming and distribution metadata remain pre-alpha and provisional.

## Owner decision and stop condition

The repository owner explicitly accepted the M3 gate in the Codex task on 2026-07-23 and
authorized publication followed by the first bounded M4 increment.

**Stop satisfied:** M3 is complete and accepted. M4 work must follow its own approved incremental
boundary; this report does not authorize later M4 increments.
