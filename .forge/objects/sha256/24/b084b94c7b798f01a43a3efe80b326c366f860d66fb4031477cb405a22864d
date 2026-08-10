# PR 44 CI Repair Requirements

## Functional requirements

1. The Local Production-v1 fixture state must be loaded with `load_archive(layout, LOCAL_V1_INITIATIVE_ID)`.
2. Lifecycle and predecessor assertions must inspect `local_v1.active`.
3. Existing predecessor references must remain asserted rather than being removed or weakened.
4. Local Production-v1 must be asserted as `LifecycleState.CLOSED`.
5. The M6 predecessor must remain asserted as `LifecycleState.CLOSED`.
6. The public M7 predecessor must remain asserted as `LifecycleState.ABANDONED`.
7. The Local Production-v1 archive manifest digest must equal `sha256:4b3eb9592b58f0325a6e5b5380f681fd9189154d88fc3b06aa58b8de4deccbbf`.
8. No production file may change.

## Verification requirements

- The focused command `.\.venv\Scripts\python.exe -m pytest tests/test_local_v1_l1.py -q` must exit successfully.
- The implementation diff must contain only the accepted test change plus legitimate FORGE governance records and declared workflow artifacts.
- The final report must state the exact focused-test result and any remaining limitations.
- Full Windows, Ubuntu, and macOS matrix verification is deferred to GitHub Actions after separately authorized publication.

## Definition of done

- The stale active-initiative assumption is replaced by immutable archive validation.
- All predecessor relationships and distinct terminal outcomes remain covered.
- The exact Local Production-v1 archive digest is covered.
- The focused test passes without production-code changes.
- No commit or publication occurs without a separate owner instruction.

## Evidence boundaries

A worker claim is not a check, evidence packet, or owner acceptance. Focused test output must be recorded independently through the FORGE verification workflow, and owner acceptance remains a separate gate.
