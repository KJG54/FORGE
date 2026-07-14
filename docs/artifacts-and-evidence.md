# Artifacts, Claims, Checks, and Evidence

M1 Increment 4 implements the record-backed verification portion of the approved vertical slice.
It keeps worker assertions, structured evaluations, durable support, and owner decisions separate.
Owner acceptance and stale-record propagation begin in Increment 5 and are not implemented here.

## Immutable revisions and preservation

`forge artifact add` creates a logical artifact and revision 1. `forge artifact revise` creates a
new record without rewriting any prior revision. Paths are normalized repository-relative paths;
traversal, symbolic links, FORGE-managed paths, configured secret locations, and recognizable
high-confidence credential patterns are refused.

Increment 4 conservatively preserves every registered revision under:

```text
.forge/objects/sha256/<first-two>/<remaining-digest>
```

The stored path, byte count, and SHA-256 digest are verified on restart. Identical bytes are
deduplicated. Registration fails with guidance when content exceeds
`artifacts.max_preserved_object_bytes`; large-artifact backends remain post-v1.

The working project file may change normally. `forge status` reports that as a healthy but blocked
drift condition and directs the participant to register an explicit revision. A missing or changed
governed record or preserved object is instead an `integrity_error`.

```console
forge artifact add objective.md \
  --role objective-and-constraints \
  --title "Objective and constraints" \
  --media-type text/markdown
forge artifact list
forge artifact show <artifact-id>
forge artifact revise <artifact-id> objective.md
```

Artifact roles must be declared by the locked workflow. Artifact views include immutable revision
IDs, digests, preservation paths, direct claim/check/evidence dependency references, and working
copy status. Increment 4 records those references but intentionally does not propagate stale record
IDs; that invalidation behavior belongs to Increment 5.

## Claim, check, evidence, verify

`forge complete` requires every declared output role for the current step and verifies that each
working file still matches its registered revision. It records a claim bound to exact revision IDs
and moves the step only from `in_progress` to `awaiting_verification`.

`forge check record` stores a manual structured check. It records the declared check identity and
version, exact current target revisions, invocation description, timestamps, exit status when
applicable, normalized outcome, limitations, actor, and a deterministic result digest. It never
executes a capability.

`forge evidence add` records a digest-bound packet of artifact-revision, check-result, and claim
references plus purpose and limitations. Evidence documents support; it does not automatically
establish truth.

`forge verify` is a FORGE CLI service transition. It advances a step to `awaiting_acceptance` only
when it derives all of the following from governed records:

- a current claim covering the exact required output revisions;
- a current passing result for every declared check;
- an evidence packet binding those revisions, check results, and a current claim.

```console
forge complete discover --assertion "Declared outputs were produced"
forge check record discover outputs-present \
  --invocation "manual file review" --outcome passed --exit-status 0
forge evidence add discover \
  --purpose "Support the output-presence check" \
  --artifact-revision <revision-id> \
  --check-result <check-result-id> \
  --claim <claim-id> \
  --limitation "Presence does not establish semantic quality"
forge verify discover
```

Every governed record is written before its event is committed. If failure occurs before journal
commit, newly created record files are removed. Once the event is committed, the journal remains
authoritative and snapshot disagreement is reported under the existing M1 transaction model. M2
still owns cross-process locking, idempotent retry, interruption recovery, and hash chaining.

## Explicit boundary

Increment 4 does not provide an acceptance command and cannot satisfy
`owner-acceptance-recorded`. It also does not mark dependent checks, evidence, gates, or acceptance
records stale after a revision. Those owner-authority and invalidation semantics are the next M1
increment and must not be inferred from a passing check or successful process exit.
