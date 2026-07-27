# ADR-0046: Declarative Structural Evidence Validation

**Status:** Accepted

**Milestone:** M5 Increment 3

## Context

The research workflow declares structural checks, and Increment 2 supplies exact evidence-register
and citation-record templates. Owners can already record manual checks or separately configure,
approve, and execute local validator processes. Neither option provides a portable data-only
structural check shipped with the research pack.

Pack data trust must not become executable authority. A structural result must also remain
distinct from an evidence packet, the FORGE verification transition, owner acceptance, and factual
truth.

## Decision

Add the public versioned `StructuralValidatorDefinition` contract. A definition contains an ID,
semantic version, declared workflow check ID, purpose, one or more artifact-role text rules, and
explicit limitations. Rules may allow bounded text media types and require exact headings or
field prefixes with at least one non-whitespace value. The strict contract has no executable,
argument, environment, network, hook, expression, regular-expression, or code field.

M5 Increment 3 enables `PackManifest.data_resource_paths` only for safe-YAML files that validate as
structural-validator definitions. Explanation resources remain unavailable. Exact definition bytes
receive individual SHA-256 digests, participate in the complete pack digest, and use the Increment
2 active-copy, restart, recovery-preflight, and archive boundary. Template-only and resource-free
digest payloads remain unchanged.

`research-basic@0.3.0` supplies:

- `research-evidence-register-structure`, recording `evidence-register-structure`; and
- `research-citation-record-structure`, recording `citation-record-structure`.

The `collect` step requires both results against its exact current `source-register` and
`research-notes` revisions.

Add read-only `forge pack validator list|show` and mutating:

```text
forge check structure <step> <check> --validator <id>
```

Evaluation runs inside the trusted FORGE CLI. It starts no child process, resolves no citation,
uses no network, and requires no executable capability approval. The owner already authorized
interpretation of the exact declarative pack bytes when trusting the pack for initiative creation.
The stable FORGE CLI actor records the observation.

Missing required outputs or corrupt governed state fail closed. Well-formed current text that lacks
declared headings, fields, media type, UTF-8 encoding, or the 1 MiB structural-read bound records an
immutable failed `CheckResult` with bounded finding codes. Conformance records a passed result.
Both outcomes bind the exact validator-resource digest and every current step-output revision.

The command records only a `CheckResult` and `check-recorded` event. It creates no run, capability
approval, evidence packet, workflow verification transition, or acceptance.

## Consequences

The schema export grows from 50 to 51 models without changing an existing persisted model or
requiring migration. Old pack locks remain readable because their manifests declare no structural
resources and retain their original digest payload.

Data-only pack authors gain a bounded inspectable structural vocabulary, but not arbitrary
validation logic. More expressive schemas, executable local validators, or human review remain
separate tools with separate authority.

A passing structural result establishes only that exact current text matches declared surface
structure. It does not establish source authenticity, citation correctness, semantic quality,
methodological validity, evidence sufficiency, factual truth, verification, or owner acceptance.

Shared bundled-pack conformance, explanation profiles, long-gap resumption, bounded filesystem
discovery, template instantiation, citation resolution, and later M5 work remain separate
increments.
