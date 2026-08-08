# ADR-0031: Governed Isolated Adapter Execution

**Status:** Accepted

**Milestone:** M3 Increment 6

## Context

ADRs 0029 and 0030 stopped Codex and Claude at deterministic invocation preparation because FORGE
did not yet have an isolated output workspace, a durable provider run, bounded supervision, or a
safe path from provider files into the existing import boundary. The Production-v1 specification
places local adapter execution and captured `AgentResult` routing in M3, while capability execution,
executable pack trust, stronger operating-system isolation, and complete asynchronous cancellation
belong to later work.

Both CLIs run with the same operating-system identity as FORGE. A disposable directory and vendor
permission flags reduce accidental reach but are not a hostile-code security boundary. Provider
content must therefore remain untrusted, and FORGE must never give an adapter repository mutation
services or interpret a successful process exit as a claim, check, evidence packet, or acceptance.

## Decision

Add synchronous `forge agent run <step> --adapter codex|claude`. Selection remains explicit and
fail-closed: an unavailable, incompatible, or unauthenticated provider still resolves visibly to
manual, and `agent run` refuses that fallback in favor of the existing `forge handoff` command.

Before execution, FORGE creates a normal immutable `RunRecord` attributed to a deterministic
`agent_adapter` actor and moves the eligible step to `in_progress`. It then creates
`.forge/local/runs/<run-id>/` containing:

- `workspace/context.json`, the exact canonical assignment used for the run;
- `workspace/agent-result.schema.json` and `workspace/run.json`;
- `workspace/inputs/`, containing copies only of digest-verified required inputs;
- `workspace/result/`, the only declared provider return bundle; and
- bounded raw `stdout.jsonl` and `stderr.log` captures outside the writable workspace.

The adapter receives only frozen request and plan values. It launches one argument-vector process
with an allowlisted environment, never a caller-controlled shell string. Execution is bounded to
3,600 seconds and 10 MiB of combined captured output. Timeout or capture overflow terminates the
process, waits briefly, and kills it if necessary. Expected preparation, start, capture, or result
validation failures are recorded as `adapter-run-executed` and followed by the existing governed
`run-cancelled` transition so the step is not silently stranded.

Codex runs in ephemeral JSONL `workspace-write` mode with approval prompts, user configuration,
repository rules, session persistence, network access, and the Git-repository prerequisite
disabled. Claude runs in non-interactive streaming mode with `acceptEdits`, only
`Read,Glob,Grep,Write`, bare startup, no session persistence, strict empty MCP configuration, and
no browser integration. These profiles allow files only for the disposable return workflow; they
do not authorize project mutation.

On exit, FORGE accepts only a regular `workspace/result/result.json`. The existing staged-import
service validates the exact bundle inventory, paths, symlinks, sizes, digests, and secrets, and now
also requires `source_run_or_handoff_id` to equal the governed run ID. Valid bytes are copied into
`.forge/local/import-staging/`; no project target is changed. The owner must still preview and apply
`forge import-result` explicitly.

A successful provider process remains an active workflow run until returned files are imported and
a claim is submitted. `forge complete --run-id <id>` attributes that claim to the immutable run
worker rather than impersonating the adapter as the repository owner. The assertion must exactly
match a `worker_claims` entry in an imported result from that run, preventing the caller from
inventing an adapter statement. Checks, evidence, and owner acceptance remain independent later
transitions.

The bundled `software-basic` data pack advances to version `0.3.0` and permits `agent_adapter` on
its steps. Existing initiative workflow locks remain immutable and retain their earlier actor
policy. No public Pydantic contract or exported JSON Schema changes; the adapter request/plan
extensions remain transient service values.

## Consequences

Compatible local Codex and Claude installations can now perform bounded work without receiving a
project mutation API, and every attempt has a durable worker identity and journal trace. Provider
files cross the same conservative staging boundary as manual handoffs, so execution does not
collapse trust layers.

The command holds FORGE's repository mutation lock while the synchronous provider runs. An
unexpected host crash may therefore leave the command receipt incomplete and the governed run in
progress; FORGE reports that condition and does not silently resume the provider. Cross-process
live cancellation, background run services, stronger OS/container isolation, provider API
integration, capability registries and approvals, validators, executable pack trust, automatic
checking/evidence/acceptance, and automatic Git operations remain out of scope.
