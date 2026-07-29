# M5 Increment 7 — Shared Pack Conformance and Milestone Closeout

## Authorized scope

- run both bundled packs through one shared conformance contract;
- prove matching transition, actor, acceptance, profile, compatibility, and digest invariants;
- prove every required input is produced by a prerequisite step;
- create both bundled initiative types through the unchanged lifecycle service;
- audit public contract field names for software/research neutrality;
- validate and create an existing repository-local pack containing no Python or executable content;
- compose the evidence from all seven M5 increments against every roadmap exit criterion;
- run cumulative source, distribution, installed-wheel, and cross-platform CI validation;
- publish the M5 implementation evidence report; and
- leave formal owner acceptance pending an explicit owner decision.

## Explicit exclusions

New workflow behavior, schemas, records, pack versions, templates, validators, explanation
profiles, discovery behavior, SQLite FTS, semantic search, automatic context mutation, provider
features, release-candidate work, production-version commitments, and automatic owner acceptance
are not implemented.

## Authority, persistence, and compatibility

Increment 7 is test and evidence work. It creates no new runtime authority and changes no supported
transition. Conformance tests exercise ordinary owner-authorized initiative creation but cannot
accept the milestone or any project work.

No public contract, persisted record, pack byte, schema version, or migration changes. The public
schema bundle remains 51 models and 52 exported files including its index. Existing locked packs
and initiatives remain unchanged.

## Exit-criteria evidence

| M5 exit criterion | Closeout evidence |
|---|---|
| Software and research initiatives use unchanged core services | One parameterized conformance test loads and creates both bundled initiatives through the same loader, validator, authorization, lifecycle, replay, and storage services; existing full software and research lifecycle acceptance tests close both domains |
| Core schemas require no software-specific fields | The complete public model registry is audited for software/research-specific contract and field names; all 51 models remain domain-neutral |
| A long-paused initiative resumes without chat history | Increment 5 derives, displays, digest-binds, replays, and tamper-checks the canonical resumption summary using governed records only |
| All explanation profiles preserve identical governance | Increment 4 parameterizes both bundled packs across Minimal, Standard, Guided, and Mentored and compares identical workflow authority and initial materialized state |
| A data-only pack can be created and validated without Python code | Closeout copies the static community-research fixture containing only YAML, configures it as a repository-local pack, validates its digest and contracts, and creates an initiative through ordinary core services |

The Increment 6 measured scenarios reached perfect precision and recall, so the roadmap's
evidence-trigger for SQLite FTS was not met.

## Architecture evidence

No ADR is required because Increment 7 introduces no architecture, trust, authority, process,
persistence, recovery, security, public-contract, or CLI decision. It proves the accepted
boundaries from ADR-0044 through ADR-0049 and the unchanged foundational contracts.

## Validation evidence

- shared closeout conformance: 4 passed;
- cumulative M5 coverage: 33 passed with 1 expected Windows privilege-based symlink skip;
- complete local suite: 310 passed with 7 expected Windows privilege-based symlink skips and no
  failures;
- Ruff clean, strict Pyright clean with 0 errors and 0 warnings, and `git diff --check` clean;
- source distribution and wheel built successfully with Hatchling 1.31.0;
- a clean Python 3.14 installed-wheel smoke validated both bundled packs, created a Mentored
  `research-basic` initiative, passed restart/doctor health, imported FORGE from `site-packages`,
  and exported all 52 schema files for the unchanged 51 public models; and
- the published Increment 6 baseline passed both push-triggered and pull-request-triggered
  Windows, macOS, and Ubuntu CI jobs on PR #5.

The remote baseline proves the published Increment 6 revision across all target operating systems.
It is not claimed as exact Increment 7 evidence. Exact closeout-branch CI remains pending until
Increment 7 is explicitly published.

## Stop point

Stop after the shared suite, complete local/package validation, exact closeout CI evidence, and M5
implementation report are ready for owner review. Do not begin M6, add SQLite FTS, or mark M5
owner-accepted without an explicit owner decision.
