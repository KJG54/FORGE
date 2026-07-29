# Troubleshooting

Start with read-only inspection:

```console
forge --version
forge config validate
forge doctor
forge status
forge next
```

Do not edit `.forge/` in response to an error. Capture the command, stable exit code, displayed
detail, current commit, FORGE version, operating system, Python version, and whether another
process may still be active. Do not copy secrets or raw local captures into public reports.

## Exit-code categories

| Code | Category | Meaning | First action |
|---:|---|---|---|
| 2 | usage | The command line is incomplete or invalid | Run `forge <command> --help` |
| 10 | configuration | Configuration, pack, or requested data is invalid | Run `forge config validate` and inspect the named file |
| 20 | authorization | The actor or exact approval cannot authorize the action | Inspect owner, pack trust, and capability approval |
| 21 | transition | Current lifecycle state does not allow the request | Run `forge status` and `forge next` |
| 30 | integrity | Persisted state, digest, replay, or referenced bytes disagree | Stop mutation; run `forge doctor`; select a narrow recovery path |
| 31 | conflict | Valid current facts conflict with the request | Inspect active runs, current revisions, IDs, and receipts |
| 40 | security | A path, secret, executable, import, or trust rule refused the request | Preserve the refusal; inspect the security boundary |
| 50 | external tool | An approved external executable failed or could not be supervised | Inspect bounded local diagnostics and tool availability |
| 70 | internal | FORGE encountered an unclassified implementation failure | Preserve diagnostics and report the exact revision |

Handled failures may create a local structured audit event containing the category and a digest of
the displayed detail. It does not contain the raw error, arguments, environment, or provider output
and is not governed evidence.

## Decision table

| Symptom | Inspect | Supported response |
|---|---|---|
| `forge` is not found | Installation environment and `forge --version` | Reinstall the exact wheel using [installation](installation.md); do not run from the source tree as release evidence |
| Repository is not initialized | `forge.yaml` and `.forge/` presence | Follow [initialization](user-guide/initialization.md) |
| Configuration or pack is invalid | `forge config validate`, `forge pack validate <id>` | Correct the ordinary source file; never weaken the validator |
| No legal workflow action | `forge status`, `forge next`, `forge run list` | Complete prerequisites, cancel the exact active run, or obtain the required owner decision |
| Working artifact drift | `forge artifact show <id>`, `forge status` | Review bytes and record `forge artifact revise`; re-establish stale downstream facts |
| Snapshot missing or mismatched | `forge doctor`, complete journal health | Owner uses `forge recover` only if the journal and governed records validate |
| Final journal bytes are truncated | `forge doctor` | Use `forge recover` only for the one proven EOF-truncated M2 tail; ambiguous damage is refused |
| Missing command receipt | Reported interrupted idempotency key | Use `forge recover-command` only for one provably complete registered tail event group |
| Mutation lock appears stale | `forge doctor`; verify process and host | Use `forge remediate-lock` only when the same-host process is proven dead |
| Legacy active journal is read-only | `forge migrate` preview | Owner reviews and applies the one registered migration; archives are never migrated |
| Close or abandon was interrupted | Terminal event/history and staging/archive state | Repeat the exact terminal command with the same idempotency key |
| Pack trust was withdrawn | `forge pack inspect <id>` | Owner reviews the exact locked digest and explicitly restores data trust if appropriate |
| Capability approval is absent or stale | `forge capability inspect <id>` | Review and approve the exact current profile; changed profiles need fresh approval |
| Adapter is unavailable or incompatible | `forge agent doctor` | Use the manual handoff fallback or install a compatible supported executable |
| Import is refused | Preview, staging limits, path/collision detail | Correct the returned bundle or choose explicit collision actions; never bypass screening |
| Archive validation fails | `forge status --archive <id>` | Preserve it unchanged; there is no supported archive repair or reopen command |

## Recovery selection

Recovery commands are deliberately non-interchangeable:

- `forge recover` reconstructs a snapshot from a valid journal or removes one proven truncated
  final journal tail after preserving the complete source.
- `forge recover-command` records an owner decision for one provably complete command whose receipt
  is missing. It does not perform the command or invent events.
- `forge remediate-lock` preserves and removes one exact same-host lock only after proving its
  process is dead.
- `forge migrate` performs one registered format conversion with exact source preservation.
- repeating `forge close` or `forge abandon` with the same key resumes that terminal transaction.

Read [recovery](recovery.md) and [closure and archives](closure-and-archives.md) before mutation. If
the observed state is ambiguous or does not match a documented prerequisite, stop. A manual edit
can destroy the evidence needed to diagnose or recover safely.

## Reporting a reproducible problem

Include:

- the FORGE version and exact repository commit;
- operating system, Python version, and installation method;
- the command name and stable exit code;
- redacted displayed detail;
- whether the repository was active, paused, closed, or abandoned;
- whether another process, migration, recovery, or terminal transaction was interrupted; and
- the smallest synthetic reproduction that contains no owner data, credentials, raw captures, or
  private project artifacts.

Security-sensitive problems follow the private process in [SECURITY.md](../SECURITY.md).
