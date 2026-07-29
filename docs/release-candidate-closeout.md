# M6 Release-Candidate Closeout

M6 Increment 8 closes the release-candidate evidence boundary. It does not tag, publish, sign, or
authorize Production v1.

## Remote validation topology

The GitHub Actions workflow builds one wheel and reuses that exact artifact:

| Job | Matrix | Purpose |
|---|---:|---|
| Quality | 1 | CLI help, Ruff, and strict Pyright |
| Tests | 9 | Complete suite on three operating systems and CPython 3.12–3.14 |
| Build | 1 | One source distribution and one reusable wheel |
| Installation | 18 | Every OS, Python, and venv/`pipx` installation cell |
| Release scenarios | 9 | Exact-wheel performance on every OS/Python cell |

The Python 3.12 release-scenario cell on each operating system also completes both static example
workflows and rehearses backup, migration, recovery, abandonment, archive access, and successor
lineage. This keeps cross-platform evidence while avoiding three identical procedure runs per
operating system.

Branch pushes do not run a duplicate matrix. Pull requests run the complete candidate matrix, and
pushes to `main` repeat it for the merged commit.

## Maintained local procedure rehearsal

Run against the exact installed console script under review:

```console
python -m tools.release_procedure_rehearsal --forge <exact-forge-executable>
```

The shell-free harness uses temporary synthetic repositories and exercises:

- a complete repository backup and healthy restored copy;
- explicit legacy-journal migration with preserved source;
- detection and governed recovery of a missing derived snapshot;
- explicit abandonment as a non-success terminal outcome;
- read-only access to the abandoned archive; and
- a fresh successor with immutable predecessor lineage.

Both example workflows separately exercise successful closure and immutable archive inspection.
The procedure harness cannot accept real work, alter the FORGE source repository, or establish
release readiness.

## Governed closeout sequence

The tracked `framework-change` initiative keeps each closeout fact separate:

1. `implement` records the exact closeout automation and evidence changes.
2. `verify-release` records complete local and remote release validation.
3. `review-risk` records observed friction and every classified residual risk.
4. `closeout` records the owner-reviewed readiness decision and lessons.

Each step still requires a claim, declared check, evidence, verification, and an explicit
configured-owner acceptance. A pull-request merge or green matrix is not acceptance.

## Required evidence

Closeout is not complete until the exact candidate commit has:

- complete local tests, lint, typing, build, and source/wheel inspection;
- both local installation modes and both fresh-user example workflows;
- local security and performance reviews;
- the maintained operational procedure rehearsal;
- a pull-request matrix result for every declared cell;
- a merged-commit matrix result for every declared cell;
- a friction report with reproducible findings;
- a residual-risk register with severity and owner disposition; and
- an M6 evidence report mapping every roadmap deliverable and exit criterion.

Failures remain release-blocking until corrected or explicitly classified and resolved by the
owner. M7 remains a separate owner decision.
