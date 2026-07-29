# M6 Evidence and Release-Readiness Report

Status: **M6 release-candidate evidence complete; owner closeout acceptance pending**

**Candidate merge commit:** `3f36aaa44da02525f962c021ce3c5a6fcec27b03`  
**Verified wheel SHA-256:** `800443d7c82523d0a11b3de0cb8834f5c1406ea8741f9ec6eb3f095bff4bca9f`

## Readiness conclusion

The eight M6 increments satisfy the authorized release-candidate hardening boundary. The candidate
is ready for M6 milestone closeout: its compatibility baseline, distribution installation paths,
examples, documentation, supply-chain review, performance budgets, governed dogfooding, and
complete closeout matrix are evidenced.

This is not a Production v1 publication decision. M6 creates no `1.0.0` tag, signature, package
upload, public support commitment, or M7 authority.

## Increment inventory

| Increment | Delivered boundary |
|---|---|
| 1 | Froze the pre-v1 compatibility inventory, additive-schema expectations, legacy/current journals, migration path, and future-version refusal. |
| 2 | Defined and implemented the 18-cell Windows, macOS, and Linux installation matrix for CPython 3.12–3.14 through virtual environments and `pipx`. |
| 3 | Added static software and research examples plus exact-installed-wheel workflow rehearsal. |
| 4 | Completed task-oriented documentation routes for users, pack authors, adapter contributors, architecture and security reviewers, troubleshooting, and recovery. |
| 5 | Added reproducible dependency, license, vulnerability, Git-history secret, and candidate-snapshot review. |
| 6 | Added maintained p95 budgets for startup, status, journal replay, context generation, and archive access. |
| 7 | Initialized FORGE as a governed FORGE project with a declarative, Python-free, capability-free framework-change workflow. |
| 8 | Built the one-wheel local and remote closeout topology, operational rehearsal, friction review, residual-risk classification, and readiness evidence. |

## Validation evidence

| Boundary | Result |
|---|---|
| Complete local suite | 348 passed; 7 Windows symbolic-link privilege skips |
| Local quality | Ruff passed; strict Pyright reported 0 errors and 0 warnings |
| Build | Source distribution and source-distribution-to-wheel build passed |
| Exact-wheel installation | Windows CPython 3.14 virtual-environment and `pipx` paths passed locally; all 18 remote installation cells passed |
| Example workflows | Software and research examples passed locally and on each supported remote operating system at CPython 3.12 |
| Procedures | Backup, migration, missing-snapshot recovery, restore, abandonment, archive access, and successor lineage passed |
| Performance | All five maintained budgets passed locally in isolation and across the corrected nine-cell remote matrix |
| Security | 26 dependency/license records approved; zero known runtime vulnerabilities; Git history and 409-file snapshot scans passed |
| Pull request | Commit `2f95708d7515560cf2186fcfbd6f3f789badeb75` passed all 38 jobs in GitHub Actions run `30482342649` |
| Merged `main` | Commit `3f36aaa44da02525f962c021ce3c5a6fcec27b03` passed all 38 jobs in GitHub Actions run `30483157200` |

The exact verification report is preserved as revision
`0384c2f4-2222-44d9-9c61-f31f5cba49f4` with digest
`sha256:697278804ea38cb206128a389b753ec451e5bfcd1f26107f5b08bee6b8c826ac`.
Owner acceptance `2e488573-9f37-4893-a8c9-55a27662a97e` accepted that exact verification evidence.

## Exit-criterion mapping

| M6 exit criterion | Evidence and disposition |
|---|---|
| Fresh users can complete both example workflows from built distributions | Both examples passed from the exact wheel locally and in the Windows, macOS, and Linux CPython 3.12 release-scenario cells. |
| Upgrade, backup, archive, abandonment, successor, and recovery procedures are rehearsed | The maintained shell-free procedure harness passed every declared procedure; legacy migration and both successful and non-success terminal paths are covered. |
| No critical governance, integrity, import, path, or secret defect remains | Complete tests, adversarial coverage inherited from M4, supply-chain review, full-history and snapshot secret scans, and the classified residual-risk review found no unresolved critical M6 defect. |
| Public compatibility commitments are documented | The compatibility policy binds the accepted pre-v1 schemas, journal formats, migration edge, additive defaults, and future-version refusal while making no promise for arbitrary intermediate commits. |
| The owner resolves every release-blocking risk | The risk register identifies no unresolved M6-blocking defect. Owner acceptance `73026cc8-0d4b-44e0-9656-3957e8f6d8a8` accepts the controlled M6 risks and preserves public publication as a separate hard gate. |

## Accepted friction and residual risk

The friction report revision `f8819d16-293a-447e-b383-905047755a4c` records host-contention
sensitivity, macOS hosted-runner calibration, UUID secret-scan false positives, Windows
symbolic-link privileges, deferred-remote-CI timing, and GitHub Actions runtime annotations.

The residual-risk report revision `9d4fd366-7e71-4d37-8945-d8db0737be4a` classifies six risks.
Performance variability, privilege-dependent test coverage, the narrow UUID exception,
point-in-time security evidence, and action-runtime maintenance are controlled and non-blocking for
M6. Public release remains blocked until separately scoped M7 work.

## Limitations and stop point

- All validation and security evidence is point-in-time.
- Hosted runners, action runtimes, dependencies, and vulnerability data can change.
- Seven local Windows symbolic-link tests require privileges unavailable to the observed process.
- M6 acceptance does not establish the safety or readiness of future changed candidate bytes.

**Stop:** Close M6 only after exact owner acceptance of this readiness evidence and its lessons.
Do not tag, sign, upload, advertise Production v1, or begin M7 implementation under this record.
