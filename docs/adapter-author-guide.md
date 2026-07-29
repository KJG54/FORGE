# Adapter-Author Guide

An agent adapter translates canonical FORGE context into one worker-specific invocation and
returns output through the normal untrusted result boundary. It does not become a repository
owner, change workflow state directly, accept output, or convert provider success into a claim,
check, evidence, verification, or acceptance.

FORGE currently ships built-in manual, Codex CLI, and Claude Code adapters. There is no dynamic
third-party adapter discovery or stable external plugin ABI. This guide is therefore for
contributors adding or maintaining an adapter in the FORGE source tree. The Python adapter surface
remains pre-v1 and is not part of the documented persisted compatibility promise.

## Neutral protocol

Implement `forge.adapters.base.AgentAdapter`. The protocol separates:

1. availability detection;
2. version reporting and compatibility assessment;
3. a complete, inspectable invocation plan;
4. process start;
5. cancellation;
6. bounded output capture;
7. result-manifest production; and
8. diagnostics.

The data classes in `forge.adapters.base` are the shared boundary. Keep provider SDK objects,
credentials, prompts, and raw output outside them.

`prepare_invocation` must be deterministic for the same validated request. It binds the step,
canonical context digest, required outputs, constraints, working/output directories, timeout,
result contract, executable, and separate argument vector. Never construct a shell command string.

## Compatibility and fallback

An installed-tool adapter should:

- use bounded executable discovery;
- report the detected executable and version without running project work;
- classify compatibility as compatible, incompatible, or unknown;
- inspect only stable feature and persisted authentication indicators;
- expose limitations in diagnostics; and
- fail to the always-available manual handoff when unavailable, incompatible, unauthenticated, or
  unregistered.

Unknown is not compatible. A user preference does not override failed discovery. Diagnostics must
not display credential values.

## Execution boundary

Local adapter execution is FORGE-governed but not a hostile-code sandbox:

- the owner must hold an active exact capability approval;
- the adapter receives canonical context through the approved input channel;
- execution uses an explicit executable and argument vector with `shell=False`;
- work occurs in a fresh disposable workspace with a dedicated output directory;
- stdout and stderr are bounded local-only captures;
- one durable run and one terminal execution event preserve the outcome; and
- returned files are staged and screened through the ordinary import pipeline.

Do not grant the provider direct mutation authority over `.forge/` or treat its process exit as
step completion. Cancellation records a governance outcome; it cannot prove an external
cross-process worker stopped unless the managed execution boundary established that fact.

## Adding an in-tree adapter

1. Implement the neutral protocol under `src/forge/adapters/`.
2. Reuse the shared local-CLI supervision helper when the worker is a separately installed command.
3. Export the implementation from `forge.adapters`.
4. Register its stable ID in the in-tree registry in `forge.core.agent_adapters`.
5. Add exact discovery, version, authentication, invocation, output, cancellation, and fallback
   tests.
6. Add platform-specific tests for executable resolution and argument construction.
7. Update [the adapter reference](adapters.md), security documentation, and an ADR if the provider
   changes execution, trust, capability, persistence, or public semantics.

Registration is source-controlled. A pack cannot register an adapter or supply executable
arguments.

## Required test cases

- executable absent, irregular, or unsupported;
- version output missing, malformed, unsupported, or outside the stable-feature range;
- unauthenticated or indeterminate authentication;
- exact prepared standard input and separate argument vector;
- spaces and non-ASCII characters in paths;
- process launch failure, nonzero exit, timeout, cancellation, and output overflow;
- no credential inheritance beyond the approved channel;
- bounded local captures that are never rendered by normal output;
- missing, malformed, symbolic, escaping, secret-like, and colliding returned files;
- manual fallback with a clear reason; and
- restart validation of every durable run and execution-event binding.

Run focused adapter tests on Windows, macOS, and Linux before claiming compatibility. Passing tests
for one machine or executable version establish only that observed cell.

## Review checklist

- Provider-specific behavior stays behind the neutral protocol.
- No adapter method gains owner authority or writes lifecycle state outside core services.
- No shell string, implicit hook, pack-provided executable, or unbounded environment is used.
- Context and result contracts remain provider-neutral and digest-bound.
- Authentication discovery is read-only and never exposes credentials.
- Output is untrusted until the standard staged import completes.
- Process success remains distinct from claim, check, evidence, verification, and acceptance.
- Unsupported conditions select manual fallback or fail closed with an actionable diagnostic.

See [agent adapters](adapters.md), [canonical context](agent-context.md), and
[handoffs and imports](handoffs-and-imports.md) for the complete current behavior.
