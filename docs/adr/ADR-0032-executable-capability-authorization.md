# ADR-0032: Executable Capability Authorization

**Status:** Accepted

**Milestone:** M3 Increment 7

## Context

Increment 6 can start compatible Codex and Claude processes, but it intentionally has no durable
capability registry or owner approval gate. Adapter availability, pack-data trust, and executable
authority are different facts. A provider discovered on `PATH` must not become executable merely
because it is installed, selected, or declared by a trusted-data pack.

The approval preview must also describe the process that will actually start. Binding only a
symbolic capability ID would permit provider upgrades, executable replacement, changed flags, or
expanded environment access to inherit authority that the owner never reviewed.

## Decision

Register `agent.codex.execute@1.0.0` and `agent.claude.execute@1.0.0` as built-in executable
capabilities. Each inspection combines a stable FORGE definition with current adapter diagnostics
and displays the provider and detected version, resolved executable, fixed argument construction,
working-directory rule, allowlisted environment keys, repository-write side-effect class, local
output locations, and approval duration choices.

Capabilities remain `disabled` by default. `forge capability approve <id>` is preview-only unless
the configured owner confirms it with `--apply`. A persisted `CapabilityApproval` binds the exact
definition digest and inspected invocation profile. The three scopes mean:

- `approved-once`: one governed run attempt;
- `approved-for-version`: the exact capability version and invocation profile; and
- `approved-for-project`: the current project initiative while provider, executable, arguments,
  working-directory rules, environment access, and side-effect class remain unchanged.

Project approval may survive a future capability-definition version change only when that complete
execution profile is unchanged. It is archived with the current initiative so successor initiatives
begin with fresh governance. Any executable, provider-version, argument, environment, working
directory, or side-effect drift makes an existing approval inapplicable and execution fails closed.

Approvals and revocations are immutable initiative-scoped governance records backed by
`capability-approved` and `capability-revoked` journal events. Revocation never deletes approval
history and blocks all future use. A one-time approval is consumed when its ID is bound into an
immutable `RunRecord`, before process start; a failed or interrupted launch therefore cannot reuse
it. Every executable adapter run binds exactly one capability ID and approval ID, and cross-record
validation rejects missing, revoked, duplicated one-time, or mismatched authorization.

Pack trust remains independent. `trusted-data` authorizes only validated declarative pack content
and never satisfies the executable capability gate.

`RunRecord.capability_approval_ids` is an additive field with an empty default. Immutable
Increment 6 run history without capability bindings therefore remains readable and valid, but it
does not create an approval and cannot authorize any new invocation. All Increment 7 service paths
write the capability and approval binding before starting a provider.

## Consequences

Installed providers are no longer sufficient authority for execution. Owners can inspect and
approve exact process profiles, list durable history, revoke future execution, and audit which
approval authorized a run. Approval operations use normal mutation locking and idempotency; list,
inspect, and approval preview are read-only.

The registry is intentionally built in for this increment. Pack trust/untrust commands, executable
pack providers, validator execution, background services, provider APIs, stronger operating-system
isolation, and complete asynchronous cancellation remain later boundaries.
