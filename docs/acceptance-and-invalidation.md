# Acceptance, Decisions, and Invalidation

M1 Increment 5 completes the approval boundary of the active workflow slice. It does not add
handoff, import, or closure behavior.

## Owner acceptance

`forge acceptance record <step> --scope <scope>` is owner-only and requires the step to be
`awaiting_acceptance`. FORGE derives current support rather than trusting caller-supplied IDs: the
acceptance binds exact current artifact revisions, a passing result for every declared check, and a
current evidence packet that connects those results to a current claim. Known limitations and
residual risks remain explicit fields.

Acceptance is a separate fact. A successful run, claim, passing check, or evidence packet never
implies it.

```console
forge acceptance record discover \
  --scope "Discovery outputs only" \
  --known-limitation "Presence check only" \
  --residual-risk "Semantic quality remains owner judgment"
forge acceptance show
```

## Revocation and revisions

`forge acceptance revoke <acceptance-id> --reason <reason>` creates a new owner-authorized
`ApprovalRevocation`; it never edits the prior acceptance. Revocation invalidates the accepted step
and resets untouched descendants to `pending`.

Likewise, `forge artifact revise` preserves the prior revision and recursively marks records bound
to it stale. This includes claims, checks, evidence, acceptances, and decisions bound to the prior
content digest. Worked affected steps become `invalidated`; untouched dependent steps reset to
`pending`. Any active run in that region loses active authority.

An invalidated step can be restarted explicitly with `forge begin <step>`. New claims, checks,
evidence, and owner acceptance must then bind the current revisions. Historical stale records remain
available for audit and cannot satisfy current transitions.

## Scope amendments

`forge scope amend` records the configured owner's complete new effective scope without editing the
initiative creation record. Every `--requirement` must exist in the locked workflow, every optional
`--artifact` must identify a current logical artifact, and `--return-to` selects the step that must
be redone.

```console
forge scope amend \
  --scope "Discovery now includes compatibility constraints" \
  --rationale "The supported platform boundary changed" \
  --return-to discover \
  --requirement requirements \
  --artifact <requirements-artifact-id>
forge scope show
```

FORGE derives affected checks, acceptances, gates, records, and descendants. It refuses the
amendment if an affected run remains active; cancel that run explicitly first. A ready or worked
return step becomes `invalidated`; a return step whose prerequisites are unresolved remains
`pending`. The latest validated amendment is used as approved scope in newly generated agent
context.

A scope amendment is not an override or acceptance. It cannot satisfy a claim, check, evidence,
verification, gate, or acceptance requirement. Rework must establish every current fact again.

## Decisions and supersession

`forge decide` records an append-only owner decision with considered options, outcome, rationale,
affected record IDs, and optional digest bindings. `--supersedes <decision-id>` records a separate
`DecisionSupersession`; the prior decision file is preserved and becomes stale while the
replacement becomes the open decision.

```console
forge decide \
  --type scope-choice \
  --question "Which boundary applies?" \
  --option narrow --option broad \
  --outcome narrow \
  --rationale "Minimize risk"
```

`forge status` displays invalidated steps, stale record IDs, and open decision IDs. Full restart
validation cross-checks each governance record against its journal event and reconstructs the same
effective state.
