# FORGE Constitution

## Purpose

FORGE is a local-first governance framework for human-directed, AI-assisted work. It
preserves intent, authority, evidence, and continuity inside an ordinary repository.
FORGE governs work; it does not perform the project work itself.

## Constitutional principles

1. **Human authority.** The repository owner alone records consequential owner decisions,
   including scope approval, capability approval, risk acceptance, outcome acceptance,
   abandonment, closure, and release progression.
2. **Claims are not completion.** Worker claims, checks, durable evidence, and owner
   acceptance are separate records and stages. No exit code, message, or generated file
   collapses them.
3. **Inspectable authority.** Governed state is available through ordinary, versioned files.
   Chat history, caches, indexes, and vendor-specific views are never authoritative.
4. **Local-first operation.** Core lifecycle operations require neither a network service nor
   a model-provider account.
5. **Replaceable workers.** Humans, agents, scripts, and tools are untrusted workers behind
   the same governance boundary.
6. **Domain-neutral core.** Software and research terminology belongs in declarative packs,
   not in core contracts or lifecycle services.
7. **Explicit state and recovery.** FORGE reports lifecycle and integrity separately. It
   detects inconsistent state and requires explicit recovery rather than silently repairing
   history.
8. **Immutable governance history.** Decisions, checks, evidence, approvals, overrides, and
   acceptance are amended, superseded, or revoked; they are never silently rewritten.
9. **Exact revisions.** Digests bind governance records to exact bytes, and closure-critical
   bytes are preserved independently of mutable working files.
10. **Separated trust.** Trusting declarative pack data never authorizes executable code.
11. **Progressive complexity.** A milestone introduces only the infrastructure required to
    satisfy its accepted scope.
12. **Education is presentation.** Explanation profiles may teach differently but cannot
    change permissions, gates, evidence, transitions, or acceptance.

## Security claims and limitations

FORGE provides supported-command authorization, tamper evidence, auditability, path controls,
and safe-default import behavior. It does not isolate a malicious process running with the
repository owner's operating-system permissions.

Secret screening is defense in depth. FORGE blocks configured secret locations and
recognizable credential patterns, but cannot guarantee discovery of every secret. The owner
remains responsible for reviewing imported and governed content.

## Milestone governance

Each milestone requires an approved brief, bounded implementation, automated checks, a manual
walkthrough, an implementation claim, an evidence packet, and explicit owner review. Work stops
after each milestone. Milestone 1 is internally divided into implementation increments, but
those increments do not create new owner gates unless scope materially changes.

Milestone 1 archival proves lifecycle behavior, exact-byte preservation, and command-level
archive immutability only. Production-strength hash-chain integrity, interruption safety,
recovery, concurrency, and corruption detection are Milestone 2 claims.

## Change control

Changes to the source-of-truth hierarchy, state machines, owner authority, trust model,
persistence, archive preservation, pack or adapter boundaries, compatibility commitments,
threat model, or public CLI semantics require an Architecture Decision Record (ADR). Material
scope changes require owner approval and must not be silently absorbed into implementation.

## Authority

The approved Production-v1 Master Implementation Specification supersedes earlier FORGE
roadmaps and handoffs wherever they conflict. Owner decisions accepted after that specification
take precedence and must be recorded with their provenance.

