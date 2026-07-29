# ADR-0057: One-Wheel Release-Closeout Matrix

**Status:** Accepted

**Milestone:** M6 Increment 8

## Context

M6 defines 18 supported installation cells and requires cross-platform tests, fresh-user examples,
operational rehearsals, security review, and performance budgets. Rebuilding independently in
every cell would make each job test different bytes. Running every expensive scenario twice on
both branch push and pull request would add cost without stronger artifact identity.

The existing CI covers three operating systems but only CPython 3.12, installs editable source,
and builds independently in each job. It does not execute the maintained installation matrix or
release scenarios.

## Decision

CI builds one wheel on CPython 3.12 and uploads it as the sole downstream candidate artifact.

- The complete test suite runs on Windows, macOS, and Linux with CPython 3.12, 3.13, and 3.14.
- The exact wheel runs all 18 OS/Python/venv-or-`pipx` installation cells.
- Performance runs against that wheel in all nine OS/Python cells.
- Both examples and the procedure rehearsal run once per operating system on Python 3.12.
- Ruff, Pyright, and CLI help remain a separate quality job.
- Pull requests and `main` pushes run the matrix; ordinary branch pushes do not duplicate it.
- Artifact upload/download failures fail closed, and the wheel path/version is exact.

## Consequences

Every downstream result is attributable to one built wheel rather than nine independently produced
candidates. The matrix contains 38 jobs, but independent cells can run concurrently and failures
do not cancel unrelated evidence.

The source distribution is built and retained but installation acceptance remains wheel-specific,
matching the declared installation policy. Platform-specific dependency resolution and host
behavior remain visible in exact job results.

Remote results cannot be recorded before the pull request exists. Increment 8 therefore produces
local evidence first, then requires the exact published commit and merged commit matrices before
M6 acceptance.

## Rejected alternatives

- **Keep Python 3.12-only CI.** This would leave six supported OS/Python cells untested.
- **Rebuild in every matrix cell.** Results would no longer share exact candidate bytes.
- **Run examples and procedures in all 18 installation cells.** This adds repetition without
  materially increasing platform or interpreter coverage.
- **Treat editable-source tests as distribution evidence.** That bypasses packaging, entry-point,
  resource, and installation behavior.
