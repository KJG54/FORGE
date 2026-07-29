# M6 Increment 8 Framework Changes

## Implemented boundary

- Expand the complete test suite to Windows, macOS, and Linux on CPython 3.12, 3.13, and 3.14.
- Build one source distribution and one wheel, then reuse the exact wheel in every downstream job.
- Execute all 18 declared venv/`pipx` installation cells.
- Enforce maintained performance budgets in all nine operating-system/Python cells.
- Complete both built-wheel example workflows on every operating system.
- Rehearse backup, legacy migration, missing-snapshot recovery, restore, abandonment, archive
  access, and successor lineage on every operating system.
- Avoid duplicate branch-push matrices while retaining pull-request and merged-`main` evidence.
- Preserve separate configured-owner gates for implementation, verification, risk review, and
  readiness.

## Exact implementation bytes

| Path | SHA-256 |
|---|---|
| `.github/workflows/ci.yml` | `sha256:19ef291b8eef37e086361878bbf130aaca817694542e9314ae2560b7aa3c367f` |
| `tools/example_workflow_smoke.py` | `sha256:4dc9a22f5d26007a578385aa632bfb372907904c12c8243db04056fcfcf1b83f` |
| `tools/release_procedure_rehearsal.py` | `sha256:291350c58a6e8599beea34135193bcb243eabb2192a95b53ae7670e4349c552c` |
| `tests/test_m6_increment_7.py` | `sha256:6eeb1484b3645585699bd0e8e79020544214c61d459022b3ab528ace07a82b5a` |
| `tests/test_m6_increment_8.py` | `sha256:456404fc9feb6cc99bac7e76d11251833773964f774db12b169b97e346295b23` |
| `docs/release-candidate-closeout.md` | `sha256:f139908eeaefd9eca2b194121ae6564a2da4c2717ec5bc8fede96e378cc1c443` |
| `docs/adr/ADR-0057-one-wheel-release-closeout-matrix.md` | `sha256:201a9d083a6a0882e2a0f39189aabaddce95598035cc84a1acec434c9b7389cc` |

## Compatibility, authority, and security impact

No runtime command, public contract, schema, persisted format, migration, bundled pack, dependency,
or executable capability changes. The new procedure tool uses the existing installed APIs only to
construct a bounded legacy fixture; every reviewed procedure uses fixed CLI argument vectors with
`shell=False`.

The CI workflow can report evidence but cannot create FORGE acceptance, resolve residual risk,
close M6, authorize M7, tag, sign, or publish a release.

## Evidence state

Focused implementation tests, Ruff, strict Pyright, formatting checks, and one local procedure
rehearsal pass. Complete local release validation and all remote matrix cells remain later
`verify-release` evidence.
