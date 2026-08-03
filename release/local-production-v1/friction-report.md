# Local Production-v1 L9 Friction Report

Status: **automated findings resolved or classified; owner-observed friction pending**

| ID | Observation | Classification | Resolution or follow-up |
|---|---|---|---|
| L9-F01 | Gitleaks classified mnemonic milestone idempotency keys in exact governed journal and receipt fields as generic API keys. | Candidate-blocking false positive | Added a rule-, value-shape-, and exact-path-bound exception plus regression coverage. Arbitrary values and paths remain scanned. |
| L9-F02 | Revising a dependency correctly invalidated an active descendant run, but run inspection treated the immutable invalidated run as neither active nor terminal. This also blocked `complete --run-id` because lookup traversed the stale record first. | Candidate-blocking lifecycle defect | Derive invalidation termination from the journal, retain `cancelled` as the compatible terminal run state, and display an explicit `Invalidation` explanation without inventing a formal cancellation record. Regression and live dogfood checks pass. |
| L9-F03 | PowerShell selected `codex.ps1`, which this host's execution policy blocks, while `codex.cmd` ran successfully. | Provider-specific environment friction | FORGE's bounded probe found Codex CLI 0.139.0. Use the executable shim when manually probing on this host; do not misdiagnose the provider as absent. |
| L9-F04 | Codex CLI 0.139.0 is newer than FORGE's supported managed-adapter range. | Provider-specific compatibility observation | FORGE fails closed to manual handoff. Direct native Codex workspace use is unaffected; reconsider the adapter range only after separately testing the changed CLI contract. |
| L9-F05 | A sandboxed clean install could not reach the package index for runtime dependencies. | Validation-environment friction | Repeated the exact command with narrowly scoped host network access; both clean modes passed. This was not a wheel defect. |
| L9-F06 | Pytest's shared default Windows temp root was inaccessible in one focused invocation. | Validation-environment friction | Used the required unique explicit external `--basetemp`; the focused and complete suites passed. |
| L9-F07 | Nine symbolic-link rejection tests cannot create their fixtures without this Windows account's symbolic-link privilege. | Known host-policy limitation | Preserve explicit skips and existing non-privileged path protections. Re-run under an appropriately privileged Windows environment before making a broader platform claim. |
| L9-F08 | Native UI clarity and owner comfort cannot be derived from CLI probes or automation. | Final-acceptance blocker, not candidate blocker | Complete the minimum native-app smoke and extended owner campaign; label those results owner-observed. |

The two candidate blockers changed shipped bytes, so L9 returned to the L8 identity boundary,
rebuilt once after the complete correction set, discarded superseded install evidence, and repeated
all exact-wheel validation. No gate or scanner was weakened merely to obtain a pass.
