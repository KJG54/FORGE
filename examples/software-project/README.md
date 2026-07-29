# Software Example: Release-Note Formatter

This synthetic project demonstrates the bundled `software-basic` workflow without requiring a
compiler, network service, or external tool.

Start from a writable copy:

```console
forge init . --owner-name "Example Software Owner"
forge create "Define a deterministic release-note formatter" \
  --scope "Document and review a bounded formatter design" \
  --pack software-basic --trust-pack-data
```

PowerShell users can enter each command on one line instead of using backslash continuation.

## Workflow map

| Step | Register these files and roles | Declared checks |
|---|---|---|
| `discover` | `artifacts/objective-and-constraints.md` → `objective-and-constraints`; `artifacts/requirements.md` → `requirements` | `outputs-present` |
| `plan` | `artifacts/implementation-plan.md` → `implementation-plan` | `outputs-present` |
| `execute` | `artifacts/project-artifacts.md` → `project-artifacts` | `declared-checks` |
| `verify` | `artifacts/verification-report.md` → `verification-report` | `declared-checks` |
| `review` | `artifacts/review-report.md` → `review-report` | `review-complete` |
| `close` | `artifacts/lessons.md` → `lessons`; `artifacts/closure-record.md` → `closure-record` | `closure-readiness` |

Use the human-directed cycle in [`../README.md`](../README.md) for each row. A manual check records
what a person actually inspected; it does not prove the assertion or grant acceptance. After every
step is accepted, inspect `forge status`, then close the initiative:

```console
forge close --summary "Reviewed example workflow completed" -C .
forge doctor -C .
```

The files describe an example outcome. They are not executable product code and make no production
readiness claim.
