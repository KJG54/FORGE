# Project-basic CI contract repair scope

## Objective

Repair the CI failures introduced on `codex/project-basic` without changing the
`project-basic` workflow, any existing pack identity, framework version, protocol version, archive,
release state, or publication boundary.

## Diagnosis

GitHub Actions run `31656597126` reported ten failed checks:

- Each of the nine platform/Python test jobs had the same single failure:
  `tests/test_local_v1_l8.py::test_candidate_readme_and_walkthroughs_track_the_installed_protocol`.
  The README edit removed the contiguous text required by that historical contract:
  `protocol 1.4.0`.
- The quality job stopped at Ruff with two `E501` line-length violations in
  `tests/test_cli.py` and `tools/version_consistency.py`.

## In scope

1. Restore accurate README wording that preserves the historical Local Production-v1 statement
   and the contiguous `protocol 1.4.0` contract text.
2. Wrap the two Ruff violations without changing their behavior.
3. Document the CI-detection friction and a local pre-push practice that preserves the separation
   among CI, Git, FORGE acceptance, and closure.
4. Run focused and quality validation, then commit and push the bounded repair to the existing
   feature branch. Remote CI remains owner-reviewed and is not claimed as evidence here.

## Out of scope

- Any change to `project-basic`, `software-basic`, or `research-basic` bytes, versions, or digests.
- New lifecycle, protocol, CLI, publication, candidate, tag, or release behavior.
- Altering immutable archives or historical candidate artifacts.

## Compatibility statement

This repair restores documentation/test-contract compatibility and lint formatting only. It does
not grant authority, change conditions, actors, transitions, owner acceptance, or the CLI default.
