# User Guide

This guide follows one initiative from installation to an immutable terminal archive. Commands use
the bundled `software-basic` workflow; the `research-basic` workflow follows the same governance
sequence with seven research-specific steps. Use `forge <command> --help` for the complete option
set and [the static examples](../../examples/README.md) for mapped sample artifacts.

## 1. Install and initialize

Install the exact built distribution using the [installation guide](../installation.md). Then
initialize an ordinary project repository:

```console
forge init --owner-name "Repository Owner"
forge config validate
forge doctor
```

Initialization preserves unrelated content, creates tracked `forge.yaml` and `.forge/` governance
paths, and appends the hybrid Git policy. Review the detailed
[initialization guarantees](initialization.md) before enabling FORGE in an existing repository.

`forge doctor` is read-only. A healthy result means the implemented structural and integrity checks
passed; it does not mean project work is correct or accepted.

## 2. Inspect and create

Inspect the available declarative packs before trusting one:

```console
forge pack list
forge pack validate software-basic
forge pack inspect software-basic
forge create "Deliver the approved change" \
  --scope "Only the declared local change" \
  --pack software-basic \
  --trust-pack-data
```

Creation is owner-authorized and locks the exact pack, workflow, explanation profile, objective,
and scope. Data trust does not approve an executable capability. One repository can have only one
active initiative.

## 3. Inspect the next legal action

Use these commands after creation and whenever a process, terminal, or chat restarts:

```console
forge status
forge next
forge history
```

They validate the journal, locked records, preserved objects, and snapshot before reporting state.
The journal is authoritative; `state.json` is a reconstructable view.

## 4. Complete one workflow step

Repeat this sequence for the current ready step. Replace values in angle brackets with identifiers
printed by the preceding commands.

```console
forge begin discover

forge artifact add artifacts/objective-and-constraints.md \
  --role objective-and-constraints \
  --title "Objective and constraints" \
  --media-type text/markdown
forge artifact add artifacts/requirements.md \
  --role requirements \
  --title "Requirements" \
  --media-type text/markdown

forge complete discover \
  --assertion "The declared discovery outputs were produced" \
  --limitation "The claim does not establish correctness"

forge check record discover outputs-present \
  --invocation "Manual review of declared files" \
  --outcome passed \
  --exit-status 0 \
  --limitation "Presence does not establish semantic quality"

forge evidence add discover \
  --purpose "Bind the discovery claim, check, and exact output revisions" \
  --claim <claim-id> \
  --check-result <check-result-id> \
  --artifact-revision <objective-revision-id> \
  --artifact-revision <requirements-revision-id> \
  --limitation "The owner must still judge fitness"

forge verify discover

forge acceptance record discover \
  --scope "Exact discovery outputs listed above" \
  --known-limitation "Manual structural review only" \
  --residual-risk "Requirement quality remains owner judgment"
```

The separation is intentional:

1. a participant begins work;
2. artifacts preserve exact output bytes;
3. a worker records a claim;
4. checks evaluate declared conditions;
5. evidence binds durable support and limitations;
6. FORGE derives whether verification conditions are current; and
7. only the configured owner records owner acceptance.

Use [artifacts and evidence](../artifacts-and-evidence.md) for the detailed record model and
[acceptance and invalidation](../acceptance-and-invalidation.md) before revising accepted work.

## 5. Use workers without transferring owner authority

The manual path is always available:

```console
forge agent context
forge handoff <step-id>
forge import-result <result-directory>
```

The import command previews untrusted returned files before explicit application. Installed Codex
and Claude Code adapters can be inspected with `forge agent doctor`; compatible local execution
uses a disposable output workspace and still returns through the same untrusted boundary. See
[agent adapters](../adapters.md) and [handoffs and imports](../handoffs-and-imports.md).

Local validators are separate executable capabilities. Their declaration, exact owner approval,
execution result, evidence, verification, and acceptance remain distinct. See
[validators](../validators.md).

## 6. Pause, rework, or change scope

Pause when the owner intentionally suspends mutation:

```console
forge pause --reason "Waiting for owner review"
forge status
forge resume
```

The derived long-gap summary contains record references and digests, not artifact content. Read
[continuity](../continuity.md) for the restart-independent boundary.

If governed bytes change, record a new artifact revision. FORGE preserves the old revision and
invalidates dependent current facts. Restart an invalidated step with `forge begin <step-id>` and
re-establish claims, checks, evidence, verification, and acceptance.

Use `forge scope amend` only for an explicit owner-authorized scope change. An amendment does not
waive workflow requirements or accept reworked results.

## 7. Close or abandon

Successful closure requires every step to be completed and currently accepted, exact working
bytes, healthy integrity, no active run, and any configured clean-Git gate:

```console
forge close --summary "All governed outputs are accepted"
forge status --archive <initiative-id>
forge history --archive <initiative-id>
```

If work should end without a successful outcome, preserve that fact distinctly:

```console
forge abandon \
  --reason "The initiative should stop" \
  --unfinished-work "Describe remaining work" \
  --risk "No accepted outcome exists"
```

Both operations create immutable terminal archives through resumable transactions. Abandonment is
not closure. Read [closure and archives](../closure-and-archives.md) before a terminal decision.
Continued work starts a new [successor initiative](../successors.md); archives never reopen.

## 8. Respond to failures conservatively

Do not edit `.forge/` to make an error disappear. Start with:

```console
forge doctor
forge status
```

Then use the [troubleshooting decision table](../troubleshooting.md). Snapshot recovery, truncated
journal recovery, interrupted-command receipt recovery, stale-lock remediation, migration, and
interrupted archive completion are different procedures. Each fails closed unless the observed
state matches its narrow proof.

## Routine owner checklist

- Review `forge status`, `forge next`, and working-tree changes before mutation.
- Keep idempotency keys stable when retrying an interrupted mutation.
- Keep secrets and raw local captures outside governed paths and version control.
- Treat worker output, process success, checks, and evidence as inputs to owner judgment.
- Back up the complete repository, including hidden `.forge/` content, before external storage
  maintenance.
- Validate an archive before relying on it, and use a successor rather than editing terminal
  history.
