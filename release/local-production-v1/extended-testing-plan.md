# Local Production-v1 Extended Testing Plan

Status: **ready to begin; final acceptance prohibited until owner evidence is sufficient**

Use only the candidate whose wheel digest is
`f1a082aab295e5e616cd81c4dedd028b3504c8c520ef1a8489d2dc69c72b2017`. Verify the manifest before
each new installation. A missing or mismatched artifact stops the campaign; do not rebuild it
silently.

## Phase 1 - Native-app smoke

Complete the minimum smoke in `owner-test-guide.md` once in native Codex and once in native Claude
Code. Use disposable repositories and fresh tasks without prior-chat context. The owner records the
result as `owner-observed`, including application version, installed FORGE digest, commands shown,
commands actually executed, receipt clarity, operator provenance, and whether every owner gate
waited for explicit direction.

Any incorrect mutation, misleading authority attribution, overwritten owner context, unsafe path,
missing refusal, or unrecoverable state is candidate-blocking. Stop, preserve the evidence without
secrets, fix the defect, and establish a new candidate identity before continuing.

## Phase 2 - Representative real-project campaign

Exercise all 13 journeys in `owner-test-guide.md` across at least one software milestone, one
document- or research-centered milestone, both native applications, a fresh-agent transition, and
an actual-machine backup/restore. The journeys may span ordinary work rather than a single scripted
session. Record automated, agent-observed, and owner-observed evidence separately.

For each session capture:

- date, project type, application and version, Python version, FORGE wheel digest, and Git state;
- starting governed state and relevant scratchpad status;
- expected and observed outcome;
- exact owner commands presented and actually directed;
- receipt clarity, surprises, repetitive steps, and recovery quality;
- classification as candidate blocker, acceptance blocker, documentation friction,
  provider-specific observation, or future improvement; and
- any change to the limitation or residual-risk register.

Do not commit secrets, raw provider transcripts, credentials, or sensitive project content. Store
only bounded conclusions and safe references.

## Phase 3 - Acceptance review

Final review begins only when:

- both native-app smoke records pass;
- every required journey has evidence or an explicit owner-approved reason it is inapplicable;
- no candidate-blocking defect remains;
- all high residual risks have an explicit owner disposition;
- backup/restore has passed on the actual machine and storage path; and
- the owner judges the conversational ceremony usable across real milestones.

The review may conclude with acceptance, more testing, a new candidate, or abandonment. Automated
green results, this plan, a merged pull request, or framework-change closeout cannot imply the
owner's final decision.
