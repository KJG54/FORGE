# Research Example: Volunteer Update Structure

This synthetic project demonstrates the bundled `research-basic` workflow. Its source and citation
records point only to repository-local example notes; it makes no external factual claim.

Start from a writable copy:

```console
forge init . --owner-name "Example Research Owner"
forge create "Compare two structures for a monthly volunteer update" \
  --scope "Use synthetic local evidence to demonstrate traceable research governance" \
  --pack research-basic --trust-pack-data
```

PowerShell users can enter each command on one line instead of using backslash continuation.

## Workflow map

| Step | Register these files and roles | Declared checks |
|---|---|---|
| `frame` | `artifacts/research-question.md` → `research-question`; `artifacts/research-boundaries.md` → `research-boundaries` | `framing-structure-reviewed` |
| `plan` | `artifacts/research-plan.md` → `research-plan`; `artifacts/evidence-criteria.md` → `evidence-criteria` | `plan-structure-reviewed` |
| `collect` | `artifacts/source-register.md` → `source-register`; `artifacts/research-notes.md` → `research-notes` | `evidence-register-structure`; `citation-record-structure` |
| `synthesize` | `artifacts/synthesis-draft.md` → `synthesis-draft`; `artifacts/claims-evidence-map.md` → `claims-evidence-map`; `artifacts/limitations.md` → `limitations` | `synthesis-traceability-reviewed` |
| `verify` | `artifacts/research-verification-report.md` → `research-verification-report` | `verification-structure-reviewed` |
| `review` | `artifacts/research-review.md` → `research-review` | `review-complete` |
| `close` | `artifacts/lessons.md` → `lessons`; `artifacts/closure-record.md` → `closure-record` | `closure-readiness` |

Use the human-directed cycle in [`../README.md`](../README.md) for each row. The two `collect`
checks may use the bundled structural validators, but a passing structural check does not
establish source quality or truth. After every step is accepted, inspect `forge status`, then
close the initiative:

```console
forge close --summary "Reviewed example research workflow completed" -C .
forge doctor -C .
```
