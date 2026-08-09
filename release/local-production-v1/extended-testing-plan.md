# Local Production-v1 Extended Testing Plan

Status: **replacement candidate ready for Phase 1 native-app retest; Phase 2 and final acceptance remain paused**

Use only the candidate whose wheel digest is
`a9c010a92d146300de7f59852d8c7181039a3c45246f615d8f7666072c672349`. Verify the manifest before
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

The 2026-08-08 Codex and Claude Code smoke runs exercised exact-wheel installation, safe refusal,
scope amendment, rework, artifact revision, direct-agent claim provenance, and the stop before
verification. They exposed candidate-blocking actionable-next-state and pre-initialization pack
inspection defects recorded in `friction-report.md`. The bounded vendor-file preservation and
owner-ceremony observations passed in both applications. The blockers are fixed and the replacement
exact candidate has passed automated validation. Phase 2 remains paused until those successful
observations are repeated against that replacement.

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
