# M3 Increment 6 — Governed Isolated Adapter Execution

## Authorized scope

- explicit synchronous execution of compatible Codex and Claude local-CLI adapters;
- durable adapter-attributed workflow runs and an immutable execution audit event;
- disposable per-run workspaces with copied allowlisted inputs and a dedicated result directory;
- allowlisted process environments, argument-vector launch, bounded time and output capture,
  termination, and kill fallback;
- provider-authored `AgentResult` validation bound to the exact source run;
- immediate copy into the existing local import staging area without project application;
- explicit run-attributed claim completion after the owner imports returned files; and
- a new `software-basic` 0.3.0 data-pack version that permits adapter workers.

## Explicit exclusions

Provider APIs, background services, cross-process live cancellation, crash-time automatic resume,
hostile-code isolation claims, capability execution or approval, executable pack trust, provider
model selection or cost policy, automatic import application, automatic checks, evidence or owner
acceptance, automatic Git operations, and M4 work are not implemented. Manual handoff remains the
portable fallback. Public schema count and persisted record shapes remain unchanged.

## Design evidence

[ADR-0031](../adr/ADR-0031-governed-isolated-adapter-execution.md) records the execution, isolation,
provider compatibility, supervision, result-binding, actor attribution, workflow-pack version, and
remaining-risk decisions. [Agent Adapters](../adapters.md) documents the operator workflow.

## Test evidence

Deterministic fake-provider tests cover successful process start and capture, credential-variable
exclusion, isolated context and return paths, source-run binding, staged-but-unapplied output,
run-attributed completion, timeout termination, failure audit, and release of failed steps. Codex
and Claude preparation tests cover their exact writable-isolation argument profiles and advertised
process capabilities. Existing handoff/import tests continue to exercise inventory, path, symlink,
size, collision, secret, provenance, and explicit-apply safeguards.

Final Windows validation recorded:

- 208 tests passed with 6 expected Windows symlink-privilege skips;
- Ruff and strict Pyright passed with no findings;
- Hatchling produced both the source distribution and wheel;
- a fresh environment installed the wheel and passed version, `agent run --help`, initialization,
  configuration, bundled `software-basic` 0.3.0 validation, initiative creation, manual adapter
  diagnostics, manual handoff, and unchanged 45-schema export smoke checks;
- the installed Claude Code 2.1.207 CLI was detected as compatible, authenticated, and execution
  capable; and
- the local Codex diagnostic failed its bounded version probe and visibly fell back to manual.

Provider execution behavior itself uses deterministic fake CLIs in the cross-platform test suite;
installed-provider diagnostics are supplemental and do not spend model tokens or mutate a project.

## Stop point

Stop after synchronous local adapter execution and untrusted result staging are implemented and
validated. Do not implement governed capabilities, executable pack trust, background execution,
automatic verification, or Milestone 4 behavior.
