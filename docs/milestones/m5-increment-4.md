# M5 Increment 4 — Minimal and Mentored Explanation Profiles

## Authorized scope

- enable the existing Minimal and Mentored profile values at initiative creation;
- provide Minimal, Standard, Guided, and Mentored inline explanations in both bundled workflows;
- advance `software-basic` and `research-basic` to exact digest-bound version `0.4.0`;
- lock the selected profile and explanation text through existing initiative and workflow records;
- reject an unavailable selected profile before writing initiative state;
- preserve Standard/Guided compatibility for older two-profile pack locks; and
- prove identical governance and initial state across all four profiles and both domains.

## Explicit exclusions

Profile switching after initiative creation, explanation resource files, markup or template
rendering, external content lookup, new permissions, relaxed gates, automated checking, evidence,
verification, acceptance, shared pack-conformance infrastructure, long-gap resumption, filesystem
discovery, and later M5 work are not implemented.

## Authority and trust

Explanation text is presentation-only trusted pack data. The configured owner authorizes the exact
pack and workflow bytes when creating the initiative. Selecting Minimal, Standard, Guided, or
Mentored grants no actor authority and changes no workflow rule.

Mentored explanations may teach why a boundary matters, but they cannot perform work, establish a
claim, satisfy a check, create evidence, verify a step, accept an outcome, or make an owner
decision. Minimal explanations omit detail, not governance.

## Persistence, compatibility, and failure semantics

The existing `Initiative.explanation_profile` records the selection, and the exact locked
`WorkflowDefinition.explanation_content` provides the text. Both remain covered by existing
record, pack-digest, restart, recovery, and archive validation.

Older two-profile packs remain valid for Standard and Guided initiatives. A request for a profile
missing from the selected workflow fails before pack resources, initiative records, workflow
locks, trust decisions, or journal events are written. No persisted schema changes, migration, or
new schema export is required; the public schema count remains 51.

## Design evidence

[ADR-0047](../adr/ADR-0047-four-profile-presentation-only-education.md) records the four-profile
semantics, unchanged-governance rule, pack-version decision, and legacy compatibility boundary.

## Validation evidence

- focused Increment 4 profile, CLI, digest, equivalence, and compatibility coverage: 7 passed;
- profile-adjacent CLI, pack, trust, and initialization coverage: 37 passed with 1 expected Windows
  privilege-based symlink skip;
- all M5 Increment 1–4 coverage: 19 passed;
- complete local suite, partitioned to keep progress observable: 296 passed and 6 expected Windows
  privilege-based symlink skips;
- Ruff: clean;
- strict Pyright: 0 errors and 0 warnings;
- `git diff --check`: clean;
- source and wheel build: clean with Hatchling 1.31.0;
- clean Python 3.14 installed-wheel smoke: both bundled `0.4.0` packs, all four profiles, eight
  initiatives, exact locked explanation reload, 51-schema export, and mentored `status` all passed;
- remote CI is intentionally not inspected or claimed until M5 closeout.

## Stop point

Stop after all four profiles are selectable for both bundled packs with identical governance. Do
not implement profile switching, shared conformance closeout, resumption summaries, discovery, or
later M5 behavior.
