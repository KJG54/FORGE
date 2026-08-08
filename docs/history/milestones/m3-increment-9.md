# M3 Increment 9 — Replaceable-Worker Acceptance and Closeout

## Authorized scope

- one end-to-end acceptance scenario proving that manual handoff, Codex CLI, and Claude Code use
  the same canonical context, staged-result import, artifact provenance, claim, and lifecycle
  boundaries;
- explicit proof that adapter output remains untrusted, is not applied automatically, and cannot
  exercise owner acceptance authority;
- a compatibility matrix covering discovery, authentication, invocation, fallback, capability
  approval, and result handling for every built-in adapter;
- an audit of every M3 exit criterion against executable tests and durable documentation; and
- the Milestone 3 evidence report and implementation stop point.

The acceptance fixture substitutes bounded local provider processes for Codex and Claude. It tests
FORGE's orchestration and governance boundary deterministically without requiring either vendor,
network access, or a live account in the test suite.

## Exit-criteria evidence

| M3 exit criterion | Evidence |
|---|---|
| Manual, Codex, and Claude use identical lifecycle and import rules | `tests/test_m3_acceptance.py` drives all three paths to the same artifact roles and `awaiting_verification` state |
| Missing or incompatible agents fall back to portable handoff | Adapter selection and provider diagnostic tests cover unavailable, incompatible, and unauthenticated installations |
| Vendor context is regenerable | Canonical-context and managed-reference tests prove deterministic regeneration and exact preservation outside managed spans |
| Capability approval is exact and bounded | Capability tests bind provider, version, invocation profile, permissions, scope, and duration before execution |
| Revoked capability cannot execute | Capability revocation and profile-drift tests fail closed before provider start |
| Agent results cannot approve gates or mutate lifecycle directly | Acceptance coverage proves staging precedes explicit import, claims remain separate, and an `agent_adapter` actor is refused owner acceptance |

## Explicit exclusions

Validator execution, executable pack providers, provider APIs, background execution, cross-process
live cancellation, automatic verification/evidence/acceptance, stronger hostile-code isolation,
and other M4 work are not implemented. Increment 9 closes and evaluates M3; it does not broaden the
worker's authority or add a new execution class.

## Contract impact

No persisted contract or public JSON Schema changes are required. The acceptance path composes the
existing canonical context, handoff, run, capability, `AgentResult`, artifact, claim, event, and
materialized-state contracts.

## Stop point

Milestone 3 implementation is complete and owner-accepted. The acceptance authorizes only the
separately bounded first Milestone 4 increment; it does not implicitly authorize validators,
executable pack providers, automatic verification, or later M4 work.
