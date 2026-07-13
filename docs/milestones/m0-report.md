# Milestone 0 Completion Claim and Evidence

- **Milestone:** M0 — Constitution and Repository Foundation
- **Date:** 2026-07-13
- **Implementation status:** Claimed complete within the approved M0 scope
- **Owner acceptance:** Pending
- **Next milestone authorized:** No

## Work completed

- Initialized the current workspace as a Git repository on branch `main`.
- Added the Python `src/` package, provisional `forge` entry point, package version, help/version
  behavior, and callable schema-export placeholder.
- Added the constitution, canonical glossary, dependency rationale, and eleven foundational ADRs.
- Added the required Apache-2.0 license and public project documents.
- Added Windows, macOS, and Linux CI configuration for clean installation, CLI help, Ruff,
  Pyright, pytest, and distribution builds.
- Added M0 unit/smoke tests and a guard that rejects premature lifecycle module scaffolding.
- Recorded the eight approved internal M1 execution increments.

No production contracts, storage engine, lifecycle service, pack loader, adapter, capability,
artifact service, or FORGE-enabled repository behavior was implemented.

## Approval conditions incorporated

1. M1 is divided into eight internal increments in
   [`m1-execution-increments.md`](m1-execution-increments.md).
2. Secret detection is described as heuristic defense in depth in the constitution, threat-model
   ADR, security policy, and M1 increment plan.
3. M1 archival is labeled preliminary; M2 owns hash-chain integrity, interruption safety,
   recovery, concurrency, and corruption hardening.
4. ADR-0001 states that it was reconstructed from the approved specification on 2026-07-13 and
   is not represented as recovered history.

## Contracts and ADRs

M0 freezes constitutional principles and compatibility rules, not production schema fields.
ADRs added:

- ADR-0001 project direction and provisional naming
- ADR-0002 embedded project repositories
- ADR-0003 one active and many archived initiatives
- ADR-0004 source-of-truth hierarchy
- ADR-0005 event ordering and materialized state
- ADR-0006 artifact revisions and preservation
- ADR-0007 owner identity and actor authority
- ADR-0008 immutable decisions and acceptance
- ADR-0009 separate pack and capability trust
- ADR-0010 threat model and same-user limitation
- ADR-0011 pre-v1 compatibility

## Automated evidence

Local environment: Windows, Python 3.14.4. The project declares Python 3.12 or newer; CI is pinned
to Python 3.12 for the minimum-version check.

| Check | Result |
|---|---|
| `ruff check .` | Passed |
| `pyright --pythonpath .venv/Scripts/python.exe` | Passed: 0 errors, 0 warnings |
| `pytest` | Passed: 6 tests |
| `python -m build` | Passed: wheel and source distribution |
| Clean-wheel installation | Passed in `.smoke-venv` |
| Installed `forge --help` | Passed |
| Installed `forge --version` | Passed: `0.1.0a0` |
| Installed package import | Passed: `forge.__version__ == 0.1.0a0` |
| Local Markdown-link check | Passed for README and contributing guide |
| `git diff --check` | Passed |

Built artifacts at the time of evidence collection:

- `forge_governance-0.1.0a0-py3-none-any.whl`
- `forge_governance-0.1.0a0.tar.gz`

Build artifacts and virtual environments are ignored local outputs and are not governed source.

## Manual walkthrough

1. Installed the built wheel into a fresh virtual environment rather than importing the source
   tree.
2. Ran `forge --help` and observed only the M0 command scaffold.
3. Ran `forge --version` and received `0.1.0a0`.
4. Ran `forge schema export` and received the explicit M0 message that no production schemas are
   defined.
5. Imported `forge` from the clean environment and confirmed the same version.
6. Inspected the source tree and confirmed that deferred `contracts`, `core`, `storage`, `packs`,
   `agents`, and `capabilities` packages do not exist.

## Deviations

- The original historical ADR-0001 was not supplied. Per owner direction, ADR-0001 was
  reconstructed with explicit provenance rather than falsely imported.
- Local verification used the available Python 3.14.4 interpreter. Minimum-version and non-Windows
  execution remain assigned to the configured CI matrix.

## Unresolved evidence and risks

- The Windows/macOS/Linux workflow is configured but has not run in a hosted CI environment.
  Therefore cross-platform installation and CLI help are not yet claimed as observed evidence.
- Naming and distribution clearance remain unresolved. No package publication was attempted.
- The project has no production lifecycle behavior by design; M0 artifacts must not be described
  as a usable governance release.
- The security-reporting document intentionally avoids claiming a private channel or response-time
  service level that has not been established.

## Deferred-feature confirmation

No web or desktop UI, hosted infrastructure, remote registry, model-provider API, agent runtime,
multi-agent coordinator, database, semantic retrieval, executable capability, adapter, production
workflow, or ESDF migration was added. No ESDF content was modified.

## Recommended owner action

Review the constitutional artifacts and this evidence. If the owner requires cross-platform CI
results as a precondition to M0 acceptance, host or otherwise run the existing workflow first.
Only after explicit M0 acceptance may a separate M1 implementation brief authorize the first
production increment.

**Stop: M1 has not begun and is not authorized by this report.**

