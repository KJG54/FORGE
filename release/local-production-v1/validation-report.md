# Local Production-v1 L9 Validation Report

Status: **automated candidate validation passed; native-app smoke exposed candidate blockers;
final acceptance prohibited**

This report describes the exact unpublished candidate in `candidate-manifest.json`. It is
post-build evidence and is excluded from the sdist identity. Passing results establish readiness
for owner-observed and extended testing; they do not authorize publication or establish final
Local Production-v1 acceptance.

## Exact candidate

| Artifact | Size | SHA-256 |
|---|---:|---|
| `forge_governance-1.0.0-py3-none-any.whl` | 288,251 bytes | `f047d25365534beafba29cf01ed6f7e82a9a72a8a90de9f85ca8172b3f8b682a` |
| `forge_governance-1.0.0.tar.gz` | 742,834 bytes | `882ddeecee77750dc2aec931d2e52df2e414f6449bc7bd68866ad4782786f9bc` |

The wheel was built from the sdist on Windows 11 with CPython 3.14.4, build 1.5.1, and Hatchling
1.31.0. `tools.local_candidate verify` passed after the final build.

## Complete source validation

| Boundary | Result |
|---|---|
| Ruff | passed |
| Strict Pyright 1.1.411 | 0 errors, 0 warnings, 0 information messages |
| Version consistency | passed; schema `1.0`, 51 public models, 94 CLI commands |
| Complete pytest suite | 409 passed, 9 skipped in 526.02 seconds |
| Candidate manifest, names, sizes, metadata, and hashes | passed |
| Distribution inventory | passed; 617 sdist entries and no `.agents`, `.claude`, `.codex`, or `.forge/local` content |

All nine skips require Windows symbolic-link creation privilege unavailable to this user account.
They cover explicit symbolic-path rejection cases; the skip reason is visible for every case.

## Exact-wheel installation

Both clean installation modes used the wheel digest above on Windows with CPython 3.14.4.

| Mode | Result | Installed contract |
|---|---|---|
| fresh `venv` | passed | `forge==1.0.0`, both packs valid, healthy repository, 51 schemas |
| isolated `pipx` 1.16.4 | passed | `forge==1.0.0`, both packs valid, healthy repository, 51 schemas |

The resolved runtime inventory was annotated-doc 0.0.5, annotated-types 0.8.0, colorama 0.4.6,
markdown-it-py 4.2.0, mdurl 0.1.2, pydantic 2.13.4, pydantic-core 2.46.4, Pygments 2.20.0,
PyYAML 6.0.3, rich 15.0.0, shellingham 1.5.4, typer 0.27.1, typing-extensions 4.16.0, and
typing-inspection 0.4.2. Dependency resolution remains point-in-time evidence.

## Lifecycle and pack journeys

| Journey | Evidence type | Result |
|---|---|---|
| New empty software repository and installation bootstrap | exact-wheel smoke plus complete suite | passed |
| Existing document discovery and non-destructive initialization | complete suite | passed |
| Research workflow | exact installed executable; 7 steps and healthy archive | passed |
| Software workflow | exact installed executable; 6 steps and healthy archive | passed |
| Warm recap and scratchpad reconciliation | complete suite | passed |
| Formal pause/resume and drift | complete suite | passed |
| Claim rejection, revision, staleness, and rework | complete suite plus live dogfood correction | passed |
| Mid-plan revision classification | protocol/conformance suite | passed |
| Definition-of-Done scope amendment | complete suite | passed |
| Interruption and snapshot recovery | procedure rehearsal plus complete suite | passed |
| Abandonment and immutable non-success archive | procedure rehearsal plus complete suite | passed |
| Successful closure and archive access | both example workflows plus procedure rehearsal | passed |
| Fresh-agent successor derivation | procedure rehearsal plus successor suite | passed |
| Complete backup and restore | procedure rehearsal | passed |

The maintained procedure report passed backup, restore, migration, snapshot recovery,
abandonment, archive access, and successor scenarios. Its digest is
`sha256:5562c1589ac7720a36aae8906762f6d53763c271152e3d57d52d06d1d5b93c66`.

## Performance

All cases passed the maintained Windows budgets in an isolated run against the exact installed
wheel.

| Case | p95 | Budget |
|---|---:|---:|
| startup | 68.200 ms | 750 ms |
| active status | 1242.035 ms | 1500 ms |
| 1,000-event journal replay | 46.227 ms | 200 ms |
| context generation | 818.329 ms | 1500 ms |
| archive access | 764.207 ms | 1500 ms |

The report digest is
`sha256:e8ac8d6b12487cfd9481fcc888f92d357945c13ad83f5315ce3544d9dbd82936`.

## Security and supply chain

The final review passed all 26 installed dependency-license records, audited 14 runtime packages
with pip-audit 2.10.1 and found no known vulnerabilities, passed Gitleaks 8.30.1 against complete
Git history, and passed the 622-file candidate snapshot. One exact historical synthetic exception
remains. The policy digest is
`sha256:1002399372c68656663d5905bf68596d6706b5dde24df23450c807ad4f4fd6ec`;
the final report digest is
`sha256:4dba754a30e0b6096cb489d093aa628defc53cde3748f0ab75de7d3db7371631`.

## Provider diagnostics and observation boundary

- Codex Desktop exposes its bundled executable through the Windows application package. FORGE's
  bounded version probe did not complete on this host, so diagnostics failed closed to the manual
  adapter. Direct native Codex workspace use remains the primary surface and does not depend on
  managed adapter execution.
- Claude Code CLI 2.1.207 passed availability and compatibility diagnostics but was not
  authenticated in the validation shell, so diagnostics also selected the manual adapter.
- This Codex Desktop task is agent-observed evidence that direct workspace work can inspect and
  mutate the repository while preserving FORGE receipts and owner gates. It is not labeled
  owner-observed without the owner's explicit confirmation.
- Fresh native Codex and Claude Code smoke repositories both used the exact recorded wheel, remained
  healthy, stopped at `discover:awaiting_verification`, and recorded claims with `direct-codex` and
  `direct-claude` operator provenance respectively.
- Refusals for a duplicate governed path, a missing required artifact role, and an active-run scope
  amendment prerequisite appended no governed events and preserved healthy state.
- Native smoke exposed candidate-blocking gaps in actionable next-state reporting and the absence
  of supported pre-initialization pack inspection. Details and lower-severity findings are in
  `friction-report.md`.
- Both providers added owner-supplied sentinels outside their managed vendor blocks, captured the
  exact unmanaged bytes, stopped when their first consequence presentations were incomplete or
  internally inconsistent, corrected those presentations, and executed once after explicit owner
  authorization. Both sentinels and all unmanaged bytes survived unchanged. Independent history
  checks confirmed 10 of 10 events and the original sequence-10 journal head hash in each
  repository. The bounded vendor-file preservation and owner-ceremony test therefore passed in
  both native applications. Extended real-work testing remains paused under
  `extended-testing-plan.md` because of the separate candidate blockers.

## Conclusion

The automated evidence remains valid for the exact candidate, but the candidate is not ready for
extended testing or final acceptance. Native smoke exposed two candidate blockers that require a
new implementation and exact candidate identity. The successful vendor-file and owner-ceremony
observations must then be repeated against the replacement candidate.
