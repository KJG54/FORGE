# Manual Handoffs and Safe Result Import

M1 Increment 6 provides the provider-neutral manual worker boundary. It does not invoke an agent,
trust worker claims, run returned content, close an initiative, or grant any owner authority.

## Portable handoffs

`forge handoff <step>` writes a disposable bundle under
`.forge/local/handoffs/<handoff-id>/`:

- `handoff.md` for a worker;
- `handoff.json` as the neutral structured assignment;
- `agent-result.schema.json` as the required return-manifest schema.

The bundle contains the initiative objective, approved scope, active step, constraints, open
decision IDs, permitted and prohibited actions, required outputs, and verification expectations. It
does not contain credentials or confer governance authority. Handoffs are derived local views and
may be removed after use.

```console
forge handoff discover \
  --constraint "Do not modify unrelated files"
```

As of M3 Increment 3, this command prepares the assignment through the built-in manual
`AgentAdapter`. The plan is bound to the exact canonical-context JSON digest, but context is derived
in memory: handoff creation still does not write tracked context views or mutate the journal. The
manual adapter starts no process and preserves the same bundle and staged-import behavior.

## Result bundle contract

The worker returns an `AgentResult` JSON manifest and only the files declared by its
`returned_files` entries. Each file declares a bundle-relative source path, repository-relative
proposed target, optional SHA-256 digest, and optional media type. Claims, limitations, and tool
metadata remain untrusted statements.

The result directory must not contain undeclared files. Source and target paths must be normalized;
absolute paths, traversal, symbolic links, `.forge` targets, configured secret locations, and
recognizable credential patterns are rejected. Configured file-count, per-file, and total-byte
limits are enforced before project mutation. Content is copied to
`.forge/local/import-staging/<result-id>/` and is never executed.

## Preview and explicit application

`forge import-result <manifest>` stages and previews only. Every returned file must resolve to one
explicit registration action:

- a new target requires `--role TARGET=ROLE`;
- a governed target requires `--collision TARGET=revise` and creates a new immutable revision;
- an existing ungoverned target requires both `--collision TARGET=replace` and a role.

Roles must be declared outputs of the source step. A completed source step accepts only governed
revisions, ensuring late results invalidate previously accepted dependencies rather than silently
adding new completion inputs.

```console
forge import-result ../worker-return/result.json \
  --role objective.md=objective-and-constraints \
  --role requirements.md=requirements

forge import-result ../worker-return/result.json \
  --role objective.md=objective-and-constraints \
  --role requirements.md=requirements \
  --apply
```

For a collision:

```console
forge import-result ../worker-return/result.json \
  --collision objective.md=revise \
  --apply
```

`--apply` revalidates staged digests, target fingerprints, actor eligibility, and journal sequence.
It writes project targets, content-addressed objects, imported-result data, and artifact records
before committing one `result-imported` event. Pre-commit failures roll back project targets and new
records. After the event commit, the journal remains authoritative under the existing M1
transaction model. M2 Increments 1 through 3 now add hash integrity, cross-process locking, and
idempotent retry; crash recovery and remaining interruption hardening remain deferred.

Imported files remain ordinary untrusted worker output. Workflow completion still requires a
participant claim, declared checks, evidence, and separate owner acceptance. Handoff and staging
files can disappear without affecting restart validation because governed records and preserved
revision bytes carry the durable import history.
