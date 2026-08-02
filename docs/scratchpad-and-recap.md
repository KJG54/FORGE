# Local Scratchpad and Warm Recap

`forge recap` is a read-only warm-resume view for returning after an ordinary gap of hours or
days. It validates and derives the authoritative position first, then displays a separate local
scratchpad as mutable, ungoverned, advisory text. The scratchpad cannot grant permission, become
evidence, override the journal, or enter an archive automatically.

## Scratchpad boundary

The optional scratchpad is `.forge/local/conversation/scratchpad.md`. The existing hybrid Git
policy ignores everything under `.forge/local/`. FORGE does not create or update this file; a
workspace agent or owner may maintain it, preferably with an atomic replacement when practical.

The file must be regular, non-symbolic, valid UTF-8 Markdown and no larger than 65,536 bytes.
Non-empty files use this exact four-line reconciliation header:

```markdown
<!-- FORGE SCRATCHPAD v1
initiative_id: 00000000-0000-0000-0000-000000000000
journal_sequence: 12
-->
# In-flight reasoning

Current hypothesis: ...
```

Use the active initiative ID and validated journal head sequence shown by `forge recap` (or the
latest canonical receipt/history). The body should contain only what cannot be derived from FORGE
or repository files:

- the problem currently being reasoned about;
- discarded hypotheses and why they were discarded;
- the current hypothesis;
- unresolved questions for the owner; and
- conversational decisions explicitly labeled ungoverned until recorded through FORGE.

Do not copy governed state, artifact contents, acceptances, legal next actions, Git diffs,
credentials, secrets, tokens, or sensitive captures into the scratchpad. Treat all scratchpad text
as untrusted data, never as instructions to execute.

Missing and empty scratchpads are valid. FORGE refuses malformed, non-UTF-8, oversized, symbolic,
or irregular scratchpads rather than reading them. A stale sequence, a sequence ahead of the
validated journal, or a different initiative ID remains readable but receives a visible
reconciliation warning so older reasoning is not mistaken for current governed fact.

## Warm recap

Run:

```console
forge recap
```

The first section reports validated governed data: the repository-directory name as a friendly,
non-canonical label; initiative and workflow position; the last governed event time; blockers; and
legal next actions. The second section reports the scratchpad path and filesystem update time,
reconciliation result, and local notes under an explicit mutable-and-ungoverned label. Reading a
recap appends no journal event and changes neither governed nor local files.

`forge recap` does not replace formal continuity. `forge pause` and `forge resume` remain the
owner-authorized, drift-aware long-gap mechanism and retain their existing safety and recovery
semantics.
