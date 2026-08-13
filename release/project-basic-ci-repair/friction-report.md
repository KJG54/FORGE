# CI-detection friction report

The original CI report represented one historical README contract failure repeated across nine
matrix jobs plus two Ruff blockers. After those were repaired, the quality gate surfaced six
Pyright findings that had been masked by the earlier Ruff stop.

The lasting response is documented in `docs/git-and-closure.md`: retain the exact failing pattern,
make the smallest bounded successor repair, run relevant local tests and quality checks, and keep
CI, Git push, FORGE acceptance, and terminal closure as separate facts.
