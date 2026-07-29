# M6 Release-Candidate Residual-Risk Report

Status: **classified; owner disposition pending**

This register classifies the risks remaining after complete local, pull-request, and merged-main
validation. Severity reflects the M6 release-candidate boundary, not a future public production
release. Evidence is point-in-time and cannot eliminate future dependency, service, or runner
change.

## Risk register

| ID | Residual risk | Severity | M6 blocking? | Existing control | Requested owner disposition |
|---|---|---:|---|---|---|
| R-01 | Hosted-runner contention or image changes can move performance p95 values. | Medium | No | Dedicated matrix jobs, platform-specific maintained budgets, fixed workloads, warmups, and 20-sample p95 measurement. | Accept for M6; investigate regressions and recalibrate only with measured evidence. |
| R-02 | Windows symbolic-link behavior is not exercised by seven tests when the process lacks the required privilege. | Low | No | Explicit skips, path and symlink refusal tests that do not require privilege, and cross-platform complete-test jobs. | Accept for M6; retain visible skips and periodically exercise a privileged Windows environment when available. |
| R-03 | The narrow Gitleaks UUID exception could conceal a credential only if it also has the canonical UUID shape and exact governed receipt or journal path. | Low | No | Rule-, shape-, and path-bound exception; focused regression tests; full-history and bounded-snapshot scans. | Accept for M6; review the exception whenever journal or receipt formats change. |
| R-04 | Dependency, vulnerability, license, and secret results can become stale after the reviewed versions or repository bytes change. | Medium | No | Exact environment inventory, 26 approved license records, zero known runtime vulnerabilities, and commit-bound CI evidence. | Accept for M6; repeat the security review for any changed release candidate and immediately before public publication. |
| R-05 | GitHub Actions currently forces Node.js 24 for action versions that declare deprecated Node.js 20. | Medium | No | Both the corrected PR and merged-main 38-job matrices passed under the current hosted behavior. | Accept for M6; upgrade to Node.js 24-native action releases in the next authorized maintenance boundary. |
| R-06 | M6 produces a verified candidate but no `1.0.0` tag, signature, package upload, or post-v1 support commitment. | High for publication; none for M6 | No for M6; yes for public release | Scope, workflow, and reports explicitly prohibit publication and M7 authority. | Close M6 only as a release-candidate milestone; require separately scoped and owner-authorized M7 work before any public release. |

## Blocking-risk disposition

No critical governance, integrity, import, path, secret, compatibility, or installation defect
remains in the verified M6 candidate. There is therefore no unresolved release-blocking risk within
the authorized M6 boundary.

R-06 remains an intentional hard boundary: the candidate must not be tagged, signed, uploaded, or
represented as Production v1 until a separate M7 scope and owner decision establish those actions.
Accepting this report records informed residual-risk disposition only; it does not perform or
authorize publication.
