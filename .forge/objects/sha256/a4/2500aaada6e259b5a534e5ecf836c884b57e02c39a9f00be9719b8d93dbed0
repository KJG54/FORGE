# Phase 1 authority and specification lifecycle lessons

## What worked

### Typed authority removed a real design ambiguity

Separating normative design, persisted runtime/history, active locked rules, reference content,
and derived advisory views resolves the three conflicting lists previously called one source of
truth. ADR-0004's persisted ordering remains useful without allowing documents to overrule bytes
or initiative-local decisions to silently amend global architecture.

### Historical preservation and current guidance can coexist

The recovered Production-v1 master specification could be preserved byte-for-byte while an
adjacent index and one current governing specification clearly mark its historical status. No
warning banner or correction had to be inserted into historical bytes.

### Machine-readable effective status is safer than rewriting ADRs

The ADR catalog preserves recorded status while expressing current effective status and reciprocal
supersession separately. The semantic checker can now detect drift without changing immutable ADR
bodies.

### Exact revisions, checks, evidence, verification, and acceptance remained distinct

The workflow caught wrong identifier usage, stale revisions after corrections, and the difference
between local validation and remote CI. The core invariant remained operational throughout:

`worker claim -> check -> evidence -> FORGE verification -> owner acceptance`

## What should improve

### Workflow outputs must be planned at scope time

The substantive implementation surface did not reserve targets for every report required by the
locked workflow. Future scope templates should enumerate implementation, verification, risk, and
closeout artifact roles and their expected project paths before owner acceptance.

### Every successful mutation needs a visible durable receipt

Several successful commands returned no immediate output in the calling session. Although stable
idempotency, state, history, and list commands enabled recovery, agents should never need to infer
whether a governed mutation occurred. Receipt delivery and command recovery require focused
testing across direct terminals, desktop tool sessions, and time-bound process wrappers.

### Legal-next output should include the identifiers its command requires

Evidence registration requires immutable artifact revision UUIDs, while the default artifact list
shows logical artifact UUIDs. `forge next` should provide executable commands or directly expose
the current revision, claim, and check-result IDs needed by the legal action.

### Owner review surfaces must be reliably visible

Hidden `.forge/local` files and Codex visualization links were not reliably openable by the owner.
FORGE should offer a first-class preview command or copy-to-review behavior that preserves digest
identity while presenting a human-readable artifact in the active client.

### Windows validation needs explicit environment guidance

A long writable test path caused a false failure, while nine symlink tests skipped because the
account lacks privilege. Windows guidance should recommend a short temp root, explain Developer
Mode, and support a strict security-test requirement.

### Routine ceremony should remain batchable

Once exact scope and risk boundaries are accepted, routine claim/check/evidence transitions can be
batched without weakening genuine owner gates. FORGE should optimize for high-signal owner choices,
not repeated approval prompts whose answers are mechanically predetermined by an already accepted
scope.

## Successor recommendation

The next initiative should be an extensive read-only-first FORGE operational audit driven by the
owner's report that FORGE is not working properly. It should reproduce receipt loss, identifier
friction, lifecycle latency, preview failures, approval ceremony, Windows behavior, and any other
malfunctions against exact command transcripts. It should also revisit the existing improvement
roadmap and friction register without assuming that Phase 1 resolved anything outside authority
documentation.

Use a controlled model and effort level for comparative dogfooding, preserve observed environment
and repository state, and distinguish product defects from desktop, sandbox, shell, Git, and
operating-system effects before proposing repairs.

## Closure lesson

Phase 1 accomplished its narrow purpose: one current governing entry point, honest historical
specification preservation, typed authority, effective ADR metadata, and semantic drift checks.
Its most important operational lesson is that FORGE's integrity model is stronger than its current
interaction ergonomics. The successor should improve that connective tissue without weakening the
authority boundaries that worked here.
