"""Read-only hybrid Git policy inspection.

Git is collaboration and transport infrastructure for FORGE. Governed filesystem
records remain authoritative regardless of Git availability, and this module never
changes the worktree, index, configuration, or history.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from forge.errors import ConflictError, IntegrityError

if TYPE_CHECKING:
    from forge.storage.repository import RepositoryLayout

GIT_TIMEOUT_SECONDS = 10
_LOCAL_PROBE = ".forge/local/.forge-ignore-probe"
_GOVERNED_PROBES = (
    "forge.yaml",
    ".forge/active/initiative.json",
    ".forge/active/events.jsonl",
    ".forge/active/migration-sources/source.jsonl",
    ".forge/archive/archive-probe/archive-manifest.json",
    ".forge/idempotency/receipt.json",
    ".forge/objects/sha256/00/object",
)


def _governed_paths(layout: RepositoryLayout) -> tuple[str, ...]:
    """Return canonical probes plus existing governed paths without following links."""
    paths: set[str] = set(_GOVERNED_PROBES)
    if layout.configuration_file.exists() or layout.configuration_file.is_symlink():
        paths.add("forge.yaml")
    stack = [layout.forge_directory]
    while stack:
        directory = stack.pop()
        if not directory.is_dir() or directory.is_symlink():
            continue
        for entry in directory.iterdir():
            relative = entry.relative_to(layout.root).as_posix()
            if relative == ".forge/local" or relative.startswith(".forge/local/"):
                continue
            paths.add(relative)
            if entry.is_dir() and not entry.is_symlink():
                stack.append(entry)
    return tuple(sorted(paths))


@dataclass(frozen=True)
class GitPolicyReport:
    """Observed read-only Git transport state for one FORGE repository."""

    git_available: bool
    worktree_root: Path | None
    tracked_governed_count: int
    untracked_governed_paths: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def inside_worktree(self) -> bool:
        return self.worktree_root is not None


def _run_git(
    layout: RepositoryLayout,
    *arguments: str,
    input_data: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=layout.root,
        input=input_data,
        capture_output=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )


def _diagnostic(completed: subprocess.CompletedProcess[bytes]) -> str:
    return completed.stderr.decode("utf-8", errors="replace").strip()


def _nul_paths(output: bytes) -> tuple[str, ...]:
    return tuple(
        sorted(
            item.decode("utf-8", errors="replace")
            for item in output.split(b"\0")
            if item
        )
    )


def _probe_worktree(
    layout: RepositoryLayout,
) -> tuple[bool, Path | None, str | None]:
    try:
        completed = _run_git(layout, "rev-parse", "--show-toplevel")
    except FileNotFoundError:
        return (
            False,
            None,
            "Git executable is unavailable; FORGE remains filesystem-authoritative, "
            "but governed records are not being checked for Git transport",
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return (
            False,
            None,
            "Git worktree inspection is unavailable; FORGE remains filesystem-authoritative: "
            f"{error}",
        )
    if completed.returncode != 0:
        return (
            True,
            None,
            "Repository is not inside a Git worktree; FORGE remains filesystem-authoritative, "
            "but governed records are not versioned by Git",
        )
    rendered = completed.stdout.decode("utf-8", errors="replace").strip()
    if not rendered:
        return True, None, "Git returned an empty worktree root; Git transport was not validated"
    return True, Path(rendered).resolve(), None


def _check_ignored(
    layout: RepositoryLayout,
    paths: tuple[str, ...],
) -> tuple[str, ...]:
    payload = b"\0".join(path.encode("utf-8") for path in paths) + b"\0"
    completed = _run_git(
        layout,
        "check-ignore",
        "--no-index",
        "-z",
        "--stdin",
        input_data=payload,
    )
    if completed.returncode not in {0, 1}:
        detail = _diagnostic(completed)
        raise IntegrityError(
            "Cannot inspect effective Git ignore policy"
            + (f": {detail}" if detail else "")
        )
    return _nul_paths(completed.stdout)


def _list_paths(layout: RepositoryLayout, *arguments: str) -> tuple[str, ...]:
    completed = _run_git(layout, *arguments)
    if completed.returncode != 0:
        detail = _diagnostic(completed)
        raise IntegrityError(
            "Cannot inspect Git tracking state" + (f": {detail}" if detail else "")
        )
    return _nul_paths(completed.stdout)


def ignored_governed_paths(layout: RepositoryLayout) -> tuple[str, ...] | None:
    """Return effectively ignored governed probes, or ``None`` outside usable Git."""
    available, worktree_root, _ = _probe_worktree(layout)
    if not available or worktree_root is None:
        return None
    try:
        return _check_ignored(layout, _governed_paths(layout))
    except (IntegrityError, OSError, subprocess.TimeoutExpired):
        # Initialization remains local-first and must not depend on Git availability.
        # Full diagnostics surface an actionable error when Git claims a worktree but
        # its policy cannot be inspected.
        return None


def inspect_git_policy(layout: RepositoryLayout) -> GitPolicyReport:
    """Validate effective hybrid policy without changing Git or FORGE state."""
    available, worktree_root, warning = _probe_worktree(layout)
    if worktree_root is None:
        return GitPolicyReport(
            git_available=available,
            worktree_root=None,
            tracked_governed_count=0,
            untracked_governed_paths=(),
            warnings=(warning,) if warning is not None else (),
        )

    try:
        ignored_governed = _check_ignored(layout, _governed_paths(layout))
        ignored_local = _check_ignored(layout, (_LOCAL_PROBE,))
        tracked_local = _list_paths(layout, "ls-files", "-z", "--", ".forge/local")
        tracked = _list_paths(layout, "ls-files", "-z", "--", "forge.yaml", ".forge")
        untracked = _list_paths(
            layout,
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "forge.yaml",
            ".forge",
        )
    except subprocess.TimeoutExpired as error:
        raise IntegrityError(f"Git policy inspection timed out: {error}") from error
    except OSError as error:
        raise IntegrityError(f"Git policy inspection failed: {error}") from error

    if ignored_governed:
        paths = ", ".join(ignored_governed)
        raise IntegrityError(
            "Git ignore rules hide governed FORGE paths: "
            f"{paths}; rerun 'forge init' to append the hybrid policy after conflicting rules"
        )
    if _LOCAL_PROBE not in ignored_local:
        raise IntegrityError(
            "Git policy does not effectively ignore .forge/local/; rerun 'forge init'"
        )
    if tracked_local:
        paths = ", ".join(tracked_local)
        raise IntegrityError(
            "Git already tracks local-only FORGE paths: "
            f"{paths}; FORGE will not alter the Git index—review the paths and remove them "
            "from the index explicitly if appropriate"
        )

    governed_tracked = tuple(path for path in tracked if not path.startswith(".forge/local/"))
    governed_untracked = tuple(
        path for path in untracked if not path.startswith(".forge/local/")
    )
    warnings: tuple[str, ...] = ()
    if governed_untracked:
        preview = ", ".join(governed_untracked[:3])
        if len(governed_untracked) > 3:
            preview += ", ..."
        warnings = (
            f"{len(governed_untracked)} governed FORGE file(s) are not tracked by Git "
            f"({preview}); review and add forge.yaml and .forge/ when ready",
        )
    return GitPolicyReport(
        git_available=True,
        worktree_root=worktree_root,
        tracked_governed_count=len(governed_tracked),
        untracked_governed_paths=governed_untracked,
        warnings=warnings,
    )


def require_clean_worktree(layout: RepositoryLayout) -> None:
    """Enforce the optional clean-worktree closure policy without false cleanliness."""
    report = inspect_git_policy(layout)
    if not report.inside_worktree:
        detail = report.warnings[0] if report.warnings else "Git worktree is unavailable"
        raise ConflictError(f"Cannot verify the configured clean-Git close policy: {detail}")
    try:
        completed = _run_git(layout, "status", "--porcelain=v1", "--untracked-files=all")
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ConflictError(
            f"Cannot verify the configured clean-Git close policy: {error}"
        ) from error
    if completed.returncode != 0:
        detail = _diagnostic(completed)
        raise ConflictError(
            "Closure requires a clean Git worktree, but Git status failed"
            + (f": {detail}" if detail else "")
        )
    if completed.stdout:
        raise ConflictError("Closure requires a clean Git worktree by project configuration")
