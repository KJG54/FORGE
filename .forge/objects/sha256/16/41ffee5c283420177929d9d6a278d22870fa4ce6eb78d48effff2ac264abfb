# Local Production-v1 Residual Risk Report

Status: **bounded risk review complete; closeout validation and owner acceptance remain pending**

## Review boundary

This review covers the unpublished local candidate identified by:

- wheel SHA-256: `a9c010a92d146300de7f59852d8c7181039a3c45246f615d8f7666072c672349`;
- sdist SHA-256: `3907c86f25b3ad36c650c6888074ed1e8148451cd861ef42ddee1af26cf12b88`;
- clean source commit: `6e222985c57a9f6e74b33cf5146cb51c80e42744`; and
- verification-report revision: `438eebe8-39e4-460d-94dd-bd3fba0ef469`.

The review uses the accepted verification report and the accumulated friction report. It does not
convert predecessor results into current-candidate evidence, claim that deferred tests ran, grant
public-release authority, or constitute final Local Production-v1 acceptance.

## Residual risks and disposition

| ID | Residual risk | Current consequence | Mitigation and required disposition |
|---|---|---|---|
| RR-01 | Full clean `venv` and `pipx` installation, procedure rehearsal, example workflows, security review, and broad suite have not been repeated against the current wheel. | A packaging or broad integration regression outside the focused status path could remain undetected. | Final-acceptance blocker. Run the deferred exact-wheel matrix during closeout and bind the results to the current artifact hashes. |
| RR-02 | Native Codex and Claude Code smoke evidence belongs to superseded wheel `f047d253...`; the current wheel has not repeated the owner-observed journeys or sentinel ceremony. | Conversational usability and managed-file behavior in the two primary applications are not yet established for the current candidate. | Final-acceptance blocker. Install only wheel `a9c010a9...` in fresh smoke repositories, verify its hash, and repeat the bounded native journeys with owner-observed outcomes. |
| RR-03 | Nine symbolic-link rejection tests remain skipped because this Windows account cannot create the fixtures. | The current host cannot establish the privileged Windows symbolic-link cases. | Known platform-evidence limitation. Preserve existing non-privileged protections and repeat under an appropriately privileged Windows environment before making a broader platform claim. |
| RR-04 | Generated canonical context and the managed vendor pointer do not refresh automatically after governed transitions. During this review, persisted `current.md` still described `verify-release:ready` after authoritative status had advanced through acceptance to `review-risk`. | A cold agent that reads only the persisted context can receive stale step, input, output, and permission guidance. | Operational risk requiring explicit closeout disposition. Reconcile `forge doctor`, `forge status`, and context before work; stop on disagreement; preview the full four-file context apply and obtain owner direction before refresh. Track automatic freshness or a clearer stale marker as a future framework improvement. |
| RR-05 | Codex Desktop adapter probing did not complete on this host and Claude Code CLI was unauthenticated in the validation shell. | Managed adapter automation is unavailable in those observed environments. | Accepted local-use limitation if direct native workspace operation passes. Do not infer adapter compatibility from direct-agent smoke results. |
| RR-06 | FORGE authority and direct-agent operator labels share the same-user filesystem boundary and are attribution, not authentication. | Another process running as the same user can spoof local caller labels or alter accessible working files. | Accepted scope boundary for personal/local use only. Do not represent the candidate as suitable for hostile multi-user or hosted enforcement. |
| RR-07 | Candidate wheel and sdist files are intentionally ignored local binaries. Rebuilding changes their identity even when version text remains `1.0.0`. | Deleting or silently rebuilding the artifacts would invalidate the manifest, smoke instructions, and accepted evidence. | Preserve the exact files through extended testing, verify SHA-256 before every install, and return to the build boundary if either artifact is missing or mismatched. |
| RR-08 | Maintained performance passed only on this Windows CPython 3.14 environment. | Other supported hosts may have different latency or filesystem behavior. | Repeat the maintained review on every platform and Python version claimed at final closeout; do not describe the local p95 values as real-time guarantees. |
| RR-09 | GitHub integration and CI are external to the governed evidence packet; PR 42 is merged, but its check result has not been imported as current FORGE evidence. | Repository integration is established, while the governed record cannot independently assert the cloud check outcome. | Confirm the PR checks during closeout and record only directly observed results. A merge alone is not evidence that every check passed. |
| RR-10 | Public naming clearance, signing, tags, PyPI/TestPyPI, GitHub Releases, publication automation, support channels, and hosted operation are explicitly excluded. | The candidate is not a public release and lacks the operational controls required for one. | Preserve the unpublished local-candidate label. Handle public release through a separate owner-approved initiative and evidence set. |

## Current positive evidence

- Candidate manifest verification passed for both exact artifacts.
- The source quality gate and focused status/readiness regressions passed.
- All five maintained exact-wheel performance cases passed; active-status p95 was 817.346 ms
  against the 1500 ms budget.
- The repository is healthy, the performance blocker is resolved, and no gate was weakened to
  obtain the pass.
- PR 42 merged the accepted implementation and bounded verification records into `main`.

## Recommendation

Proceed to closeout preparation and extended owner testing, but do not grant final Local
Production-v1 acceptance yet. Closeout should first reconcile the stale generated context, execute
the deferred current-wheel matrix, collect current-wheel native Codex and Claude observations, and
confirm the GitHub checks. Any changed shipped byte requires a new clean source commit, rebuilt
artifact identities, and repeated artifact-bound validation.
