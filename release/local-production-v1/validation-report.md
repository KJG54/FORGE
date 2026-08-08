# Local Production-v1 L9 Validation Report

Status: **automated candidate validation passed; native-app owner observation and final acceptance pending**

This report describes the exact unpublished candidate in `candidate-manifest.json`. It is
post-build evidence and is excluded from the sdist identity. Passing results establish readiness
for owner-observed and extended testing; they do not authorize publication or establish final
Local Production-v1 acceptance.

## Exact candidate

| Artifact | Size | SHA-256 |
|---|---:|---|
| `forge_governance-1.0.0-py3-none-any.whl` | 287,012 bytes | `9d12b62096d099d0669d8fbcedfc77ff93a31c6918667ccdf443644fb4820b18` |
| `forge_governance-1.0.0.tar.gz` | 741,536 bytes | `8b2ff9c795be463d1733bbc1a19d1dcc68b555608e5aceecf24a175933c2f66d` |

The wheel was built from the sdist on Windows 11 with CPython 3.14.4, build 1.5.1, and Hatchling
1.31.0. `tools.local_candidate verify` passed after the final build.

## Complete source validation

| Boundary | Result |
|---|---|
| Ruff | passed |
| Strict Pyright 1.1.411 | 0 errors, 0 warnings, 0 information messages |
| Version consistency | passed; schema `1.0`, 51 public models, 94 CLI commands |
| Complete pytest suite | 409 passed, 9 skipped in 505.83 seconds |
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
| startup | 65.843 ms | 750 ms |
| active status | 1184.885 ms | 1500 ms |
| 1,000-event journal replay | 47.508 ms | 200 ms |
| context generation | 768.240 ms | 1500 ms |
| archive access | 764.471 ms | 1500 ms |

The report digest is
`sha256:f4800a6ea41f0ce84f3066f4b59976c3afb5e0e455168085aa533917f21cc21a`.

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
- Native Codex and Claude Code UI smoke, conversational usability judgment, and extended real-work
  results remain pending under `extended-testing-plan.md`.

## Conclusion

No known automated candidate blocker remains. The exact candidate is ready for native-app
owner-observed smoke and extended testing. Final Local Production-v1 acceptance remains a later,
explicit owner decision based on that campaign.
