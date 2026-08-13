# Git publishing and clean-worktree closure

FORGE and Git record different facts. Git records project-file history and may publish a branch to
a remote; FORGE records governed scope, claims, checks, evidence, verification, owner acceptance,
and terminal archival. Neither system implies the other.

## Why `forge close` can refuse a dirty worktree

Some FORGE projects configure terminal closure to require a clean Git worktree. This prevents a
closed archive from being detached from the source changes and governed records it describes. When
`forge close` reports a dirty-worktree blocker, it has not archived the initiative and has not
discarded any changes.

Resolve the friction deliberately:

1. Inspect the exact state with `git status --short`.
2. Review the scoped changes, including the tracked `.forge` records that belong to the initiative.
3. Stage and commit only the intended project and governance records on the current branch.
4. Push that branch if the owner wants the Git history published or backed up.
5. Re-run `git status --short`; it must be empty before a clean-worktree `forge close` succeeds.
6. Run the separately owner-authorized `forge close --summary "<owner summary>"`.

Do not delete, reset, or manually edit `.forge` files merely to make Git look clean. Use FORGE's
supported append-only commands for governed state and ordinary Git commands for source history.

## Commit, push, CI, and closure are separate decisions

A commit is not FORGE acceptance. A push is not publication approval, a release, or a replacement
candidate. Passing CI is useful evidence but does not become owner acceptance; conversely, a local
terminal closure may be appropriate after the owner has accepted the exact records even when the
owner chooses to review CI later.

If the owner directs “publish without waiting for CI,” the bounded interpretation is to commit and
push the reviewed branch, report that CI remains unverified, and avoid claiming a release. CI may
still affect a later merge or release decision. The clean-worktree requirement therefore does not
interfere with closure: it supplies a checkpoint that preserves both Git and FORGE history before
the terminal archive is created.

## Safe handoff after closure

After a successful `forge close`, the archive is terminal and immutable. Further work uses a new,
owner-authorized successor; it does not reopen the archive or retroactively alter the commit that
made the worktree clean.
