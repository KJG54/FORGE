# Governing FORGE's Own Release Work

M6 Increment 7 initializes the FORGE source repository as a real FORGE project. This is live
dogfooding, not a temporary demonstration: tracked `forge.yaml` and `.forge/` records govern the
remaining release-candidate work.

## Framework-change workflow

The repository-local `packs/forge-framework-change/` pack is declarative YAML, declares no
capabilities, and is trusted only as the exact data locked by the active initiative.

| Step | Required output |
|---|---|
| `scope` | Change scope and release requirements |
| `implement` | Exact framework-change manifest |
| `verify-release` | Release validation report |
| `review-risk` | Friction and residual-risk reports |
| `closeout` | Release-readiness record and lessons |

Every step preserves the ordinary FORGE sequence: worker claim, declared check, evidence packet,
verification transition, and configured-owner acceptance. The custom domain language does not
change authority or create an executable path.

## Current boundary

Increment 7 registers:

- `release/dogfood/change-scope.md` as `change-scope`; and
- `release/dogfood/release-requirements.md` as `release-requirements`.

The `scope-reviewed` check and one evidence packet bind the exact preserved revisions and bounded
worker claim. The `scope` step deliberately remains `awaiting_acceptance`. A passing check, this
documentation, a merged pull request, or the agent performing release work cannot accept it.

Inspect the complete boundary before any owner decision:

```console
forge status
forge history
forge artifact list
forge check list
forge evidence list
forge agent context
```

If the configured owner accepts the exact current scope after inspection, the separate command is:

```console
forge acceptance record scope --scope "<exact accepted scope>"
```

Known limitations and residual risks supplied to that command are owner facts, not values a worker
should invent.

## Continuing the initiative

After explicit scope acceptance, Increment 8 can advance the remaining steps using the normal
artifact, claim, check, evidence, verification, and acceptance commands. It must register exact
release outputs instead of treating console success or CI status as an artifact.

Do not edit `.forge/active/` records manually. Regenerate derived context through
`forge agent context`, diagnose through `forge doctor`, and use supported recovery commands for
integrity failures.

The hybrid Git policy tracks `forge.yaml` and governed `.forge/` state while ignoring
`.forge/local/` locks, staging, captures, caches, and secrets. Configuration requires a clean Git
worktree before successful closure so the final archive cannot silently describe uncommitted
release evidence.

## Non-claims

Dogfooding does not authenticate the configured owner, make the same-user threat model adversarial,
prove release readiness, resolve residual risk, accept M6, authorize M7, publish version `1.0.0`, or
turn trusted pack data into executable authority.
