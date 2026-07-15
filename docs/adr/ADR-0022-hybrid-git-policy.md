# ADR-0022: Hybrid Git Collaboration and Transport Policy

**Status:** Accepted

**Milestone:** M2 Increment 11

## Context

FORGE's governed files are inspectable local authority, while Git is optional collaboration and
transport infrastructure. The M1 initializer ignored `.forge/local/`, but a pre-existing broad
rule such as `.forge/` or `*.yaml` could still hide governed records. Conversely, ignore rules do
not remove a local-only file that a user already added to the Git index. The optional clean-Git
closure gate could also report false cleanliness if governed paths were ignored.

## Decision

`forge init` preserves every existing `.gitignore` byte and newline convention, then appends an
idempotent root-scoped policy that re-includes `forge.yaml`, `.forge/`, and `.forge/**` before
excluding `.forge/local/`. A legacy local-only rule is upgraded. If a later rule conflicts inside
an available Git worktree, a repeated initialization appends the policy again after that rule.

`forge doctor` validates both the declared block and Git's effective behavior. It uses read-only
Git commands to ensure canonical probes and every existing governed path are not ignored,
`.forge/local/` is ignored, and no local-only path is already tracked. Governed files that are
merely untracked produce an actionable warning rather than an integrity failure. Ignored governed
paths and tracked local-only paths fail closed without changing either files or the Git index.

Git remains optional. When Git is unavailable or the project is outside a worktree, FORGE reports
filesystem-only operation and all lifecycle services continue to use governed files normally. If
the owner enables `require_clean_git_for_close`, closure requires an available worktree, a valid
effective hybrid policy, and an empty full-worktree porcelain status.

FORGE never runs `git add`, removes index entries, commits, checks out, resets, fetches, pushes, or
otherwise changes Git state as part of this policy.

## Consequences

Governed state is visible to normal Git collaboration by default while locks, staging, caches,
logs, handoffs, and secrets under `.forge/local/` remain local. Existing ignore content is not
rewritten, so files retain owner formatting and intent. Effective inspection requires a local Git
executable, but its absence never changes FORGE's authority hierarchy.

An owner must still decide when and how to stage or commit governed changes. A previously tracked
local-only file requires explicit owner review and index cleanup; FORGE reports it but never
performs that potentially consequential action.

This decision does not repair journals, remove locks, recover unrelated interrupted commands,
generate agent context, invoke adapters, or authorize capabilities.
