# Canonical authority and specification lifecycle changes

## Candidate outcome

This implementation candidate separates five authority types, creates one current governing entry
point, preserves the recovered Production-v1 specification byte-for-byte as historical evidence,
and adds deterministic checks that prevent the authority map and ADR effective-status catalog from
drifting silently.

This is a worker-authored change report. It does not establish a check result, FORGE verification,
owner acceptance, publication, or release.

## Authority model

The candidate defines:

1. normative design;
2. persisted runtime/history;
3. active locked rules;
4. reference content; and
5. derived advisory views.

ADR-0004's persisted ordering remains intact. ADR-0062 partially supersedes only the interpretation
that ADR-0004 is one universal hierarchy. Initiative-scoped owner decisions remain limited to
their recorded applicability and cannot silently amend global architecture.

## Changed-file inventory

| Target | Change |
|---|---|
| `docs/governing-specification.md` | Adds the current concise design and navigation entry point. |
| `docs/constitution.md` | Replaces obsolete milestone mechanics and absent-spec authority with durable governance and typed authority. |
| `docs/architecture.md` | Replaces the blended hierarchy with the five authority types and cross-type conflict handling. |
| `docs/README.md` | Routes maintainers and agents to the governing specification and typed authority map. |
| `docs/history/specifications/README.md` | Records provenance, historical status, byte length, digest, and current references. |
| `docs/history/specifications/FORGE-Production-v1-Master-Implementation-Specification.md` | Preserves the owner-supplied 77,538 bytes unchanged. |
| `docs/history/milestones/constitution-milestone-governance.md` | Preserves the removed constitutional milestone language with provenance. |
| `docs/history/adr/ADR-0062-typed-authority-and-specification-lifecycle.md` | Records the typed model, applicability boundary, and specification lifecycle. |
| `docs/history/adr/README.md` | Documents recorded versus effective status and the catalog fields. |
| `docs/history/adr/index.json` | Catalogs all 62 ADRs and reciprocal partial supersession. |
| `docs/forge-improvement-roadmap.md` | Corrects only the separate project-basic baseline's terminal closure status. |
| `docs/friction-register.md` | Adds the later terminal closure evidence without marking the observed friction fixed. |
| `tools/documentation_consistency.py` | Adds deterministic authority, digest, link, catalog, status, and supersession validation. |
| `tests/test_documentation_consistency.py` | Covers the passing repository plus five negative failure modes. |
| `tools/quality_gate.py` | Runs documentation consistency as part of the existing fast quality gate. |
| `release/authority-specification-lifecycle/framework-changes.md` | Supplies this workflow-required implementation inventory and validation boundary. |

The final row is a narrowly required workflow output. It was not named in the scope artifact's
expected implementation-surface list, so it must receive explicit owner-visible review before
import. It adds no behavior beyond reporting the exact candidate required by the locked
`framework-changes` artifact role.

## ADR effective status

The machine catalog preserves every historical ADR's recorded status. Current effective status is
separate:

- ADR-0004 is partially superseded by ADR-0062 only for the untyped-hierarchy reading.
- ADR-0059 and ADR-0060 are partially superseded by ADR-0061 in the scopes stated by ADR-0061.
- ADR-0058 remains proposed because its immutable document records `Proposed`.
- ADR-0062 is the accepted candidate decision whose effectiveness remains subject to this
  initiative's exact owner acceptance.

ADRs without a date inside their immutable text use their Git introduction date and explicitly
record `date_source: git-introduction`; the catalog does not insert dates into historical files.

## Owner review choices and conflicts

Three judgments are visible for owner review rather than silently treated as settled:

1. **Normative precedence.** The candidate places the Constitution and its change-control boundary
   before an applicable owner decision. This differs from the recovered master specification and
   the earlier review draft, which placed the owner's newest explicit decision first. The candidate
   still gives the owner sole consequential authority, but requires a global architectural choice
   to satisfy the Constitution's recorded ADR process instead of letting an initiative-local
   decision bypass it.
2. **ADR-0058 remains proposed.** Its file records `Proposed` even though related Git-portable
   directory behavior exists. The catalog does not infer owner acceptance from implementation.
   A later explicit decision may accept, reject, or supersede it; this phase leaves it proposed.
3. **Missing historical dates.** Thirty-six ADRs contain no date in their immutable text. Their
   catalog dates come from Git introduction history and are labeled `git-introduction`, not
   presented as text recorded inside the ADR.

## Historical specification preservation

The preserved candidate has:

- byte length: 77,538;
- SHA-256: `ec0da4a895dd762e49746c6f029f6bfca251825e011363c53438e5034ccd764a`;
- no inserted front matter or warning;
- no corrected links or normalized line endings; and
- an adjacent index that clearly marks its instructions and authority claim historical.

## Pre-import validation

The staged candidate was overlaid on the current repository in disposable local validation state.
That overlay produced:

- documentation consistency: passed, 62 ADRs, 103 validated local links, exact historical digest;
- focused documentation-consistency tests: 6 passed;
- Ruff on the changed Python files: passed;
- Pyright on the checker and focused tests: 0 errors, 0 warnings; and
- direct preserved-specification digest comparison: passed.

The first staged pytest attempt encountered the existing inaccessible default Windows pytest temp
directory. Re-running with an explicit writable `--basetemp` passed all six tests; this was an
environment limitation, not a product-test failure.

## Validation still required after import

The exact project targets must be imported before the repository-root quality gate, full test
suite, `git diff --check`, final changed-file inventory, and `forge doctor` can evaluate the real
candidate. Those results remain checks, not owner acceptance. Remote CI remains separate and is
not authorized or claimed by this implementation artifact.

## Preserved exclusions

No runtime source, public contract schema, workflow, pack, protocol, version, installation route,
CLI behavior, journal behavior, security setting, GitHub setting, cleanup target, default workflow,
publication state, terminal archive, or existing accepted ADR body is changed.
