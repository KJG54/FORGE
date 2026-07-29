# M6 Increment 2 — Built-Distribution Installation Matrix

## Authorized scope

- define the bounded release-candidate Python, operating-system, and installation matrix;
- add one cross-platform harness that installs an exact wheel outside the source tree;
- exercise both an ordinary virtual environment and an isolated `pipx` home;
- validate installed version/help, repository initialization, configuration, bundled packs,
  repository health, and schema export;
- bind each result to the wheel SHA-256 digest and exact matrix cell; and
- document installation methods, tested-support meaning, and explicit non-claims.

The matrix contains 18 cells: CPython 3.12–3.14 × Windows/macOS/Linux × venv/`pipx`.

## Explicit exclusions

GitHub Actions changes, remote matrix execution, source-distribution installation, example
repositories and full example workflows, public package publication, dependency and security
reviews, performance budgets, complete documentation, dogfooding, friction reporting, release
signing, OpenTelemetry, SQLite FTS, and M7 work are not implemented.

Per owner direction, CI configuration and remote CI evidence remain deferred until M6 closeout.

## Authority, persistence, failure, and security semantics

Increment 2 changes no public contract, persisted record, migration, authority, capability, or
runtime command. The matrix is strictly data-only and rejects unknown fields; it cannot declare
commands. The harness owns fixed subprocess argument vectors, sets `shell=False`, uses a fresh
temporary root, and isolates all `pipx` state. An explicitly supplied work directory must not
already exist and is retained rather than deleted.

The harness fails closed for an unknown operating system, Python implementation or version, mode,
malformed matrix, missing wheel, failed install, missing console script, unexpected command
output, invalid schema index, or schema-count mismatch. A pass is evidence for one cell, not a
release decision or owner acceptance.

Normal dependency resolution uses the operator-configured package index. It does not establish
dependency integrity, license acceptability, or vulnerability absence; those reviews remain
separate M6 work.

## Design evidence

[ADR-0051](../adr/ADR-0051-built-distribution-installation-acceptance.md) records the exact support
matrix and executable harness boundary. [`installation.md`](../installation.md) is the
reader-facing installation guide.

## Validation evidence

- focused matrix, metadata, path, scratch, and console-encoding coverage: 8 passed;
- complete local suite: 323 passed with 7 expected Windows privilege-based symlink skips and no
  failures;
- Ruff: clean;
- strict Pyright, including `tools/`: 0 errors and 0 warnings;
- `git diff --check`: clean;
- Hatchling 1.31.0 built the source distribution and wheel outside the source tree;
- source-archive inspection found the matrix, harness, ADR, installation guide, Increment 2
  record, and focused test module;
- the exact wheel
  `forge_governance-0.1.0a0-py3-none-any.whl` had SHA-256 digest
  `11cdd6a5615c38b7f6646c64e9a5d18c0c013274561f36596053200e28573d75`;
- a fresh Windows CPython 3.14 venv installed that wheel and passed module and console-script
  version, help, initialization, configuration, both bundled packs, doctor, and 51-schema export;
  and
- `pipx` 1.16.3 installed the same wheel into an isolated home on Windows CPython 3.14 and passed
  the same console-script product smoke.

Exactly 2 of 18 matrix cells are locally observed. The remaining 16 cells and all remote evidence
are intentionally deferred until M6 closeout by owner direction.

## Stop point

Stop after the matrix, reusable smoke harness, focused tests, installation documentation, and
local venv/`pipx` evidence for the available Windows CPython 3.14 cell. Do not modify CI, claim the
remaining 16 cells, add examples, publish a package, or begin Increment 3 without a separate owner
decision.
