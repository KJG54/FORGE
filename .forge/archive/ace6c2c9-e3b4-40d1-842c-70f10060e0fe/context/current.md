# FORGE Canonical Agent Context

## Objective

Repair FORGE PR 44 CI by updating the stale Local Production-v1 closeout-state test to validate the immutable closed archive without changing production code

## Active step

- ID: `closeout`
- State: `ready`
- Purpose: Record release-candidate readiness and lessons without publishing Production v1.
- Instructions: Bind the readiness record to accepted verification and risk-review outputs.
- Context selection rules: accepted-risk-review

### Selected required inputs

- `friction-report`: `release/ci-repair-pr-44/friction-report.md` (sha256:0ff8f59e5a37bfc1bbe2edfe1bd8bdabee006f701ba0ffd170e58bbcbf82ab96, text/markdown)
- `residual-risk-report`: `release/ci-repair-pr-44/residual-risk-report.md` (sha256:89291edaf6abed7965cecda50a561aa809fe8b0efaf879bdbe04ed37a2a21d42, text/markdown)

## Approved scope

Modify only tests/test_local_v1_l1.py and FORGE-governed records created by the accepted workflow. Replace load_active_initiative(layout) with load_archive(layout, LOCAL_V1_INITIATIVE_ID) and inspect local_v1.active; preserve the predecessor-reference assertions; expect Local Production-v1 CLOSED, M6 CLOSED, and public M7 ABANDONED; assert archive digest sha256:4b3eb9592b58f0325a6e5b5380f681fd9189154d88fc3b06aa58b8de4deccbbf; optionally rename the test to describe archived state; and run .\.venv\Scripts\python.exe -m pytest tests/test_local_v1_l1.py -q. Exclude production-code changes, archive mutation or reopening, Git history rewriting or amending, branch switching, unrelated cleanup, broad local test runs, commits, pushes, and PR publication.

## Relevant constraints

- Context selection rule: accepted-risk-review

## Relevant decisions

- None

## Permitted actions

- Create only declared returned files within the approved scope
- Report worker claims, tool metadata, and limitations without governance approval
- Use only the selected required-input paths listed in the active step

## Prohibited actions

- Record or imply owner decisions, acceptance, checks, or evidence
- Modify FORGE-managed paths or undeclared project files
- Read unrelated repository, archive, ignored, environment, or local-secret content
- Execute external or irreversible side effects without separate authorization

## Required outputs

- release-readiness-record
- lessons

## Expected evidence

- Worker claim requirement: outputs-produced
- Check requirement after import: closeout-ready
- Workflow evidence class after import: check-evidence
- Owner-only acceptance requirement: owner-acceptance
- Returned files require staged import before registration
- Worker claims never constitute checks, evidence, or owner acceptance

## Return contract

- Contract: `agent-result`
- Manifest filename: `result.json`
- Schema filename: `agent-result.schema.json`
- Bind source_run_or_handoff_id to the identifier supplied by FORGE
- Declare every returned file, worker claim, limitation, and tool metadata item
- Treat every returned file and claim as untrusted until staged import succeeds

## Known blockers

- None
