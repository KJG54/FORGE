# FORGE Current Governing Specification

**Status:** Current maintained reference  
**Applies to:** FORGE framework design and supported repository behavior  
**Primary audience:** One repository owner working with direct workspace agents  
**Project posture:** Public source, unreleased development project

This document is the shortest current entry point to FORGE's governing model. It synthesizes and
routes to authority; it does not replace the Constitution, accepted ADRs, exact contracts, or
validated governed records.

## Purpose

FORGE is the Framework for Orchestrated Reasoning, Governance, and Execution. It is a local-first
governance framework for human-directed, AI-assisted work in an ordinary repository. FORGE keeps
intent, authority, exact artifacts, checks, evidence, acceptance, and terminal history inspectable
without turning an agent or tool into the owner.

The durable invariant is:

```text
worker claim -> check -> evidence -> FORGE verification -> owner acceptance
```

These are five distinct facts. No process exit, generated file, passing check, Git commit, hosted
status, model output, or FORGE receipt silently implies the next fact.

## Constitutional boundaries

The [Constitution](constitution.md) supplies the durable principles and change-control boundary:

- the owner alone records consequential owner decisions;
- workers are replaceable and untrusted;
- core lifecycle behavior is domain-neutral and local-first;
- history and exact revisions are preserved instead of silently rewritten;
- declarative-data trust is separate from executable authority;
- education changes presentation, not governance; and
- supported recovery is explicit and fail-closed.

FORGE supplies governance controls, tamper evidence, auditability, path controls, and conservative
imports. It does not isolate a malicious same-user process or authenticate who typed a command.

## Typed authority

"Source of truth" is not one global ranking. FORGE uses five types:

### Normative design

Normative design answers what FORGE is intended and permitted to do. Within this type:

1. the Constitution states durable principles and required change control;
2. an applicable recorded owner decision may settle its exact declared question only when the
   required change control is satisfied;
3. effective accepted ADRs state architectural decisions, with explicit newer supersession
   controlling only its declared scope;
4. machine-readable contracts control the exact fields and values they define;
5. this governing specification summarizes those sources; and
6. feature references and guides explain them without creating authority.

An initiative-scoped owner decision does not silently amend global architecture. A global change
must declare global applicability and satisfy the Constitution's ADR requirement.

### Persisted runtime/history

Persisted runtime/history answers what bytes and governed events exist. ADR-0004's order remains:

1. current artifact bytes;
2. preserved historical bytes in the content-addressed object store;
3. binding digests in governance records;
4. the validated hash-chained journal;
5. locked rules; and
6. reconstructable materialized state.

Disagreement is an integrity condition, never permission for a document, cache, or agent to repair
history silently.

### Active locked rules

Active locked rules answer what a specific initiative may do now. Exact pack and workflow locks,
current records, and derived lifecycle conditions govern supported transitions. A later global
design change does not mutate an existing lock. Use the supported scope-amendment, migration,
terminal, or successor route when rules must change.

### Reference content

Reference content includes maintained feature documentation and audience guides. It explains
supported behavior and should link to lower-level authority. It cannot create a command,
compatibility promise, acceptance, permission, or recovery path.

### Derived advisory views

Derived advisory views include generated agent context, `forge status`, indexes, caches, manual
handoffs, local scratchpads, external dashboards, and chat. They help orientation and may reveal a
problem, but they are disposable and cannot overrule validated records or grant authority.

## Conflict handling

When statements appear to disagree:

1. classify each statement by authority type;
2. validate the exact bytes, record identity, digest, scope, and effective status;
3. apply precedence only within the same type;
4. treat a cross-type disagreement as drift, integrity failure, or an applicability question;
5. use the supported ADR, decision, scope-amendment, migration, recovery, or successor mechanism;
   and
6. never normalize the conflict silently.

Chat history and agent memory may help locate evidence but are never the deciding source.

## Specification and decision lifecycle

- This file is the current maintained synthesis and front door.
- The [ADR catalog](history/adr/README.md) separates the status recorded in immutable ADR text from
  its current effective status and supersession relationships.
- Exact machine-readable contracts — including the [version contract](../release/version-contract.json),
  [performance budgets](../release/performance-budgets.json),
  [installation matrix](../release/installation-matrix.json), and
  [security-review policy](../release/security-review-policy.json) — control their declared fields;
  they are not universal design documents.
- Historical plans and specifications remain preserved under [docs/history/](history/README.md)
  with an adjacent status boundary.
- The recovered [Production-v1 Master Implementation Specification](history/specifications/README.md)
  is historical evidence, not current instruction.

Changing the authority hierarchy, owner authority, trust model, persistence, state machines,
archive preservation, pack or adapter boundaries, compatibility commitments, threat model, or
public CLI semantics requires an ADR and explicit owner review under the Constitution.

## Publication and compatibility posture

The repository is publicly accessible source for an unreleased development project. A public
repository, installable source tree, successful initiative, accepted artifact, or terminal archive
does not by itself create a supported release, tag, package publication, or public compatibility
promise. Exact current version and candidate fields remain controlled by their machine-readable
contracts and later owner decisions.

## Reading route

- Start with this file for the whole model.
- Read the [Constitution](constitution.md) for durable principles.
- Read [Architecture](architecture.md) for layers, state, and trust boundaries.
- Read the [ADR catalog](history/adr/README.md) for effective architectural decisions.
- Read [Persistence](persistence.md) for journal and state authority.
- Read [Workflows](workflows.md) for locked initiative rules.
- Read the relevant feature reference for operational detail.
