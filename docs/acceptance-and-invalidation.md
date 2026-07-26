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

## Workflow deviations

`forge deviation record` preserves an observed difference between the locked workflow and actual
behavior. It is owner-only, append-only, and state-neutral.

```console
forge deviation record \
  --declared "Run every required verification action" \
  --actual "One required action was omitted" \
  --rationale "Preserve the discrepancy for explicit review" \
  --review-requirement "Choose rework or abandonment"
forge deviation show
```

The record is not a waiver, override, risk acceptance, or lifecycle transition. Review uses the
ordinary decision system:

```console
forge deviation review <deviation-id> \
  --option rework --option abandon \
  --outcome rework \
  --rationale "The locked workflow remains governing"
```

Only a current, non-stale `workflow-deviation-review` decision resolves the deviation. Superseding
that decision without a replacement review for the same deviation reopens it. Open deviations
appear in `forge status` and block successful closure. Explicit abandonment remains available and
preserves the deviation as part of unfinished terminal history.

## Emergency overrides

`forge override record` preserves a configured-owner emergency exception to exactly one
locked-workflow requirement or gate.

```console
forge override record \
  --requirement declared-checks \
  --rationale "An external emergency requires a documented exception" \
  --residual-risk "The affected check still has no passing result" \
  --permanence temporary \
  --review-requirement "Reassess after the emergency ends"
forge override show
```

The record is deliberately state-neutral. It cannot create or replace a claim, passing check,
evidence packet, gate approval, verification transition, or owner acceptance. Recording an
override therefore adds an auditable residual-risk blocker; it does not remove a workflow blocker.

Successful closure refuses unresolved overrides. Explicit abandonment remains available and
preserves them as unfinished terminal history. Risk acceptance is separate and is not implied by
either the override record or its owner actor.

## Exact override risk acceptance

The configured owner may accept the residual risk of one exact current emergency override:

```console
forge risk accept <override-id> \
  --rationale "Accept this bounded residual risk" \
  --residual-impact "Describe the impact if it materializes" \
  --review-condition "Optional manual review condition"
forge risk show
```

The acceptance copies the override's residual risk and binds the exact override and workflow
digests. It clears only that override's successful-closure blocker. Claims, checks, evidence,
gates, verification, step completion, and ordinary owner acceptance remain fully required.

Only one current risk acceptance may bind an override. The optional review condition is durable
text for manual governance; FORGE does not claim to monitor external conditions or automatically
expire it. If a scope amendment affects the target requirement or gate, the override and its risk
acceptance become stale together. A stale override cannot receive another acceptance; the changed
scope requires a new exception and a new explicit owner decision.
