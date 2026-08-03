"""Run the exact fast quality gate used locally and in GitHub Actions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(
    command: tuple[str, ...],
    *,
    cwd: Path,
    label: str,
    required_output: str | None = None,
) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    combined = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
        raise SystemExit(f"{label} failed with exit code {result.returncode}")
    if required_output is not None and required_output not in combined:
        raise SystemExit(
            f"{label} produced no trustworthy identifying output; refusing a false pass"
        )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    python = sys.executable
    _run(
        (python, "-m", "ruff", "check", "."),
        cwd=root,
        label="Ruff",
        required_output="All checks passed!",
    )
    _run(
        (python, "-m", "pyright", "--version"),
        cwd=root,
        label="Pyright version check",
        required_output="pyright ",
    )
    _run(
        (python, "-m", "pyright", "--pythonpath", python),
        cwd=root,
        label="Pyright",
        required_output="0 errors",
    )
    _run(
        (python, "-m", "tools.version_consistency"),
        cwd=root,
        label="Version consistency",
        required_output='"status": "passed"',
    )
    print("FORGE fast quality gate: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
