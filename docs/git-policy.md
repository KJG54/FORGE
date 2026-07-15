# Hybrid Git Policy

FORGE stores authoritative governance in ordinary files. Git can collaborate on and transport
those files, but Git commits, branches, remotes, and hosting services never replace the validated
FORGE journal, locked rules, records, preserved objects, or materialized-state checks.

## Initialization policy

`forge init` preserves existing `.gitignore` content and appends:

```gitignore
# FORGE hybrid policy: track governed state, ignore local-only data
!/forge.yaml
!/.forge/
!/.forge/**
/.forge/local/
```

The negations keep `forge.yaml`, active governance, archives, idempotency receipts, migration and
recovery provenance, and preserved objects visible to Git even when earlier rules ignore YAML or
`.forge/`. The final rule excludes locks, import staging, handoffs, caches, verbose runs, and local
secrets. Existing legacy repositories receive the complete block on their next `forge init`.

FORGE does not stage or commit anything. After review, an owner may use ordinary Git commands such
as:

```console
git status --short
git add -- forge.yaml .forge/
```

The local subtree remains excluded by the generated policy.

## Diagnostics

`forge doctor` is read-only. Inside a Git worktree it checks effective ignore behavior rather than
trusting text alone:

- an ignored governed path is an integrity error because collaboration could omit authoritative
  records;
- a local-only path already tracked by Git is an integrity error because ignore rules cannot
  untrack it;
- a governed file that is visible but not yet tracked is a warning, because staging and commit
  timing belong to the owner;
- a missing Git executable or non-Git directory is a warning, and FORGE continues in
  filesystem-only mode.

If later ignore rules hide governed paths, run `forge init` again to append the policy after those
rules. If Git already tracks a `.forge/local/` path, inspect it for sensitive content before using
an explicit index-only removal such as `git rm --cached -- <path>`. FORGE deliberately does not run
that command for you and never deletes the working file.

## Optional clean-close gate

`behavior.require_clean_git_for_close: true` remains optional. When enabled, successful closure
requires an available Git worktree, a valid hybrid policy, and no tracked, modified, staged, or
untracked worktree changes. Ignored `.forge/local/` activity does not make the worktree dirty.
Abandonment does not require a clean worktree.
