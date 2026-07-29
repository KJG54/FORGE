# ADR-0059: Production-v1 Identity, Version, and Publication Channels

**Status:** Accepted

**Date:** 2026-07-29

**Milestone:** M7 Increment 1

## Context

FORGE completed M6 as the provisional Python distribution `forge-governance`, import package
`forge`, and command `forge`, at pre-release version `0.1.0a0`. Production v1 needs one
owner-reviewed public identity, explicit version boundaries, canonical public locations, and a
publication trust model before release metadata or automation can be finalized.

An exact-name check on 2026-07-29 found no indexed `forge-governance` project on the PyPI or
TestPyPI simple indexes. The shorter `forge` distribution name is already used by an unrelated
project. Automated index and web searches establish neither continued availability nor trademark
or other legal clearance.

The Production-v1 roadmap requires public source and Python artifacts. It does not make
standalone signing a blocker, and it preserves owner authority over every irreversible external
action.

## Decision

### Public identity

- The owner-approved public product mark is **FORGE Governance**.
- The Python distribution name remains `forge-governance`.
- The Python import package remains `forge`.
- The command-line entry point remains `forge`.
- The owner accepts the practical command-name collision risk in favor of preserving the
  established interface.

This is an owner-reviewed project decision, not legal clearance. Before Production-v1 publication,
the owner must either accept the remaining legal uncertainty for publication or supply a stronger
clearance result. Package-index availability must also be checked again immediately before any
publisher is configured or release is uploaded.

### Version contract

- The first public production distribution version is `1.0.0`.
- Its immutable Git tag is `v1.0.0`.
- The distribution remains at its current pre-release version until M7 Increment 2 freezes and
  consistently updates the compatibility and version contract.
- Public persisted `schema_version: "1.0"` values are contract versions, not distribution
  versions, and are not mechanically rewritten.
- Bundled-pack, local-pack, and workflow versions remain independent semantic versions. Their
  compatibility with the v1 distribution is declared explicitly rather than inferred from equal
  version numbers.
- A published tag or artifact is never moved, overwritten, or silently rebuilt.

### Canonical public locations

- Repository, source, and v1 homepage:
  `https://github.com/KJG54/FORGE`
- Documentation for v1:
  `https://github.com/KJG54/FORGE/tree/main/docs`
- Public issues:
  `https://github.com/KJG54/FORGE/issues`
- Security policy:
  `https://github.com/KJG54/FORGE/security/policy`
- Private vulnerability reports, after the repository feature is enabled and verified:
  `https://github.com/KJG54/FORGE/security/advisories/new`
- Production Python distribution:
  `https://pypi.org/project/forge-governance/`
- Rehearsal Python distribution:
  `https://test.pypi.org/project/forge-governance/`

Private vulnerability reporting was disabled when this decision was recorded. Increment 3 must
configure and verify it before FORGE presents that URL as an available reporting channel.

### Channels and supply-chain evidence

- PyPI is the primary public Python package index.
- GitHub Releases publishes the matching source distribution, wheel, checksums, release notes,
  provenance, and SBOM for the immutable tag.
- TestPyPI is the external rehearsal channel in Increment 5; it is not Production-v1 publication
  evidence.
- TestPyPI and PyPI use tokenless OpenID Connect trusted publishing through separate protected
  GitHub environments named `testpypi` and `pypi`.
- Any TestPyPI upload requires the increment-specific owner authorization for that external
  rehearsal. The `pypi` environment requires owner approval for production publication.
- The release reuses one exact source distribution and one exact universal wheel built from the
  approved commit. Validation and publication do not rebuild them.
- PyPI publish attestations and GitHub build-provenance attestations are required release evidence.
- The release includes an SPDX 2.3 JSON software bill of materials and a GitHub SBOM attestation.
- Production v1 has no separate long-lived signing key or standalone package signature. Keyless
  attestations provide provenance without creating a private-key custody burden.

Trusting the declarative M7 pack as data grants no executable, credential, environment, tag, or
publication authority.

## Consequences

The project has stable identity and channel inputs for later metadata, support, documentation, and
automation work. Keeping the `forge` command avoids a breaking rename but does not guarantee global
command uniqueness. Using `forge-governance` avoids the already occupied `forge` distribution
name, while availability and legal uncertainty remain explicit release-time checks.

M7 Increment 1 changes no package version, public repository setting, tag, release, publisher, or
package index. TestPyPI rehearsal and Production-v1 publication remain separate, owner-gated
external actions. A passing build, accepted workflow step, or trusted data pack cannot authorize
either action.

## Rejected alternatives

- **Use `forge` as the distribution name.** It is already occupied by an unrelated PyPI project.
- **Rename the import or CLI for v1.** This adds avoidable compatibility disruption after the
  interface has already been rehearsed and documented.
- **Treat automated searching as legal clearance.** Search results cannot establish trademark or
  other legal rights.
- **Store long-lived package-index tokens.** Trusted publishing provides narrower, short-lived
  credentials bound to the approved repository workflow and environment.
- **Require standalone signatures for v1.** This would add key-management obligations without
  enough benefit beyond the selected keyless attestations.
- **Publish separately rebuilt artifacts to each channel.** That would break the exact-artifact
  evidence chain.
