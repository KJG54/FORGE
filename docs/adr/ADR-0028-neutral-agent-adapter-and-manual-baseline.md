# ADR-0028: Neutral Agent Adapter and Manual Baseline

**Status:** Accepted

**Milestone:** M3 Increment 3

## Context

FORGE needs a common integration boundary before it can support separately installed Codex,
Claude, or other tools. The boundary must not make a vendor authoritative, grant an adapter direct
access to governed mutation services, or become an empty abstraction with no working
implementation. Missing or unusable tools must degrade to the existing manual file workflow.

The canonical agent context and portable handoff already provide provider-neutral assignment and
return contracts. They remain the correct baseline for exercising the interface without starting an
external process or changing durable run semantics.

## Decision

Define a transient, provider-neutral `AgentAdapter` protocol covering availability detection,
version reporting, compatibility assessment, invocation preparation, process start, cancellation,
output capture, result-manifest production, and diagnostics. The protocol exchanges frozen data
objects containing scalar values and repository-independent paths; it does not receive
`RepositoryLayout`, journal writers, lifecycle services, or any other core mutation service.

Ship `ManualAgentAdapter` in the same increment. It is always available, reports the installed
FORGE version, requires no authentication, prepares a digest-bound `manual-handoff` plan, and
explicitly reports process start, cancellation, and output capture as unsupported. Result-manifest
production reports `manual-required` because a person or worker must return an `AgentResult` for
the existing staged-import path.

Keep selection in core orchestration with a static registry. An explicit adapter ID takes
precedence over `agents.preferred_adapter`; otherwise the configured preference applies. An
unregistered, unavailable, or incompatible selection falls back to `manual` with a visible reason.
`forge agent doctor` exposes this read-only decision. Existing `forge handoff` explicitly requests
the manual adapter, binds its plan to the exact canonical-context SHA-256 digest, and then lets core
create the disposable handoff bundle.

The interface data is not persisted and receives no public JSON schema in this increment. Existing
`AgentHandoff`, `AgentResult`, journal, snapshot, run, configuration, and archive formats remain
unchanged.

## Consequences

The adapter abstraction has a tested implementation and the manual fallback travels through the
same preparation boundary future installed tools must honor. Provider code remains isolated from
governance mutation, and a missing preferred tool cannot prevent a portable handoff.

The static registry intentionally recognizes only `manual`. Therefore a `codex` or `claude`
preference currently produces an explicit fallback rather than tool discovery. No process is
started, supervised, cancelled, or captured; no authentication state is inspected; no adapter run
or result manifest is created automatically; and no capability is approved or executed. Those are
separate later increments with additional security and compatibility decisions.
