# PR 44 CI Repair Change Scope

## Objective

Repair the stale Local Production-v1 closeout-state test in PR 44 so it validates the immutable closed archive instead of requiring an active initiative. This is a test-only compatibility correction; production behavior must not change.

## In scope

- Modify only `tests/test_local_v1_l1.py` during implementation.
- Replace `load_active_initiative(layout)` for Local Production-v1 with `load_archive(layout, LOCAL_V1_INITIATIVE_ID)` and inspect `local_v1.active`.
- Preserve the existing predecessor-reference assertions.
- Expect Local Production-v1 to be `CLOSED`, M6 to be `CLOSED`, and public M7 to be `ABANDONED`.
- Assert the Local Production-v1 archive digest is `sha256:4b3eb9592b58f0325a6e5b5380f681fd9189154d88fc3b06aa58b8de4deccbbf`.
- Rename the test only if needed to describe archived rather than active state.
- Run `.\.venv\Scripts\python.exe -m pytest tests/test_local_v1_l1.py -q` as the focused implementation check.
- Create only the FORGE governance records and declared workflow artifacts required to govern this repair.

## Exclusions

- No production-code changes.
- No archive mutation, reopening, or manual editing of `.forge` state.
- No Git history rewriting or amending.
- No branch switching or unrelated cleanup.
- No broad local test runs; GitHub Actions remains responsible for the complete cross-platform matrix.
- No commit, push, pull-request update, or other publication without separate owner authorization.

## Compatibility impact

The intended implementation changes only a repository-state test assumption. It preserves the production archive and successor APIs and strengthens closeout coverage by binding the test to the immutable archive digest.

## Risks and mitigations

- Risk: historical coverage could be weakened while replacing the active-state lookup. Mitigation: preserve predecessor-reference and distinct lifecycle assertions.
- Risk: the test could validate the wrong terminal archive. Mitigation: use `LOCAL_V1_INITIATIVE_ID` and assert the exact archive digest.
- Risk: scope creep could obscure the CI defect. Mitigation: restrict implementation to one test file and the focused test command.

## Abandonment conditions

Stop and return to owner review if the repair requires production-code behavior changes, archive mutation, expanded test scope, or any action excluded above.

## Predecessor

This successor is linked to closed initiative `26c0c628-cc77-478c-b77b-0c1d703891ac`, whose validated archive digest is `sha256:4b3eb9592b58f0325a6e5b5380f681fd9189154d88fc3b06aa58b8de4deccbbf`.
