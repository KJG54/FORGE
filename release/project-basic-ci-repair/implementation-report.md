# Project-basic CI contract repair implementation report

## Changes made

- Restored the accurate historical Local Production-v1 README statement, including the
  `protocol 1.4.0` text required by the historical documentation contract.
- Wrapped the two Ruff `E501` lines in `tests/test_cli.py` and
  `tools/version_consistency.py` without changing behavior.
- Added explicit UUID list annotations to `tests/test_project_basic_workflow.py`, resolving the
  six Pyright errors that became visible after Ruff passed.
- Added `CI-detection friction` guidance to `docs/git-and-closure.md`. It preserves the separation
  among CI diagnostics, Git publication, FORGE acceptance, and terminal closure.

## Local validation

- `python -m pytest tests/test_local_v1_l8.py tests/test_cli.py` — 17 passed, using an external
  writable pytest base so the pre-initialization test did not inherit this repository's state.
- `python -m pytest tests/test_project_basic_workflow.py` — 2 passed.
- `python -m tools.quality_gate` — passed; Pyright reported 0 errors and 0 warnings.

## Limitations

- A full 465-test suite was started but the terminal bridge did not retain its final result. It is
  not claimed as validation evidence.
- Replacement GitHub Actions CI is intentionally not awaited or claimed. The owner will review it
  after the branch push.

## Preservation

No bundled-pack source, pack version, digest, framework version, protocol version, archive,
candidate artifact, release state, CLI default, or publication boundary changed.
