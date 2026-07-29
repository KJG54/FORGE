# FORGE Production-v1 Naming and Channel Contract

## Owner-reviewed identity

| Boundary | Accepted value |
| --- | --- |
| Public product mark | FORGE Governance |
| Python distribution | `forge-governance` |
| Python import package | `forge` |
| CLI command | `forge` |
| First production version | `1.0.0` |
| Immutable release tag | `v1.0.0` |

The owner accepts the practical CLI collision risk and the absence of legal clearance at this
stage. The exact `forge-governance` name was not indexed by PyPI or TestPyPI when checked on
2026-07-29, while the shorter `forge` distribution name was occupied by an unrelated project.
Availability must be rechecked before publisher configuration and publication. These observations
do not establish trademark, ownership, reservation, or future availability.

## Canonical URLs

| Purpose | Canonical URL |
| --- | --- |
| Repository, source, homepage | `https://github.com/KJG54/FORGE` |
| Documentation | `https://github.com/KJG54/FORGE/tree/main/docs` |
| Issues | `https://github.com/KJG54/FORGE/issues` |
| Security policy | `https://github.com/KJG54/FORGE/security/policy` |
| Private vulnerability report | `https://github.com/KJG54/FORGE/security/advisories/new` |
| PyPI | `https://pypi.org/project/forge-governance/` |
| TestPyPI | `https://test.pypi.org/project/forge-governance/` |

Private vulnerability reporting was disabled when checked. Increment 3 must enable and verify it
before documentation represents the private-report URL as operational.

## Publication and evidence contract

- PyPI is the primary Python package index; TestPyPI is the rehearsal channel.
- GitHub Releases carries the exact matching sdist, wheel, checksums, notes, provenance, and SBOM.
- TestPyPI and PyPI use separate protected `testpypi` and `pypi` GitHub environments with
  tokenless OpenID Connect trusted publishing.
- External rehearsal and production publication each require explicit owner authorization.
- Production publication additionally requires owner approval at the protected `pypi`
  environment.
- One exact sdist and one exact universal wheel are built once, completely verified, and reused
  unchanged for every approved publication target.
- Required supply-chain evidence consists of artifact hashes, PyPI publish attestations, GitHub
  build-provenance attestations, an SPDX 2.3 JSON SBOM, and a GitHub SBOM attestation.
- Production v1 uses no standalone package-signing key or signature.
- Published tags and artifacts are immutable and are never overwritten or silently rebuilt.
- Yank and incident procedures may limit or withdraw availability but never replace historical
  bytes under the same version.

## Version boundaries

Distribution version `1.0.0`, persisted `schema_version: "1.0"`, and pack/workflow versions are
independent contracts. Increment 2 will define and validate their exact compatibility without
rewriting immutable archives or mechanically setting every version to `1.0.0`.

This document records the approved planning contract. It is not an external-action authorization,
legal opinion, package-index reservation, release candidate, or publication acceptance.
