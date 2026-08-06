# Milestone 1 Evidence Report

**Milestone:** M1 — Complete Local Vertical Slice

**Implementation state:** complete; owner review and acceptance pending

**Authorized boundary:** M1 Increment 8 only; M2 has not begun

## Outcome

M1 now provides the smallest complete, local, restart-safe governance workflow specified for the
milestone. A repository can be initialized, a data-only workflow can be selected and locked, work
can be handed off and imported as untrusted content, exact artifact revisions can be claimed,
checked, evidenced, accepted, invalidated, repeated, and closed into a preliminary archive. The
same core services complete both the bundled software workflow and a test-only synthetic community
research workflow.

Standard and Guided profiles select presentation text only. They do not change transitions,
authority, required records, or derived state. Run cancellation is an explicit terminal run event;
it never completes a step and returns only safe work to `ready`, otherwise it moves the step to
`blocked` for owner review.

## Architecture delivered

| Layer | M1 implementation | Evidence |
|---|---|---|
| Contracts | Strict, immutable Pydantic v2 records with schema version `1.0` | `src/forge/contracts`, schema export tests |
| Configuration | Safe bounded YAML, owner bootstrap, no governed secrets | `forge init`, `config show|validate` |
| Packs | Data-only safe-YAML loading, declared-file inventory, digest and compatibility validation | bundled `software-basic`; synthetic `community-research-test` |
| Persistence | Ordered JSONL journal as authority, reconstructable snapshot, atomic file replacement | replay/integrity tests |
| Workflow | Domain-neutral reducer, explicit actor/transition authority, next actions, manual runs | lifecycle and cross-process tests |
| Artifacts | Immutable logical revisions with SHA-256 preserved objects and drift reporting | artifact/invalidation tests |
| Verification | Separate claims, manual checks, evidence packets, and exact-revision binding | verification tests |
| Acceptance | Owner-only acceptance/revocation and recursive staleness | acceptance tests |
| Worker boundary | Portable handoffs and bounded, non-executing, staged result imports | import security tests and walkthrough |
| Closure | Owner-only completion gates and exact-byte preliminary archives | closure/archive tests and walkthrough |
| Diagnostics | Read-only validation of layout, config, packs, active/archive integrity, records, and M1 Git policy | `forge doctor` tests |

The source-of-truth order remains the constitution and accepted decisions, immutable governed
records, the event journal, the reconstructable snapshot, then disposable local caches. Chat is not
authoritative state.

## Schema inventory

`forge schema export` emits an index plus these 37 versioned schemas:

- Governance and identity: `actor`, `owner-identity`, `authority-grant`, `audit-event`,
  `initiative`, `initiative-reference`, `materialized-state`.
- Configuration, packs, workflow, and execution: `project-configuration`, `pack-manifest`,
  `pack-trust-decision`, `workflow-definition`, `step-definition`, `transition-definition`, `gate`,
  `capability-definition`, `run-record`.
- Artifacts and worker exchange: `artifact-record`, `artifact-revision`, `provenance-record`,
  `agent-handoff`, `agent-result`, `returned-file`.
- Verification and acceptance: `claim`, `check-result`, `evidence-packet`, `acceptance-record`,
  `approval-revocation`.
- Decisions: `decision-record`, `decision-supersession`, `emergency-override`, `risk-acceptance`,
  `scope-amendment`, `workflow-deviation`.
- Closure and archive: `closure-record`, `archive-manifest`, `archived-file`,
  `archived-object-reference`.

Run terminal state is derived from immutable journal events. M1 does not overwrite the initial
`run-record` merely to display `succeeded` or `cancelled`.

## Command inventory

- Repository and diagnostics: `forge init`, `doctor`, `status`, `next`, `history`.
- Configuration and schemas: `forge config show|validate`, `forge schema export`.
- Pack and initiative: `forge pack list|validate`, `forge create`, `begin`, `complete`, `close`.
- Runs: `forge run list|show|cancel`.
- Artifacts and verification: `forge artifact add|revise|list|show`,
  `forge check record|list`, `forge evidence add|list|show`, `forge verify`.
- Acceptance and decisions: `forge acceptance record|revoke|show`, `forge decide`.
- Worker boundary: `forge handoff`, `forge import-result`.

Every implemented mutation uses core services that are independently testable. Structured FORGE
errors map to stable nonzero exit categories and expected rejection paths do not emit tracebacks.

## Acceptance walkthrough transcript

The executable transcript is `tests/test_m1_acceptance.py`; each `_run` invocation launches a new
Python process. The software scenario performs:

1. `forge init`, `forge doctor`, and owner-authorized Guided initiative creation.
2. A separate-process status reload.
3. A portable `discover` handoff.
4. Untrusted `AgentResult` preview followed by explicit apply with declared role mappings.
5. A manual run, worker claim, structured check, evidence packet, verification, and exact owner
   acceptance for `discover`.
6. A changed requirements file registered as a new immutable revision. The prior claim, check,
   evidence, and acceptance become stale and `discover` becomes `invalidated`.
7. Rework with new current records and owner acceptance.
8. The remaining `plan`, `execute`, `verify`, `review`, and `close` steps, each through the same
   claim/check/evidence/acceptance boundary.
9. Successful closure, archived status, filtered archived history, and a final healthy diagnostic.

The synthetic scenario installs a repository-local data-only `community-research-test` fixture,
validates its digest without Python extension code, and completes `frame`, `gather`, and
`synthesize` through unchanged lifecycle, artifact, verification, acceptance, and closure
services. Its roles are `question-brief`, `participation-boundaries`, `observation-log`,
`findings-summary`, and `limitations-note`; no software field is required by core.

Additional acceptance coverage proves:

- missing outputs, checks, evidence, or acceptance block progression;
- non-owner actors cannot exercise owner authority;
- traversal, symlink, inventory, size, schema, and recognizable-secret import attacks are bounded;
- Standard and Guided profiles preserve identical workflow transitions and derived next actions;
- safe cancellation returns the step to `ready`, while externally risky cancellation becomes
  `blocked`; neither path records success.

## Validation results

The final validation run for this report records:

- Ruff: passed (`ruff check .`).
- Pyright strict mode: passed with 0 errors and 0 warnings.
- Pytest: 98 passed, 3 skipped in 97.74 seconds on Windows. All skips are symlink-attack
  scenarios that require a Windows privilege unavailable on this host; the same tests execute on
  symlink-capable hosts.
- Wheel and source distribution build: passed with `python -m build --no-isolation`.
- Built-wheel CLI smoke: passed after a forced no-dependency reinstall into the clean smoke
  environment. It exercised help/entry-point loading, initialization, bundled pack discovery,
  diagnostics, Guided initiative creation, run creation, and cancellation.
- CI matrix: configured for Python 3.12 on Windows, macOS, and Linux; remote result requires the
  eventual Increment 8 push and is not claimed by this uncommitted report.

## Known limitations and deferred work

- M1 archive integrity is preliminary and command-level. Event hash chains, archive hash chaining,
  crash recovery, concurrent-writer safety, idempotent retry, and corruption repair belong to M2.
- M1 implements successful closure only. Abandonment and successor initiatives remain M2.
- Check recording is manual structured evidence; M1 does not execute or trust capabilities.
- No agent adapter is configured or invoked. Handoffs are provider-neutral and manual.
- Secret detection is deliberately heuristic; owner review remains required.
- `blocked` cancellation requires owner review; M1 does not add a remediation transition merely to
  make the test workflow more convenient.
- Standard and Guided are the only authorized M1 explanation profiles. Minimal and Mentored remain
  deferred.
- Naming and distribution metadata remain pre-alpha and provisional.

## ESDF concept assessment — no migration

The ESDF material was not modified, imported, copied, or used as a parallel source of truth. No
ESDF importer was added.

The concepts that align with FORGE's independently approved direction are durable externalized
state, bounded resumable context, explicit provenance, and separation of working memory from
authoritative project records. M1 realizes those concepts through ordinary repository files,
immutable records, the journal, the reconstructable snapshot, handoff bundles, and exact artifact
revisions.

A migration or wholesale copy would be harmful at this stage: it would introduce a second state
model, obscure the constitution/ADR authority hierarchy, and expand schema and compatibility scope
without M1 evidence. The recommendation is therefore to leave ESDF unchanged. Any future adoption
must be concept-by-concept, owner-authorized, and justified against measured FORGE limitations.

## Deviations and stop condition

No M2 feature was implemented. The Increment 8 audit found three omitted M1-required surfaces—
`forge doctor`, `forge run list|show|cancel`, and selectable Standard/Guided presentation—and closed
them without changing the approved persistence architecture or trust boundary.

**Stop:** M1 implementation is complete and awaiting owner review. M2 is not authorized by this
report and has not begun.
