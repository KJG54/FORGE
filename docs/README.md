# FORGE Documentation

FORGE is a local-first governance framework for human-directed, AI-assisted work. It records
authority, claims, checks, evidence, acceptance, continuity, and terminal history in an ordinary
repository. It does not perform the governed project work or isolate programs that run with the
repository owner's operating-system permissions.

This index routes each audience to a task-oriented starting point. The linked feature references
remain the canonical detail; the guides connect them without redefining contracts or authority.

## Start by audience

| Audience | Start here | Continue with |
|---|---|---|
| Repository owner or contributor | [User guide](user-guide/README.md) | [Examples](../examples/README.md), [troubleshooting](troubleshooting.md) |
| Pack author | [Pack-author guide](pack-author-guide.md) | [Workflows](workflows.md), [validators](validators.md) |
| Adapter contributor | [Adapter-author guide](adapter-author-guide.md) | [Adapters](adapters.md), [agent context](agent-context.md) |
| Architect or maintainer | [Architecture](architecture.md) | [Contracts](contracts.md), [persistence](persistence.md), [ADRs](adr/README.md) |
| Security reviewer or operator | [Security guide](security.md) | [Security policy](../SECURITY.md), [Git policy](git-policy.md) |
| Operator handling a failure | [Troubleshooting](troubleshooting.md) | [Recovery](recovery.md), [migrations](migrations.md) |

## Core journeys

- Install a built distribution using an
  [ordinary virtual environment or `pipx`](installation.md).
- [Initialize a repository](user-guide/initialization.md), create an initiative, and complete the
  [governed lifecycle](user-guide/README.md).
- Inspect the uninitialized [software and research examples](../examples/README.md).
- [Pause and resume](continuity.md) work without relying on chat history.
- Read [canonical transaction receipts](transaction-receipts.md), then use detailed history and
  record inspection when a concise mutation result needs forensic expansion.
- [Close, abandon, and inspect archives](closure-and-archives.md), or create a
  [successor initiative](successors.md).
- Diagnose integrity separately from lifecycle state, then select the exact
  [recovery procedure](recovery.md).

## Governance model

Read the [constitution](constitution.md) and [glossary](glossary.md) first when evaluating the
model. The most important boundary is:

```text
worker claim -> check -> evidence -> FORGE verification -> owner acceptance
```

These are distinct facts. A successful process or passing check never becomes evidence,
verification, owner acceptance, milestone acceptance, or release acceptance by implication.

The [contracts](contracts.md) define versioned public records. The [journal and materialized-state
reference](persistence.md) explains durable authority, transaction order, and replay. The
[compatibility policy](compatibility.md) states which pre-v1 schema and storage formats are
actually supported.

## Trust and execution

Declarative pack data, executable capability approval, worker output, and owner acceptance use
separate trust boundaries:

- [packs and workflows](workflows.md) are validated data and are locked by exact digest;
- [local validator capabilities](validators.md) require an exact owner approval before execution;
- [agent adapters](adapters.md) stage output through an untrusted result boundary; and
- [imports](handoffs-and-imports.md) require bounded staging and explicit application.

FORGE supplies governance controls, tamper evidence, and path protections. It does not supply a
hostile-code sandbox. See the [security guide](security.md) before enabling any local process.
Release reviewers should also run the
[dependency, license, vulnerability, and secret review](supply-chain-security-review.md).
The [performance budget guide](performance.md) defines the maintained release-candidate latency
workloads and interpretation.
The [self-dogfooding guide](dogfooding.md) explains how this repository's tracked framework-change
initiative governs the remaining M6 release work without manufacturing owner acceptance.
The [release-candidate closeout guide](release-candidate-closeout.md) defines the one-wheel matrix,
operational rehearsals, governed evidence sequence, and final M6 evidence requirements.

## Documentation authority and maintenance

The source-of-truth order is:

1. the accepted governing specification and later explicit owner decisions;
2. accepted Architecture Decision Records (ADRs);
3. versioned public contracts and validated persisted records;
4. feature references in this directory; and
5. audience guides and examples.

Guides summarize supported behavior and link to the lower-level source. They do not create CLI
commands, compatibility promises, authority, or recovery procedures. When behavior changes,
update the canonical feature reference, the applicable guide and index, and an ADR whenever the
change affects architecture, trust, persistence, compatibility, authority, or public semantics.
