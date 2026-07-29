# M6 Release-Candidate Friction Report

Status: **complete; owner acceptance pending**

This report records friction observed while preparing and validating the M6 release candidate on
2026-07-29. It distinguishes workflow inconvenience from release risk and grants no acceptance,
closeout, or M7 publication authority.

## Findings

| ID | Observation | Effect | Resolution or follow-up |
|---|---|---|---|
| F-01 | The first local performance run shared the host with example and procedure rehearsals. | Windows startup p95 exceeded its maintained budget while the other cases passed. | Preserve the failed measurement as evidence and use isolated performance execution. The isolated rerun passed all five budgets, and CI uses dedicated performance jobs. |
| F-02 | The original macOS startup and status budgets did not represent the slowest supported CPython 3.12 hosted-runner cell. | Two PR attempts failed even though the other matrix cells passed. | With owner approval, recalibrate only macOS startup from 500 ms to 600 ms and status from 1000 ms to 1500 ms. Workloads, sampling, Linux budgets, and Windows budgets remain unchanged. The corrected PR and merged-main matrices passed. |
| F-03 | Generic secret detection classified canonical idempotency UUIDs in journals and receipt paths as API keys. | The candidate snapshot could not pass the secret review without distinguishing governed identifiers from credentials. | Add a narrow Gitleaks exception requiring the UUID shape, generic API-key rule, and exact canonical paths. Regression coverage keeps all other shapes and paths scanned. |
| F-04 | Seven symbolic-link tests require Windows privileges unavailable to the local test process. | The local complete suite reported seven skips rather than executing those platform-policy cases. | Keep the skips explicit, retain cross-platform CI, and treat privileged symbolic-link behavior as a documented host-policy limitation rather than silently claiming local coverage. |
| F-05 | Remote CI was intentionally deferred until milestone closeout. | Matrix and hosted-runner calibration issues appeared late, concentrating feedback in Increment 8. | The one-wheel PR and merged-main topology now provides exact closeout evidence. For future release work, run a representative hosted-runner calibration earlier when performance budgets or runner images change. |
| F-06 | GitHub annotated several pinned actions for deprecated Node.js 20 runtime use and forced them to Node.js 24. | Current jobs passed, but future runner enforcement could turn the warning into CI maintenance work. | Track action-version upgrades during the next authorized maintenance or M7 planning boundary. Do not treat the current annotation as a product failure. |

## Lessons

- Performance evidence is meaningful only when workload isolation and runner variability are
  visible.
- Security exceptions should bind the smallest defensible combination of rule, value shape, and
  path.
- A green matrix is evidence, not owner acceptance or publication authority.
- Deferring remote CI reduces routine increment cost but moves hosted-environment discovery into
  closeout; future milestones should make that tradeoff explicitly.

No finding above requires a new runtime feature, contract, schema, dependency, or authority change
inside M6.
