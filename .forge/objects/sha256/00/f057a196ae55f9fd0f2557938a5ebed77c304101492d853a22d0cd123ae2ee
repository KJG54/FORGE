# Profile-Aware Facilitation — Change Scope

Initiative: `fb1e3732-334f-4bb1-9e51-40dad0e9521b`
Pack / workflow: `forge-framework-change` 0.1.0 / `framework-change` 0.1.0
Explanation profile: `guided`
Predecessor: `26c0c628-cc77-478c-b77b-0c1d703891ac` (closed, Local Production-v1)
Step: `scope` — required output role `change-scope`

This artifact declares the bounded framework change. It is a registered project artifact, not an
acceptance. Owner acceptance of the `scope` step is a separate recorded act.

Companion artifact: `release/profile-aware-facilitation/release-requirements.md` (role
`release-requirements`) carries the definition of done and evidence map.

## Provenance labels

- **[Sourced]** — verified from repository state or the supplied handoff.
- **[Owner]** — stated by the owner in conversation.
- **[Agent]** — workspace-agent recommendation.

## Objective

```text
Deliver a beginner-centered, profile-aware collaboration and learning layer for FORGE direct
workspace agents, comprising agent protocol 1.4.0, starter-prompt documentation, additive pack
interview and phase guidance data, profile-differentiated agent behavior, and protocol/CLI
version-skew detection, while preserving every existing governance, authority, compatibility,
and append-only pack-identity boundary.
```

## Declared scope

```text
Introduce FORGE agent protocol 1.4.0 as a strict superset of 1.3.0 and regenerate its
Codex/Claude managed references for profile-aware collaboration, learning goals, phase playback,
and task delegation; add additive, default-empty interview-guidance and phase-guidance fields to
the pack workflow contract with a mandatory software-basic minor-version bump, append-only
(version, digest) identity, unchanged digests for every pack that supplies no guidance, and a
matching release/version-contract.json update; populate that guidance for the bundled
software-basic pack only; add profile-differentiated rendering rules for minimal, standard,
guided, and mentored; add starter-prompt documentation for universal, short, installed-CLI,
GitHub-only, Codex, Claude, manual, beginner, and existing-project cases plus the supporting
README and docs-index entries; add a protocol/CLI version-skew check surfaced by forge doctor;
and add tests for schema compatibility, pack validation, digest identity, context allowlisting,
managed-reference byte preservation, and absence of authority drift.
```

## In scope

1. **Protocol 1.4.0.** **[Owner]** A new version, not an amendment to 1.3.0. Adds
   `src/forge/resources/agent-protocol-1.4.0.md` and updates the constant
   `AGENT_PROTOCOL_VERSION` at `src/forge/core/agent_protocol.py:11`; `AGENT_PROTOCOL_FILENAME`
   derives from it. 1.4.0 requires fresh-agent FORGE identification, small question batches,
   six-heading coverage playback, phase-explicit step presentation,
   owner/agent/either/owner-only task maps, learning-goal elicitation in `guided` and `mentored`,
   must-answer-now versus acceptable-uncertainty separation, and preservation of receipt-quoting
   and owner-gate ceremony. Prior protocol resources remain shipped and unmodified.

   **1.4.0 must be a strict superset of 1.3.0.** The supplied handoff was written against an
   older mental model and omits the following 1.3.0 requirements. Each must carry forward or the
   new protocol is a silent regression:

   - durable-project-home detection before any bootstrap proposal, and "durable project home" as
     a required element of the coverage playback;
   - `forge pack list` and `forge pack inspect <pack-id>` as read-only pre-initialization
     inspection exposing valid symbolic requirement IDs;
   - `forge agent context --apply` as preview-required, owner-directed derived-file maintenance,
     whose preview shows the persistent write set, temporary lock path, managed-marker
     preservation boundary, and zero-journal-event effect;
   - the run-cancellation rule limiting an agent to cancelling only its own active run;
   - the scope-amendment pre-flight requiring `forge pack inspect` and `forge status` first, with
     affected runs cancelled before the amendment command is presented.

2. **Managed references.** Regenerate Codex and Claude context references for the new protocol,
   preserving owner-authored bytes outside FORGE markers.

3. **Pack contract.** Additive, default-empty `interview_guidance` (workflow scope) and
   `phase_guidance` (step scope) fields. Old packs and old locks must load unchanged.

4. **Digest neutrality for empty guidance.** `calculate_pack_digest()` hashes the *parsed model*
   (`workflow.model_dump(mode="json")`), not raw YAML bytes, so a default-empty field still
   enters the payload and would change the digest of every existing pack.
   `src/forge/packs/validation.py:63-67` already establishes the required pattern — step-level
   `explanation_content` is deleted from the payload when empty, commented "Preserve the canonical
   bytes used by pre-L5 locks." Both new fields need the same treatment at step and workflow
   scope. **Default-empty is necessary but not sufficient; the strip is what preserves identity.**

   **[Sourced]** Verified empirically 2026-08-10 against `forge-framework-change` 0.1.0, whose
   steps supply no `explanation_content`:

   | Computation | Digest | Matches manifest |
   |---|---|---|
   | With the strip (current code) | `sha256:6e9ab5f0…3b68f4` | yes |
   | Without the strip | `sha256:b3c19737…a9a2be` | **no** |

   `sha256:6e9ab5f0…3b68f4` is the value pinned in the archived `pack.lock.json` of archives
   `26c0c628` and `ace6c2c9`. An unguarded additive field breaks archived lock validation on real
   existing records.

5. **Pack data.** **[Owner]** Populate guidance for bundled `software-basic` only and bump its
   minor version. `research-basic` and both repository-local packs receive the schema fields as
   default-empty and must emerge with byte-identical digests.

6. **Pack identity.** Enforce and test that a `(pack version, integrity digest)` pair is never
   reused for different content.

7. **Version contract.** Update `release/version-contract.json`, which pins bundled pack versions
   (`research-basic` 0.4.0, `software-basic` 0.5.0) and is asserted by `tests/test_local_v1_l4.py`
   and `tests/test_m7_increment_2.py`. **[Agent]** The contract does not currently record the
   agent protocol version despite agents depending on it as a public surface; adding it is
   recommended while the file is being touched.

8. **Profile behavior.** Rendering and behavior rules distinguishing `minimal`, `standard`,
   `guided`, and `mentored` — qualitative, not numeric. Numeric knobs such as
   `question_batch_size` are excluded because nothing can enforce an agent's question batch size,
   and encoding it as validated pack data implies control that does not exist.

9. **Starter prompts.** `docs/agent-starter-prompts.md` plus README and docs-index links.

10. **Version-skew detection.** `forge doctor` reports when the installed CLI's protocol version
    is older than the repository source, and starter prompts instruct agents to check.

11. **No-active-initiative first contact.** Generated context and starter prompts handle the
    initialized-but-no-active-initiative state honestly.

12. **Documentation.** Updates to `conversational-walkthroughs.md`, `quickstart.md`,
    `agent-context.md`, `pack-author-guide.md`, `workflows.md`, `adapters.md`, and
    `adapter-author-guide.md`, including the note that collaboration style is conversational and
    ungoverned — an owner may ask for less teaching without a governed change.

13. **Tests.** Per the definition of done in the companion `release-requirements` artifact.

## Out of scope

- `forge agent starter`, `forge pack interview`, `forge step guide` — deferred to a named
  successor initiative. The handoff scoped these "if they fit the implementation budget"; a
  conditional inside accepted scope cannot be evaluated at the acceptance gate.
- **Interview and phase guidance data for `research-basic`** — **[Owner]** deferred to the
  successor. It receives the schema fields as default-empty only, and its digest must not change.
- Switching explanation profile after initiative creation.
- Domain-specific curricula, concept packs, or resource catalogs.
- Hosted or multi-user operation.
- Third-party adapter plugin ABI, or new first-class adapter targets.
- Public package publication or release automation.
- Any change to existing archives or historical records.
- Automatic owner acceptance, or any new command that mutates governed state.
- Automatic network installation without explicit owner authorization.
- **macOS performance-budget changes.** Commit `ef8ea35` relaxes three macOS budgets by 67–100%
  with a one-line message and no recorded measurement, bundled into a documentation change. It
  belongs in its own change with a recorded measurement. Its genuine documentation/JSON drift fix
  should be kept.
- Broad task-management features or integrated conversational workflow commands.

## Constraints

- Governance is append-only. No edits to `.forge/` history; corrections use the legal
  invalidation, revocation, decision, or scope-amendment path.
- Schema additions must be additive and default-empty; `forge-contracts-1` compatibility holds.
- Any change to pack guidance data forces a pack minor-version bump.
- Any additive field entering the pack digest payload must be stripped when empty, per the
  established `explanation_content` pattern, so packs supplying no guidance keep their exact prior
  digests and archived locks continue to validate.
- Managed references preserve owner-authored bytes outside FORGE markers exactly.
- No owner-gate command is run by the agent without the exact command displayed and explicitly
  authorized by the owner for that exact command.
- The repository source protocol is authoritative over any stale installed CLI; skew must be
  reconciled before dogfooding produces meaningful evidence.

## Existing assets and predecessor

**[Sourced]**

- `docs/profile-aware-facilitation-plan.md` — the supplied handoff, on branch
  `codex-profile-aware-facilitation-docs`.
- `docs/agent-starter-prompts.md` — already fully written on that branch with README and
  docs-index links; the handoff's entire Phase 2 deliverable, authored before this initiative
  existed.
- Closed archive `26c0c628-cc77-478c-b77b-0c1d703891ac` — Local Production-v1, which produced the
  conversational layer this work extends.
- Closed archive `ace6c2c9-e3b4-40d1-842c-70f10060e0fe` — PR 44 CI repair; not a predecessor.

**[Owner]** Decision 2026-08-10: the branch content is imported as a **supplied asset**, not as
completed or accepted work. Consequences:

- The reusable exact revision is commit `b77ba8a` ("Document profile-aware FORGE facilitation
  plan"), covering `docs/profile-aware-facilitation-plan.md`, `docs/agent-starter-prompts.md`,
  `README.md`, and `docs/README.md`. Commit `ef8ea35` is **not** part of the supplied asset.
- Document statements are inputs, not accepted truth. The starter prompts are re-checked against
  protocol 1.4.0 during `implement` — but not re-authored from scratch.
- Phase 2 already being written does not shorten the workflow. `implement` still produces
  `framework-changes` covering it, and owner acceptance is still required.

**[Owner]** Predecessor `26c0c628-cc77-478c-b77b-0c1d703891ac` confirmed 2026-08-10 and recorded
at creation. Lineage imports no progress or acceptance.

## Durable project home

**[Sourced]** Required by protocol 1.3.0 §"First contact and state detection" item 3.

- Durable location: `C:\Users\kryst\Code\FORGE` on the owner's own machine — not a remote or
  containerized workspace whose filesystem can be reclaimed.
- Published mirror: `https://github.com/KJG54/FORGE.git` (`origin`, fetch and push).
- Governed journal and archives live in `.forge/` inside that repository.

No ephemeral-workspace risk applies; no owner throwaway declaration is needed.

## Labor split

| Party | Work |
|---|---|
| Owner | Authorize every gate command; run dogfooding sessions and author the owner-observed records; decide release readiness. |
| Workspace agent | Draft protocol and schema changes; implement pack data, docs, and tests; run checks; report receipts verbatim; author claims with `--operator direct-claude`. |
| FORGE | Validate packs and locks; enforce transitions, checks, evidence, and acceptance separation; record append-only history. |
| External contributors | None planned. |

## Recorded decisions

| # | Question | Resolution |
|---|---|---|
| 1 | New protocol version or amend 1.3.0? | **[Owner]** New version 1.4.0. |
| 2 | Where does guidance live? | **[Agent]** Workflow YAML at both scopes — `interview_guidance` as a top-level peer of `explanation_content`, `phase_guidance` per step. All candidate locations sit inside the pack digest, but workflow content is captured in `workflow.lock.json` at creation, making an active initiative's guidance immutable for its lifetime — the same property explanation content already has. |
| 3 | Import posture for branch content | **[Owner]** Supplied asset. |
| 4 | Record format for owner-observed evidence | **[Agent]** Dispositions live inside the `friction-report` artifact at `review-risk`. `framework-change` declares only `check-evidence`, which is for checks; human observation must not be dressed up as an automated check. |
| 5 | Explanation profile | **[Owner]** `guided`. |
| 6 | Dogfooding environment | **[Agent]** Build the candidate, install into an isolated environment (precedent: `.smoke-venv`), and run scenarios in a throwaway project outside this repository. `mentored` cannot be exercised from inside the initiative constructing it. |
| 7 | Slice size | **[Owner]** `software-basic` guidance only; `research-basic` deferred. No numeric effort ceiling; bounded by the exclusion list. |

## Accepted uncertainty

**[Owner]** A durable product vision specific to this initiative's intended users was not
separately stated. It is established for FORGE as a whole from `README.md` and the handoff. This
is named here as accepted uncertainty rather than settled fact; the bounded scope keeps affected
work out of bounds.

## Abandonment conditions

**[Owner]** Accepted 2026-08-10. Abandon or re-scope if:

- the schema additions cannot remain additive without breaking `forge-contracts-1`;
- pack identity cannot be preserved append-only across the guidance change;
- dogfooding shows the guidance does not measurably change agent behavior, making the maintenance
  burden unjustified; or
- the work cannot be bounded away from the deferred CLI helpers without leaving the protocol
  incoherent.

## Note on the locked workflow

**[Agent]** The `closeout` step's declared purpose references "release-candidate readiness …
without publishing Production v1," wording inherited from the previous release initiative. The
artifact classes are generic enough to use as-is; this is noted so the mismatch is not a surprise
at that gate.
