# ADR-0052: Static Example Repositories and Temporary Rehearsal

**Status:** Accepted

**Milestone:** M6 Increment 3

## Context

Release-candidate exit requires fresh users to complete both example workflows from built
distributions. FORGE therefore needs examples that are understandable before initialization,
exercise the real bundled packs, and do not ship fabricated governed history or owner decisions.
The release process also needs one repeatable way to prove that every supplied artifact can pass
through the installed CLI without turning a testing shortcut into real project authority.

## Decision

Ship two ordinary static directories under `examples/`:

- a bounded software-design project for `software-basic`; and
- a synthetic, repository-local evidence project for `research-basic`.

Each directory contains Markdown starting artifacts and a workflow map. It contains no `.forge`
directory, configuration, journal, generated identifier, credential, executable content, check
result, evidence packet, or acceptance.

`tools/example_workflow_smoke.py` is a release-test harness with fixed, typed scenarios matching
the bundled workflows. It copies an example into a new temporary directory, initializes only that
copy, registers the supplied artifacts, records explicitly limited synthetic checks and evidence,
records synthetic-owner acceptance, closes the initiative, validates the archive, and deletes the
temporary directory.

The harness accepts only an exact installed `forge` executable and an example ID. It cannot target
an existing repository or retain its synthetic governed state. It uses argument-vector subprocess
execution with `shell=False`.

## Consequences

- Readers can inspect or copy examples without inheriting another owner's identity or decisions.
- Release closeout can run identical example rehearsals against an exact built wheel in every
  selected environment.
- A rehearsal pass proves CLI and example completeness only. It does not establish product
  fitness, factual truth, a real owner's acceptance, or fresh-user usability.
- Human fresh-user walkthroughs remain necessary at M6 closeout; automated rehearsal is not a
  substitute for friction observation.
- No public contract, persistence format, runtime command, authority rule, package version, or CI
  workflow changes.
