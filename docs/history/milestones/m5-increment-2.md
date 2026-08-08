# M5 Increment 2 — Digest-Bound Research Templates

## Authorized scope

- one research evidence-register template and one citation-record template;
- strict UTF-8, regular-file, symlink, executable-suffix, per-file size, aggregate-size, declared
  inventory, and unique resource-path validation;
- individual SHA-256 template identity and canonical inclusion in resource-bearing pack digests;
- backward-compatible preservation of the pre-resource digest payload for packs with no resources;
- exact pre-event copy into tracked active governed state;
- pre-commit rollback and post-commit fail-closed restart behavior;
- automatic terminal archive inventory and reload validation;
- read-only available-or-locked `forge pack template list|show`; and
- research pack version `0.2.0` with no executable capability declaration.

## Explicit exclusions

Executable structural validators, explanation files, general data resources, template
instantiation or project copying, automatic artifact or evidence registration, citation
resolution, source-quality scoring, semantic or factual truth evaluation, shared pack conformance,
new explanation profiles, resumption changes, filesystem discovery, and later M5 work are not
implemented.

## Authority, persistence, compatibility, and failure semantics

The configured owner still explicitly trusts the complete exact pack digest as data during
initiative creation. That decision authorizes no process and grants no worker owner authority.
Template listing and showing are read-only and journal-neutral.

Resource-bearing creation copies validated bytes to
`.forge/active/pack-resources/<declared-path>` before the creation event commits. A pre-event
failure removes that new tree. After commitment, restart and recovery preflight validate the
locked copies directly rather than consulting the installed or local source pack. Any missing,
changed, extra, symbolic, irregular, oversized, binary, or digest-inconsistent content fails
closed. Closure and abandonment preserve the tree through the existing archive file inventory.

No public Pydantic model changes. Existing manifest fields represent template paths, the no-resource
digest payload is unchanged, prior workflow locks remain readable, and no schema migration is
required. The schema export remains expected at 50.

The templates establish structure and attribution only. They do not establish source authenticity,
authority, currency, correct interpretation, legal reuse, privacy compliance, methodological
validity, or factual truth.

## Design evidence

[ADR-0045](../adr/ADR-0045-digest-bound-pack-templates.md) records the resource digest, exact-copy,
authority, compatibility, restart, archive, CLI, and non-truth decisions.

## Validation evidence

- focused pack, workflow, and M5 coverage: 18 passed;
- focused resource, closure, and abandonment coverage: 20 passed;
- exact M5 Increment 1 and Increment 2 coverage: 8 passed;
- pre-existing cumulative suite, partitioned from the M5 tests: 277 passed and 6 expected Windows
  privilege-based symlink skips;
- combined local result: 285 passed and 6 expected skips;
- Ruff: clean;
- strict Pyright: 0 errors and 0 warnings;
- `git diff --check`: clean;
- isolated source and wheel build: clean with Hatchling 1.31.0;
- clean Python 3.14 installed-wheel smoke: available and locked template list/show, exact digests,
  owner-trusted research creation, restart/status integrity, `doctor`, 50-schema export,
  abandonment, archive reload, and exact archived template hashes all passed; and
- remote CI was intentionally not inspected or claimed. It is deferred to M5 closeout.

## Stop point

Stop after exact research templates and their governed resource boundary. Do not implement
validators, explanation resources, instantiation, conformance, resumption, discovery, or later M5
behavior.
