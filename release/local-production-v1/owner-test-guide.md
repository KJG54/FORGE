# Local Production-v1 Owner Test Guide

Use this guide only with the exact wheel named and hashed in `candidate-manifest.json`. L9 records
candidate readiness for extended use; it does not manufacture final owner acceptance.

Automated L9 rehearsals cover every lifecycle mechanism below, but they do not establish that a
native application presented the interaction clearly or that the owner found it usable. Record the
Codex and Claude Code native-app smoke separately before beginning the longer real-project campaign.

## Before testing

1. Preserve `dist/local-production-v1/` in access-controlled local storage.
2. Run `python -m tools.local_candidate verify`; do not rebuild after a mismatch.
3. Create a clean virtual environment and install the recorded wheel by exact path.
4. Record Windows version, Python version, Codex/Claude application and CLI versions, installed
   dependency inventory, FORGE wheel digest, project type, and whether each observation was
   automated, agent-observed, or owner-observed.
5. Use disposable projects for destructive rehearsals and a controlled copy for restore testing.

For each journey, capture the starting state, commands presented, commands actually executed,
receipt or error, expected outcome, observed outcome, friction, surprises, and any limitation or
risk change. Never place secrets or raw sensitive captures in Git or governed records.

## Required journeys

1. **New empty software project:** begin in an ordinary empty Git repository; use the pre-init
   protocol and interview, review exact effects, initialize, create a `software-basic` initiative,
   and reach the first legal work action.
2. **Existing documentation project:** initialize without disturbing existing files or ignore
   rules; confirm document-first bootstrap and bounded context discovery.
3. **Research project:** select `research-basic`, review research-specific framing, and complete at
   least one representative step without software-only assumptions.
4. **Warm resume after a day or more:** leave an active initiative without formal pause, add a
   bounded local scratchpad note, return in a fresh task, and use `forge recap` to reconcile it with
   canonical state.
5. **Formal pause/resume with working drift:** pause cleanly, change a registered working file while
   paused, inspect the drift report and long-gap summary, then resume without treating the summary
   as acceptance.
6. **Rejection after claim:** record a claim and supporting mechanics, reject the result through the
   appropriate owner path, revise the artifact, and prove old support becomes stale before rework.
7. **Mid-milestone plan revision:** classify and record an implementation-plan change that does not
   change the Definition of Done (DoD); confirm it remains distinct from governed scope amendment.
8. **DoD scope amendment:** present the complete replacement scope and consequences, cancel any
   affected active run, execute owner-authorized `forge scope amend`, and re-establish invalidated
   support.
9. **Interrupted recovery:** on a disposable copy, exercise at least one supported interruption
   case with a stable idempotency key; prove ambiguous damage fails closed.
10. **Abandonment:** stop an incomplete initiative with reason, unfinished work, and unresolved
    risks; verify the terminal archive says non-success and cannot reopen.
11. **Closure and archive:** complete and accept every required step, close successfully, inspect
    archive status/history, and prove supported mutation is refused.
12. **New-agent successor without chat:** start a fresh Codex or Claude task with no prior-chat
    context, generate `forge successor brief --archive <id>`, label fresh Git observations, validate
    exact reusable revisions, and create a successor that imports no progress or acceptance.
13. **Backup and restore on the actual machine:** back up the complete repository including hidden
    `.forge/` content, restore to a controlled path, run `forge doctor`, inspect active or archived
    state, and compare expected identities before relying on the copy.

Exercise both native Codex and Claude Code applications across the campaign. Where automation
cannot independently observe a native UI action or human judgment, label the result
`owner-observed`; do not translate observation into programmatic proof.

## Minimum native-app smoke

In one disposable project per application, ask a fresh native Codex and Claude Code task to read
the installed FORGE protocol, inspect repository state, and identify the next legal action. Then
exercise one routine agent-operated mutation and one consequential owner gate. Record whether:

- the application preserved owner-authored `AGENTS.md` or `CLAUDE.md` bytes;
- the agent quoted `Recorded` and `Means` without presenting its own `Read` or `Next` as fact;
- the routine mutation named honest `direct-codex` or `direct-claude` provenance;
- the owner gate showed the exact command and consequence before execution; and
- no owner-only action occurred until the owner explicitly directed it.

CLI version probes and adapter diagnostics are environment evidence only. They cannot substitute
for these native UI observations.

## Friction review

After every journey, ask:

- Did the agent know the next legal action without relying on prior chat?
- Were command effects, authority, operator identity, and irreversible consequences clear before
  execution?
- Did the receipt explain what changed, what it meant, and what remained blocked?
- Was the Minimal/Standard/Guided/Mentored explanation useful without changing governance?
- Could the owner distinguish working notes, derived views, governed facts, and fresh repository
  observations?
- Did rejection, revision, pause, recovery, abandonment, closure, and succession fail safely?
- What step felt repetitive, surprising, ambiguous, or too easy to approve accidentally?
- Does the finding change a known limitation, residual risk, protocol rule, or final acceptance
  criterion?

Classify findings as candidate-blocking defects, final-acceptance blockers, documentation friction,
provider-specific observations, or future improvements. Fixing a candidate-blocking defect changes
the artifact bytes and requires a new L8 candidate identity before the campaign continues.
