# Project-basic friction report

## Scope and evidence basis

This report reviews the completed verification report for friction visible in the implementation
and validation process. It does not manufacture owner-observed dogfood results or make release
decisions.

## Observed friction

| Finding | Classification | Impact | Mitigation or follow-up |
|---|---|---|---|
| A general-project workflow must make unfamiliar work approachable without changing governance. | Product/adoption risk | Moderate | `project-basic` provides document-first interview groups, small question batches, profiles, and phase guidance, while tests assert identical transition and acceptance boundaries. Owner-observed dogfood remains the next qualitative check. |
| Mandatory research can feel artificial for work already supported by sufficient materials. | Workflow friction | Moderate | The readiness report explicitly supports an evidence-based no-new-research-needed result, naming material considered, sufficiency basis, uncertainty, and owner review. |
| The fixed DAG cannot conditionally omit a phase. | Design constraint | Low to moderate | Research remains a real, documented phase rather than a hidden skip; no conditional lifecycle semantics were introduced. |
| Templates are reference-only rather than generated or automatically attached to artifacts. | Expectation/UX risk | Low | Documentation and templates state list/show-only behavior. Automation would require separately authorized runtime work. |
| Pack guidance is not rendered by dedicated guide/interview commands. | Discoverability limitation | Moderate | The explicit scope excludes new CLI guidance commands. Companion and workflow documentation route the experience; future owner-observed feedback can justify a successor. |
| Built-wheel validation needed external dependency access. | Environment/tooling friction | Low | The source and focused tests were local; installed-wheel smoke passed after the isolated environment was allowed to obtain declared dependencies. |
| Broad pytest attempts did not emit a final summary through this terminal bridge. | Validation-observability limitation | Moderate | The verification record makes no full-suite claim and relies on the completed focused suite plus source and installed-wheel checks. Re-run in a stable terminal/CI before broader release decisions. |
| Clean-worktree policy blocked terminal closure while scoped source and governed records were uncommitted. | Git/closure coordination friction | Low | The Git/closure guide now requires an intentional scoped commit, optional owner-directed push, and a clean status before separately authorized closure. Neither commit nor push implies FORGE acceptance or a release. |

## Positive controls retained

- The workflow remains data-only; no executable capability, profile switching, persisted approval
  envelope, template generation, core lifecycle change, or CLI-default change was introduced.
- Existing `software-basic@0.6.0` and `research-basic@0.4.0` digest identities remained pinned.
- Evaluation and review guidance distinguish a finding, a check, FORGE verification, and owner
  acceptance instead of turning advice into an automatic transition.

## Conclusion

The implementation has manageable documented friction for an experimental pack. The material
friction is qualitative adoption and teaching fit, which cannot be resolved by structural tests;
it remains intentionally delegated to owner-observed dogfood rather than asserted as complete.
