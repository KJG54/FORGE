# Local Production-v1 L9 Friction Report

Status: **automated findings resolved or classified; owner-observed cloud findings recorded;
native-app owner-observed friction pending**

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

## Bootstrap and cloud-workspace findings (2026-08-05 to 2026-08-06, owner-observed)

These findings come from owner-observed cloud workspace sessions (claude.ai/code on the FORGE
repository) during extended testing. Cloud observations supplement but do not satisfy the
native-app smoke boundary in L9-F08.

| ID | Observation | Classification | Resolution or follow-up |
|---|---|---|---|
| B-F01 | Cold workspace agents never discovered the agent protocol. In two owner-observed runs the agent read the README, installed the CLI, and proceeded to objective/scope questions — one run executed `forge init` unprompted before any interview — because no reachable surface named `forge agent protocol` before the first command. | Candidate-blocking bootstrap defect | Added protocol signposts to `forge --help`, both `forge init` receipt paths, and the README, and applied managed `CLAUDE.md`/`AGENTS.md` vendor context to this repository so sessions load the pointer at start. An owner-observed cloud retest on the fixed branch produced protocol-first contact, a document-first interview, coverage playback, displayed owner gates, and verbatim canonical receipts. Output changes retire the L9 candidate identity; rebuild and exact-wheel revalidation are scheduled. |
| B-F02 | A governed project built in an ephemeral cloud container with no Git remote (repository, journal, and initiative) was destroyed when the container was reclaimed. | Environment friction and documentation gap | The quickstart now states the durable-home rule: a local folder, a private remote for cloud sessions, or an explicitly declared throwaway. Protocol 1.2.0 now requires first contact to establish the project's durable home before bootstrap; candidate rebuild and exact-wheel revalidation remain pending. |
| B-F03 | The cloud execution container pre-seeded a remote-tracking ref for the session's assigned branch that did not exist on GitHub, so the session misreported which branch it had built from. | Cloud-environment hazard, not a FORGE defect | Ground truth is `git ls-remote --heads origin`; the workaround is documented in the session handoff that discovered it. Affects the validity of cloud test evidence; verify the actual checked-out commit before trusting any cloud run as evidence. |
| B-F04 | A phone-driven remote owner cannot execute owner-shell ceremony commands; owner gates were executed by the agent on explicit chat direction instead. | Ceremony observation within the accepted model | The protocol already permits explicit owner direction. The accepted remote mode is display-first, explicit direction in chat, and honest `direct-claude`/`direct-codex` operator provenance on agent-authored records. Not authentication, and not claimed as such. |
| B-F05 | The cloud container's default Python (3.11) is below FORGE's >=3.12 floor, and its venvs ship without pip. | Provider-environment friction | Agents detected the floor and built a 3.13 venv (using `uv pip` where pip was absent). Documented; no FORGE change required. |
