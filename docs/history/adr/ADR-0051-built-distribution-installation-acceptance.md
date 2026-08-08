# ADR-0051: Built-Distribution Installation Acceptance

**Status:** Accepted
**Milestone:** M6 Increment 2

## Context

Release-candidate readiness requires FORGE to install through ordinary virtual environments and
`pipx` on Windows, macOS, and Linux across every supported Python version. Earlier milestone
smokes proved selected built wheels locally, while CI exercised only CPython 3.12 and installed
the editable checkout. Those results do not define or satisfy a complete installation support
matrix.

The matrix must be bounded, reproducible from an exact wheel, safe to run outside a source tree,
and usable by the deferred M6 closeout CI work. A successful process is evidence of one tested
cell; it is not owner acceptance or authority to publish.

## Decision

The release-candidate acceptance matrix is the Cartesian product of:

- CPython 3.12, 3.13, and 3.14;
- Windows, macOS, and Linux; and
- isolated ordinary-venv and `pipx` installation.

This produces 18 required cells. `requires-python = ">=3.12"` continues to permit later Python
versions, but FORGE makes no tested-support claim for an unlisted interpreter until the matrix is
deliberately revised.

`release/installation-matrix.json` is the data-only source for support expectations. It may name
platforms, versions, modes, expected metadata, schema count, and bundled packs. It cannot contain
commands. `tools/distribution_smoke.py` owns fixed subprocess argument vectors and never invokes a
shell. It:

1. validates that the current interpreter, operating system, and requested mode are an exact
   matrix cell;
2. creates an isolated temporary venv or isolated `pipx` home;
3. installs the exact wheel with normal dependency resolution;
4. invokes the installed `forge` console script;
5. checks version/help, initialization, configuration, both bundled packs, repository health, and
   the complete schema export; and
6. emits a deterministic summary containing the wheel SHA-256 digest and tested cell.

The harness does not persist its result into a governed FORGE repository. Release evidence and
owner acceptance remain separate later decisions.

## Consequences

- All supported installation cells share one executable smoke definition.
- The source tree cannot accidentally satisfy the import boundary because product commands run
  from the isolated installation and a temporary working directory.
- `pipx` remains a release-validation prerequisite, not a FORGE runtime or development
  dependency.
- Dependency download integrity still depends on the configured Python package index. Dependency,
  license, and vulnerability review remains a separate M6 increment.
- M6 closeout must execute all 18 cells from an exact published review commit before claiming
  cross-platform support. Increment 2 records only locally observed cells.
- This decision does not change contracts, persistence, authority, package version, or CI.
