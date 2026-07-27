# M5 Increment 3 — Declarative Structural Evidence Validation

## Authorized scope

- one strict public `StructuralValidatorDefinition` contract and schema;
- safe-YAML structural definitions as the only supported general pack data resource;
- individual and canonical pack-digest binding plus exact active/archive copies;
- one evidence-register and one citation-record definition in `research-basic@0.3.0`;
- generic bounded in-process UTF-8 heading and non-empty field-prefix evaluation;
- exact current step-output revision and validator-resource digest binding;
- immutable passed or failed `CheckResult` capture by the FORGE CLI actor;
- read-only available-or-locked `forge pack validator list|show`; and
- explicit `forge check structure`.

## Explicit exclusions

Child processes, shell execution, executable capability approval, regular expressions, expressions,
hooks, network access, citation resolution, source retrieval, semantic scoring, factual truth
evaluation, automatic evidence registration, workflow verification, owner acceptance, template
instantiation, shared pack conformance, explanation profiles, resumption changes, filesystem
discovery, and later M5 work are not implemented.

## Authority and trust

The configured owner authorizes interpretation of the complete exact declarative pack digest as
data during initiative creation. A structural definition cannot declare executable behavior or
gain capability authority. The stable FORGE CLI actor records deterministic observations.

A structural result is one check fact. It is not evidence, verification, acceptance, or truth.
Normal progression still requires an evidence packet binding all current passing checks and claims,
the explicit `forge verify` transition, and configured-owner acceptance.

## Persistence, compatibility, and failure semantics

Structural definitions reuse `.forge/active/pack-resources/`, pack digests, restart validation,
recovery preflight, and terminal archive inventories. They add no event type or initiative-scoped
record type. `CheckResult` and `check-recorded` retain the observation.

Malformed or executable-looking definitions fail pack loading. Missing, extra, changed, binary,
symbolic, irregular, oversized, or digest-inconsistent locked resources fail initiative loading.
Missing current outputs or artifact-integrity errors fail closed. Structurally nonconforming but
readable current artifacts record a failed result rather than disappearing as an exception.

Resource-free and template-only pack digest payloads remain unchanged. Existing 0.1 and 0.2
research locks need no migration. One new public definition schema raises the export count from 50
to 51.

## Design evidence

[ADR-0046](../adr/ADR-0046-declarative-structural-evidence-validation.md) records the declarative
vocabulary, authority separation, digest, execution, check, compatibility, and non-truth decisions.

## Validation evidence

- focused M5 and pack coverage: 17 passed;
- expanded M5, artifact/evidence, and executable-validator coverage: 36 passed;
- complete local suite: 289 passed and 6 expected Windows privilege-based symlink skips;
- Ruff: clean;
- strict Pyright: 0 errors and 0 warnings;
- `git diff --check`: clean;
- isolated source and wheel build: clean with Hatchling 1.31.0;
- clean Python 3.14 installed-wheel smoke: locked validator inspection, both passing structural
  checks, no validator run or capability, 51-schema export, abandonment archive reload, and
  `doctor` all passed; and
- remote CI was intentionally not inspected or claimed. It remains deferred to M5 closeout.

## Stop point

Stop after data-only structural evidence validation. Do not implement shared conformance,
explanation profiles, resumption, discovery, instantiation, citation resolution, semantic
evaluation, or later M5 behavior.
