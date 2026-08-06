# M6 Increment 7 — Governed Self-Dogfooding

## Authorized scope

- add a data-only repository-local framework-change pack;
- initialize the FORGE source repository under its configured owner;
- require a clean Git worktree before successful closure;
- create one real M6 release-candidate initiative using the locked local pack;
- register exact dogfood-scope and release-requirement artifact revisions;
- record a bounded worker claim, manual structural check, and digest-bound evidence;
- advance the `scope` step to `awaiting_acceptance`;
- generate neutral canonical context for continued release work; and
- document the workflow, trust, authority, persistence, and stop boundaries.

## Explicit exclusions

Runtime behavior, public contracts, schema versions, migrations, bundled pack bytes, dependencies,
executable capabilities, adapters, automatic acceptance, M6 closeout, the final friction and
residual-risk report, release readiness, CI configuration, signing, tagging, publication, version
`1.0.0`, and M7 work are not implemented.

The complete suite, distributions, clean-wheel environments, expanded installation matrix, remote
CI, fresh-user exercises, and operational procedure rehearsals remain deferred to M6 closeout by
owner direction.

## Authority and trust boundary

The configured owner identity is derived from the repository's existing Git author display name.
It records authority but is not authentication.

The local pack contains YAML only and declares no capability. `trusted-data` permits the exact
locked workflow bytes to define steps; it cannot execute code, create evidence, accept work,
resolve risk, close M6, or authorize M7.

Increment 7 uses ordinary CLI services to record claim, check, evidence, and the verification
transition. It does not run `forge acceptance record`. The active step therefore proves both that
the evidence path works and that the configured-owner gate remains effective.

## Persistence and compatibility

Tracked `forge.yaml` configures the local pack and Mentored presentation. Tracked `.forge/active/`
contains the initiative, exact pack and workflow locks, pack-trust decision, hash-chained journal,
bound snapshot, preserved objects, artifact/claim/check/evidence/run records, and derived neutral
context. `.forge/local/` remains ignored.

No existing contract or storage format changes. The project uses the accepted schema-`1.0`
contracts and current journal format. Later supported commands may append records and update the
active snapshot; terminal closure must archive the initiative instead of rewriting history.

## Architecture evidence

[ADR-0056](../adr/ADR-0056-tracked-self-dogfood-workflow.md) records the decision to use real tracked
self-governance, a release-specific local pack, exact data trust, clean-Git closure, and a hard stop
before owner acceptance.

## Validation evidence

Focused local validation passed on Windows with CPython 3.14 and FORGE `0.1.0a0`:

- 2 focused pack and live-state tests passed;
- 4 documentation-route conformance tests passed;
- Ruff reported `All checks passed!`;
- strict Pyright reported `0 errors, 0 warnings, 0 informations`;
- configuration schema `1.0` validated;
- the capability-free `forge-framework-change` pack validated at digest
  `sha256:6e9ab5f0cdc8e67757b3fcd8cc710936149ca8f4df3a6c81d3fc0be29e3b68f4`;
- `forge doctor` reported healthy configuration, layout, packs, journal, snapshot, locked workflow,
  governed records, archives, idempotency, Git policy, and capability boundaries;
- active status reported healthy integrity, trusted pack data, and `scope: awaiting_acceptance`;
- history validated all 9 events through journal head
  `sha256:7aba0d7372f1d701cae2b493fa52bab7736d143f6c4d0fc24cf2d0eccc51bbe5`;
- neutral canonical context reported owner acceptance as the only current blocker; and
- formatting and diff checks reported no errors.

Doctor's only pre-publication warning was that the newly created governed files were untracked.
Staging the exact Increment 7 scope resolved it: the final pre-commit doctor pass reported 27
tracked governed files and healthy repository status. Broad release validation remains Increment 8
closeout evidence.

## Stop point

Stop with the healthy initiative's `scope` step at `awaiting_acceptance`. Do not accept scope,
begin implementation, produce the final friction or residual-risk report, change CI, claim M6
readiness, or begin M7 without separate owner decisions.
