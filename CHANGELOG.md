# Changelog

All notable changes will be documented here. FORGE follows milestone evidence before public
semantic-version commitments begin at v1.0.0.

## [Unreleased]

### Added

- M5 bounded read-only filesystem context discovery with hard inventory limits, filename-only
  lexical ranking, Git-ignore and configured-secret exclusions, no symlink following, current
  required-input coverage, fail-closed indeterminate results, and measured software/research
  precision and recall without a persistent search index.

- Milestone 0 constitutional, legal, packaging, tooling, testing, and CI foundation.
- Strict schema-versioned M1 canonical contracts and deterministic JSON Schema export.
- Project configuration validation, owner identity bootstrap, and repository discovery.
- Non-destructive `forge init` with safe `.gitignore` merging and repository-bound path checks.
- `forge config show|validate` and stable error categories for the implemented command surface.
- Ordered event journals, deterministic replay, atomic snapshots, and mismatch detection.
- Data-only pack validation, immutable pack/workflow locks, initiative creation, manual runs,
  workflow authority checks, status, and next-action reporting.
- Immutable artifact revisions with content-addressed preservation, drift detection, heuristic
  secret screening, worker claims, manual check results, evidence packets, dependency references,
  and record-backed verification transitions.
- Owner-only acceptance and revocation, append-only decisions and supersession, recursive
  dependency staleness, downstream workflow invalidation, and restart-safe rework transitions.
- Provider-neutral manual handoff bundles and two-phase untrusted result import with bounded
  staging, inventory/path/symlink/secret safeguards, previews, explicit collision actions,
  content-addressed preservation, and single-event artifact registration.
- Owner-only successful closure with complete-workflow and current-acceptance gates, exact-byte
  archive manifests, preserved-object verification, read-only archived status and history, and
  terminal command-level immutability.
- M1 end-to-end acceptance with a restarted-process software walkthrough, a data-only synthetic
  community-research workflow, repository diagnostics, Standard/Guided presentation, and immutable
  event-derived run inspection and cancellation.
- M2 canonical UTF-8 event serialization, SHA-256 previous-hash chaining, snapshot head binding,
  corruption detection, and explicit read-only compatibility for legacy M1 journals.
- M2 repository-wide cross-process mutation locking with bounded owner metadata, live contention
  refusal, platform-safe process liveness checks, stale-lock diagnostics, and ownership-verified
  release.
- M2 journal-bound mutation idempotency with generated or caller-provided keys, canonical request
  binding, exact-event completion receipts, duplicate-free retry, and interruption detection.
- M2 owner-authorized active-snapshot recovery with exact-byte evidence preservation, complete
  journal and governed-record validation, recovery provenance, atomic reconstruction, and
  duplicate-free resume after recovery-event commitment.
- M2 owner-authorized pause and resume with resumable-state digests, active-run refusal,
  inspection-only paused behavior, restart-safe lifecycle restoration, and durable resumption
  summaries.
- M2 resumable successful closure with hardened archive manifests, deterministic staging, atomic
  promotion, archive-before-retirement validation, interruption diagnostics, and duplicate-free
  same-idempotency-key completion.
- M2 owner-authorized abandonment with required reason, unfinished-work and unresolved-risk
  records, explicit active-run refusal, active-or-paused entry, distinct non-success manifests,
  exact governed-history preservation, and resumable atomic archival.
- M2 successor initiative creation with one or more validated archived predecessors, canonical
  lineage links, fresh identities and governance state, no inherited approval, and exact-byte
  predecessor artifact reuse through new provenance-bound registrations.
- M2 validated multi-archive status summaries, detailed terminal and lineage inspection, and
  source-aware filtered archive history with visible journal hash-chain identities.
- M2 registered schema migration with read-only planning, explicit owner apply, exact legacy-byte
  preservation, atomic event-chain conversion, durable provenance, and interruption-safe retry.
- M2 hybrid Git policy with byte-preserving ignore-rule merging, governed-path re-inclusion,
  local-only exclusion, effective ignore and index diagnostics, filesystem-only fallback, and a
  clean-closure gate protected from ignored governed state.
- M2 conservative active-journal recovery for unambiguous EOF-truncated final records, with exact
  damaged-source and snapshot preservation, atomic valid-prefix replacement, owner provenance,
  ambiguity refusal, tamper detection, and interruption-safe retry.
- M2 conservative interrupted-command recovery for one complete active-tail event pattern, with
  owner provenance, exact receipt reconstruction, atomic snapshot-boundary validation, partial
  multi-event refusal, and duplicate-free post-commit resume.
- M2 explicit stale-lock remediation with configured-owner authority, same-host dead-process proof,
  concurrent-mutation exclusion, exact local lock-byte preservation, versioned provenance,
  same-key interruption recovery, and live, foreign-host, malformed, symbolic, changed, or
  ambiguous lock refusal.
- M3 canonical provider-neutral agent context with deterministic tracked JSON and Markdown,
  allowlisted required-input metadata, effective decisions, explicit authority and return
  boundaries, blocker-aware worker permissions, public schema export, and leakage-resistant
  exclusion of unrelated, archived, ignored, environment, local-secret, and non-selected content.
- M3 managed Codex and Claude context references with digest-bound delimited blocks, non-mutating
  create/append/replace/no-change preview, explicit apply confirmation, exact preservation of user
  bytes, context and file race refusal, bounded UTF-8 handling, and atomic vendor-file replacement.
- M3 provider-neutral agent adapter lifecycle interface, built-in process-free manual baseline,
  explicit configured-selection fallback, read-only adapter diagnostics, and canonical-context
  digest binding for portable handoffs without persistence-format changes.
- M3 Codex CLI adapter with process-local discovery, bounded version/feature/authentication probes,
  normalized manual fallback diagnostics, exact canonical-payload validation, and deterministic
  read-only ephemeral invocation preparation without model execution or schema changes.
- M3 Claude Code adapter with process-local discovery, bounded version/feature/authentication
  probes, normalized manual fallback diagnostics, exact canonical-payload validation, and
  deterministic plan-mode invocation preparation with sessions and extensions disabled.
- M3 governed Codex and Claude execution with adapter-attributed durable runs, disposable
  digest-bound workspaces, allowlisted environments, bounded supervision and output capture,
  source-bound untrusted result staging, explicit run-attributed completion, and no automatic
  project application or verification.
- M3 default-disabled executable capability authorization with exact invocation-profile preview,
  owner-scoped approval, immutable revocation, one-time consumption, durable run binding, and
  validation that trusted pack data cannot authorize execution.
- M3 owner-controlled pack data-trust lifecycle with exact locked-pack preview, immutable
  journal-backed trust and untrust decisions, effective-state replay, workflow mutation blocking,
  tamper detection, safe retrust and abandonment, and no executable-authority implication.
- M3 replaceable-worker acceptance proving identical manual, Codex, and Claude context, untrusted
  import, artifact, claim, and lifecycle boundaries; explicit worker acceptance refusal; a built-in
  compatibility matrix; and milestone exit-criteria evidence.
- M4 declarative local validator capabilities with strict tracked profiles, separate executable and
  argument vectors, bounded working directory/timeout/outputs/environment/risk metadata,
  non-executing inspection, exact owner approval, profile-drift invalidation, and continued
  separation from trusted-data packs and check execution.
- M4 supervised local-validator execution with pre-launch immutable run and one-time-approval
  binding, no-shell process creation, credential-denying environment allowlisting, declared
  timeout, bounded local stdout/stderr capture, exact artifact-revision targeting, typed immutable
  pass/fail/timeout/overflow/error check results, and no automatic evidence, verification, or
  acceptance.
- M4 owner-governed scope amendments with complete effective-scope replacement, locked-workflow
  requirement validation, derived downstream support and gate invalidation, affected-run
  cancellation prerequisites, current worker-context propagation, immutable history, and no
  waiver of renewed claim, check, evidence, verification, or acceptance.
- M4 owner-reviewed workflow deviations with exact locked-workflow binding, state-neutral
  observation, immutable decision-backed review, supersession-aware reopening, status and closure
  enforcement, restart validation, archive preservation, and no waiver or override authority.
- M4 non-bypassing emergency overrides with exact locked-workflow requirement/gate targeting,
  explicit residual risk and permanence, state-neutral audit history, fail-closed closure
  enforcement, restart validation, archive preservation, and no fabricated progression support.
- M4 exact override-bound risk acceptance with owner-only authority, digest-bound residual-risk
  acknowledgement, one-current-record enforcement, state-neutral closure resolution,
  scope-amendment staleness, restart validation, and terminal archive preservation.
- M4 append-only risk-acceptance revocation with exact acceptance and override binding,
  owner-only authority, state-neutral blocker reopening, fresh reacceptance, stale-target refusal,
  retry recovery, restart validation, and archive preservation.
- M4 append-only general decision withdrawal with a reserved exact-binding replacement decision,
  configured-owner authority, immutable supersession history, state-neutral authority removal,
  deviation-review reopening, historical inspection, retry recovery, restart validation, and
  archive preservation.
- M4 formal run cancellation with a public immutable cancellation record, exact run and locked
  policy/risk binding, worker-or-owner authority, terminal adapter-execution proof, fail-closed
  live-process refusal, deterministic workflow destination, retry recovery, restart validation,
  inspection, and archive preservation.
- M4 structured local security and failure auditing with a strict public event contract, stable
  classification, privacy-preserving detail digests, atomic local-only storage, best-effort CLI
  capture, filtered inspection, doctor validation, and no workflow-authority implication.
- M4 cumulative adversarial closeout with executable exit-criteria coverage, full canonical claim
  digest binding for new events, backward-compatible restart validation, packaged-wheel
  acceptance, and a formally owner-accepted milestone evidence report.
- M5 bundled data-only `research-basic` pack with declarative question framing, planning, evidence
  collection, synthesis, structural verification, review, and closure; unchanged core lifecycle
  and authority services; and an explicit non-claim of automated factual truth.
- M5 digest-bound research evidence-register and citation-record templates with strict text and
  inventory validation, exact governed active copies, restart and archive integrity, legacy
  no-resource digest compatibility, and read-only available-or-locked template inspection.
- M5 strict data-only research structure validators with digest-bound safe-YAML definitions,
  bounded in-process heading and field checks, exact artifact-revision `CheckResult` capture,
  template-only lock compatibility, and explicit separation from processes, evidence,
  verification, acceptance, and factual truth.
- M5 Minimal and Mentored explanation profiles for both bundled packs, with four-profile
  digest-bound workflow text, identical governance behavior, pre-write availability checks,
  legacy Standard/Guided compatibility, and no explanation-resource or authority expansion.
- M5 canonical long-gap resumption summaries derived from effective scope, workflow state, open
  decisions, current artifact revision references, non-stale evidence, and legal next actions,
  with paused-status preview, hash-bound resume events, stale-reference exclusion, and legacy event
  compatibility.

### Limitations

- Existing M1 archives retain their preliminary guarantee; recovery does not alter archive journals,
  infer missing events, or mark partial interrupted mutations complete.
- Git is optional collaboration and transport infrastructure; FORGE never stages, commits, cleans,
  or synchronizes a repository on the owner's behalf.
- Stale-lock remediation evidence contains host runtime metadata and remains local-only under the
  hybrid Git policy; it does not alter or repair governed initiative history.
- Provider APIs, executable pack providers, background execution, cross-process live cancellation,
  automatic crash resume, hostile-code isolation guarantees, and automatic verification remain
  deferred to later milestones.
- Project and distribution naming remain provisional.
