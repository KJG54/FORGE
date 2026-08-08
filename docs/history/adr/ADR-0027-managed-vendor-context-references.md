# ADR-0027: Managed Vendor Context References

**Status:** Accepted

**Milestone:** M3 Increment 2

## Context

Codex and Claude Code conventionally read root `AGENTS.md` and `CLAUDE.md` files. FORGE must make
its neutral context discoverable through those conventions without taking ownership of the user's
instructions, duplicating authoritative state, leaking existing content into previews, or silently
changing a vendor file.

The master specification permits clearly delimited blocks or references, requires preservation of
existing user content, and requires preview and confirmation before a change.

## Decision

Manage one optional, clearly delimited reference block in `AGENTS.md` for target `codex` and in
`CLAUDE.md` for target `claude`:

```text
<!-- BEGIN FORGE MANAGED CONTEXT -->
...
<!-- END FORGE MANAGED CONTEXT -->
```

The block references `.forge/active/context/current.md` and `current.json`, includes the SHA-256
digest of the exact canonical JSON bytes, restates the non-authoritative boundary, and gives the
target-specific regeneration command. It does not embed the objective, decisions, artifact content,
or any existing vendor-file text.

`forge agent context --target codex|claude` is read-only. It displays the target path, create,
append, replace, or no-change action, current/proposed/context digests, and only the proposed managed
block. `--apply` is the explicit confirmation. The apply path rebuilds the neutral context under the
repository mutation lock and refuses if either the previewed vendor digest or context digest changed.
It regenerates the canonical JSON and Markdown first, rechecks the vendor bytes, and atomically
replaces only the selected root file.

When no block exists, the exact existing bytes remain a prefix and FORGE appends a separated block.
When one valid block exists, bytes before and after its complete marker span remain exact. Existing
LF or CRLF style is used for the managed block. Missing, empty, user-populated, or already-current
files are supported. Symbolic links, non-files, non-UTF-8 Markdown, files or proposed results over
10 MiB, duplicate/incomplete/out-of-order/non-standalone markers, and observed races are refused.

FORGE does not remove user content, stage the file, commit it, change Git ignore rules, invoke a
vendor CLI, create an adapter run, or grant worker authority.

## Consequences

Vendor tools receive a stable conventional pointer to the exact neutral context while the journal,
workflow lock, and governed records remain authoritative. Normal regeneration changes only the
managed span. Preview output cannot disclose existing user instructions because it never renders
the complete proposed file.

The reference can become stale after a governed state change until the owner previews and applies a
refresh; its embedded digest makes that condition visible. Root vendor files are not copied into
initiative archives and a terminal initiative may therefore leave a reference to a retired active
context. FORGE does not silently remove that block because removal is also a vendor-file change that
would require an explicit future previewed operation.
