# M5 Increment 1 — Bundled Declarative Research Workflow

## Authorized scope

- one bundled, data-only `research-basic` pack;
- a complete seven-step workflow covering question framing, planning, evidence collection,
  synthesis, verification, review, and closure;
- research artifact roles, structural check identities, context-selection rules, and Standard and
  Guided explanation content expressed only in existing declarative contracts;
- explicit separation of source collection, worker claims, structural checks, governed evidence,
  FORGE verification, and configured-owner acceptance;
- full lifecycle use of unchanged core services, persistence, recovery, archive, CLI, and authority
  behavior;
- safe-YAML, declared-inventory, executable-content, digest, reachability, restart, and archive
  validation; and
- focused source and installed-wheel acceptance plus unchanged public-schema export.

## Explicit exclusions

Research evidence or citation templates, executable structural validators, shared bundled-pack
conformance infrastructure, Minimal and Mentored explanation profiles, new long-gap summaries,
bounded filesystem discovery, SQLite Full-Text Search, source-quality scoring, citation resolution,
semantic or factual truth evaluation, and later M5 work are not implemented.

## Authority, persistence, and failure semantics

The configured owner explicitly trusts the exact pack as data at initiative creation and remains
the only acceptance and terminal-decision authority. Participants and agent adapters use the
existing worker boundary and cannot fabricate owner authority.

The increment adds no persisted schema, event type, migration, recovery path, or executable
capability. Existing pack and workflow locks preserve the exact selected bytes. Invalid or changed
pack content fails before initiative creation; governed restart and archive validation use the
existing exact locked records and journal relationships.

Research checks are structural support only. A passing check, source entry, citation, worker claim,
or evidence packet does not establish correctness or factual truth and does not bypass explicit
verification and owner acceptance.

## Design evidence

[ADR-0044](../adr/ADR-0044-declarative-research-workflow-boundary.md) records the data-only,
unchanged-core, exact-owner-authority, and non-truth decisions.

## Validation evidence

Focused Windows tests validated exact pack identity, step order, roles, actor rules, structural
check names, empty executable/resource declarations, the integrity digest, and a seven-step
research lifecycle through fresh CLI processes. The lifecycle registered ordinary artifacts,
claims, checks, evidence, verification, and owner acceptance, then produced a validated atomic M2
archive.

Local validation on Python 3.14 recorded:

- Ruff passed with no findings;
- strict Pyright passed with 0 errors and 0 warnings;
- the two focused M5 tests passed in 54.56 seconds;
- all 277 pre-existing tests passed with 6 expected Windows symlink-privilege skips in 322.65
  seconds;
- combined coverage was 279 passed and 6 skipped on the same unchanged source tree;
- one monolithic quiet-mode run reached its five-minute command ceiling after reporting only
  passing progress and three expected skips, so the exact suite was completed in the two explicit
  partitions above rather than misreported as one completed invocation;
- isolated source-distribution and wheel builds passed with Hatchling 1.31.0;
- a clean environment installed the built wheel and loaded `forge` version `0.1.0a0` from
  `site-packages`;
- the installed-wheel CLI initialized a repository, listed and validated bundled
  `research-basic@0.1.0`, created an exact-pack-trusted research initiative, reloaded healthy
  status with `frame` ready and all six descendants pending, and exported all 50 public schemas;
  and
- no remote Windows, macOS, or Linux CI result is claimed.

## Stop point

Stop after the bundled research workflow and its acceptance evidence. Do not add templates,
validators, shared conformance work, new explanation profiles, resumption behavior, context
discovery, or search.
