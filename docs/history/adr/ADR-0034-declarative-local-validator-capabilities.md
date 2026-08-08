# ADR-0034: Declarative Local Validator Capabilities

**Status:** Accepted

**Milestone:** M4 Increment 1

## Context

M3 introduced exact owner approval for built-in agent executable profiles. M4 must add trusted
local validators without allowing trusted-data packs to execute code, accepting shell command
strings, or treating a passing process as evidence or acceptance.

A validator also needs a portable declaration separate from its machine-specific inspection. The
owner must be able to review the resolved executable, ordered arguments, working directory,
timeout, expected outputs, environment access, and side-effect risk before granting authority.

## Decision

Add strict `LocalValidatorDefinition` records under
`forge.yaml.capabilities.local_validators`. Each declaration contains:

- a `validator.`-namespaced ID and semantic version;
- owner-declared provider identity and version;
- purpose;
- one executable plus an ordered argument vector;
- repository root or one normalized repository-relative working directory;
- a timeout from 1 through 3,600 seconds;
- one or more symbolic expected outputs;
- environment-variable names, never values; and
- the existing `SideEffectClass` risk classification.

There is no shell-command field. Invocation parts must be single-line and NUL-free. Inspection
resolves a bare executable through `PATH`, a repository-relative executable through the governed
path boundary, or an absolute local executable directly. It records the canonical resolved file
and rejects missing, irregular, escaping, and Windows batch-command-shim profiles. Inspection does
not start the executable or probe its version; `provider_version` is explicitly owner-declared.

Local validator declarations enter the existing capability registry as disabled
`CapabilityDefinition` profiles. The configured owner may preview and approve them through the
existing immutable capability approval/revocation lifecycle. Approval binds the resolved
executable, ordered arguments, working-directory rule, environment access, side-effect class, and
the complete definition digest. Unlike the compatibility allowance for agent project approvals,
every validator scope—including `approved-for-project`—requires the exact definition version and
digest, so timeout or expected-output drift invalidates prior authority.

Pack manifests may name capability IDs as data, but they cannot register a local validator,
supply its executable declaration, or approve it. Only tracked project configuration creates a
validator registry entry, and only an explicit owner approval grants authority.

Increment 1 does not execute validators, create runs, record checks, produce evidence, or advance
workflow state.

## Consequences

FORGE now has a domain-neutral, inspectable validator declaration and authorization boundary
without expanding worker authority. Project configuration may be cross-platform only when its
executable declaration is portable across those systems; otherwise each platform needs an
owner-reviewed profile change and fresh approval.

Later M4 increments may add supervised validator execution and immutable `CheckResult` capture,
but must use the declared argument vector with shell execution disabled and must preserve the
claim/check/evidence/acceptance separation.
