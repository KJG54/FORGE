# ADR-0033: Owner-Controlled Pack Data-Trust Lifecycle

**Status:** Accepted

**Milestone:** M3 Increment 8

## Context

Initiative creation already records the configured owner's explicit `trusted-data` decision for
one exact validated pack and locks its manifest and workflow. That creation record is immutable,
but the owner needs to withdraw trust if later review identifies a concern and restore trust after
revalidating the same locked bytes. Rewriting the original decision would destroy provenance, while
conflating data trust with executable capability approval would violate FORGE's separated-trust
principle.

The untrusted state must fail closed for operations whose meaning or authority comes from the
locked workflow. It must not make the repository impossible to inspect, prevent the owner from
restoring trust, strand an active governed run, or prevent explicit non-success abandonment.

## Decision

Keep `.forge/active/pack-trust.json` as the immutable creation-time decision. Store every later
decision as `.forge/active/pack-trust-decisions/<decision-id>.json` and bind it to a
`pack-trust-changed` event. Each record identifies the exact locked pack ID and version, includes
the locked manifest digest, references the immediately preceding decision, records the configured
owner and rationale, and must alternate between `trusted-data` and `untrusted`.

Derive effective trust by replaying the initial decision and the append-only event-ordered chain.
Validate record inventory, ownership, sequence, predecessor, pack identity, state transition, and
digests on every active or archived load. A missing, additional, reordered, same-state, or modified
decision is an integrity error.

`forge pack inspect` reports the exact locked identity, digest, declared executable capabilities,
effective trust, and full history. `forge pack trust` and `forge pack untrust` are preview-only
unless `--apply` is supplied; applied operations use the normal repository mutation lock and
idempotency receipt.

When effective trust is `untrusted`, ordinary workflow-dependent services fail before mutation.
Status and history inspection, pack inspection and retrust, independent capability governance,
run inspection and cancellation, registered schema recovery, and owner abandonment remain
available. Successful closure remains blocked. Active runs are not cancelled implicitly because
automatic cross-process cancellation remains outside this increment.

Pack data trust never approves or executes a declared capability. Executable capability authority
continues to require the separate exact-profile approval introduced by Increment 7.

## Consequences

Owners can stop using questioned declarative workflow data without deleting or weakening audit
history and can recover after revalidation without creating a successor initiative. Archives
retain the complete decision chain and remain readable when their final effective state is
untrusted.

The implementation adds one governed record directory and one state-neutral journal event but no
new public schema. Executable pack providers, validator execution, automatic run cancellation,
background services, provider APIs, and Milestone 4 behavior remain later boundaries.
