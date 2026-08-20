# Phase 1 authority and specification lifecycle friction report

## Purpose and boundary

This report records friction observed while governing, validating, and preparing publication of
the Phase 1 authority and specification lifecycle change. It does not expand this initiative's
implementation scope or mark any item resolved. Product changes belong in a separately authorized
successor review.

## Observed friction

### FR-1 — Successful mutation commands sometimes returned no receipt text

Several `forge complete`, `forge check record`, `forge evidence add`, and `forge verify` invocations
completed successfully and changed canonical state but returned an empty command result in the
calling session. The operator had to run `forge status`, `forge next`, `forge history`, or a list
command to determine whether the mutation occurred and to recover record identifiers.

This is high-impact agent and human friction. A mutation command must provide an unambiguous
receipt or a recoverable command identifier. Canonical state remained healthy in this run, but
missing immediate output makes safe retry behavior harder to reason about.

### FR-2 — Artifact listing exposes logical IDs where evidence needs revision IDs

`forge artifact list` displays each logical artifact UUID, role, revision number, and path.
`forge evidence add --artifact-revision`, however, requires the immutable revision UUID. The
current list output does not expose that required UUID. The first evidence attempt therefore used
logical IDs and made no state change; resolving the correct identifiers required inspecting each
artifact or parsing governed revision records.

The legal-next guidance said evidence was needed but did not show a directly executable command
or the current revision UUIDs. This is avoidable agent friction on a common integrity path.

### FR-3 — Required workflow reports were absent from the accepted implementation surface

The locked workflow required `framework-changes`, `verification-report`, `friction-report`, and
`residual-risk-report` artifact roles. The reviewed change-scope inventory listed the substantive
implementation files but did not reserve project targets for all required workflow reports. This
created repeated additional-target review boundaries after implementation had already been
accepted.

Workflow-generated reporting targets should be declared during scope planning or kept in a
clearly governed reporting namespace whose creation is already part of the workflow contract.

### FR-4 — Hidden staging paths were not accessible through the desktop review surface

The verification report was staged under `.forge/local/`, but the owner could not open the link
from the desktop application. A byte-identical copy outside the repository was still not visible
through the rendered link, and the owner had to ask for the filesystem path explicitly.

Owner-visible artifact review needs a reliable preview surface that does not depend on hidden
directories or application-specific local-link handling.

### FR-5 — Long Windows test paths caused a false product failure

The first full suite used a writable but long Codex visualization path as `--basetemp`. One test
that creates a Git repository then failed with `Filename too long` while staging a deeply nested
archive artifact. The same test and the full suite passed under a shorter system temp path.

Test guidance should recommend a short writable Windows temp root, not merely any writable root.

### FR-6 — All local symlink-security tests remain silently unexercised

Nine tests skipped because the Windows account lacks symlink-creation privilege (`WinError 1314`).
Pytest reported the skips at the end, but FORGE itself does not elevate this into a security
coverage warning or provide a strict mode for owner validation.

### FR-7 — Pre-publication governed-file warnings are accurate but operationally broad

`forge doctor` remained healthy while warning that more than one hundred current governed files
were not tracked by Git. This is expected during active work, but the warning is long and does not
separate active-state files that must be committed from local-only files or provide a concise
publication readiness summary.

### FR-8 — The owner reports broader malfunction beyond this phase

After reviewing the Phase 1 report, the owner stated that FORGE is not working properly and needs
extensive review. This initiative does not infer a cause or alter runtime behavior. The statement
is preserved as a high-priority input for a successor audit covering command behavior, lifecycle
ceremony, agent usability, integrity, performance, and publication ergonomics.

## Recommended successor handling

The next review should begin from observed command transcripts and canonical journal evidence,
then reproduce each issue with controlled model, effort, operating-system, and repository state.
It should distinguish product defects from shell, desktop-link, sandbox, and Windows-environment
effects. Findings should enter the living friction register only after classification, without
requiring one initiative per observation.

No item in this report is marked fixed by Phase 1.
