import subprocess
from pathlib import Path

import pytest

from forge.core import git_policy
from forge.core.diagnostics import inspect_repository_health
from forge.core.git_policy import inspect_git_policy, require_clean_worktree
from forge.errors import ConflictError, IntegrityError
from forge.storage.repository import initialize_repository


def _git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except FileNotFoundError:
        pytest.skip("Git is unavailable")
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    return completed


def _git_repository(path: Path) -> None:
    path.mkdir()
    _git(path, "init", "--quiet")


def _is_ignored(repository: Path, relative_path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", "--", relative_path],
        cwd=repository,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert completed.returncode in {0, 1}
    return completed.returncode == 0


def test_init_preserves_rules_and_applies_effective_hybrid_policy(tmp_path: Path) -> None:
    repository = tmp_path / "project"
    _git_repository(repository)
    gitignore = repository / ".gitignore"
    original = b"*.yaml\r\n.forge/\r\nunrelated/\r\n"
    gitignore.write_bytes(original)

    initialized = initialize_repository(repository, owner_display_name="Owner")

    assert initialized.gitignore_changed is True
    assert gitignore.read_bytes().startswith(original)
    assert b"!/forge.yaml\r\n" in gitignore.read_bytes()
    assert b"!/.forge/**\r\n" in gitignore.read_bytes()
    assert _is_ignored(repository, "forge.yaml") is False
    assert _is_ignored(repository, ".forge/active/initiative.json") is False
    assert _is_ignored(repository, ".forge/local/locks/mutation.lock") is True

    before = gitignore.read_bytes()
    repeated = initialize_repository(repository, owner_display_name="Different Owner")
    assert repeated.gitignore_changed is False
    assert gitignore.read_bytes() == before


def test_init_reappends_policy_after_later_conflicting_rules(tmp_path: Path) -> None:
    repository = tmp_path / "project"
    _git_repository(repository)
    initialized = initialize_repository(repository, owner_display_name="Owner")
    governed_file = initialized.layout.forge_directory / "specific-governed.json"
    governed_file.write_text("{}", encoding="utf-8")
    gitignore = repository / ".gitignore"
    gitignore.write_text(
        gitignore.read_text(encoding="utf-8") + ".forge/specific-governed.json\n",
        encoding="utf-8",
    )

    with pytest.raises(IntegrityError, match="hide governed FORGE paths"):
        inspect_git_policy(initialized.layout)

    repaired = initialize_repository(repository, owner_display_name="Owner")

    assert repaired.gitignore_changed is True
    assert gitignore.read_text(encoding="utf-8").count("!/.forge/**") == 2
    assert _is_ignored(repository, "forge.yaml") is False
    assert _is_ignored(repository, ".forge/specific-governed.json") is False
    assert _is_ignored(repository, ".forge/local/secrets/token") is True


def test_doctor_distinguishes_untracked_governed_files_from_integrity(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    _git_repository(repository)
    initialized = initialize_repository(repository, owner_display_name="Owner")

    report = inspect_repository_health(initialized.layout)

    assert any("not tracked by Git" in warning for warning in report.warnings)
    assert any("Git worktree policy" in check for check in report.checks)

    _git(repository, "add", "--", ".gitignore", "forge.yaml")
    tracked = inspect_repository_health(initialized.layout)
    assert not any("not tracked by Git" in warning for warning in tracked.warnings)


def test_doctor_refuses_local_only_files_already_tracked_by_git(tmp_path: Path) -> None:
    repository = tmp_path / "project"
    _git_repository(repository)
    initialized = initialize_repository(repository, owner_display_name="Owner")
    local_file = initialized.layout.local_directory / "should-stay-local.txt"
    local_file.write_text("local-only", encoding="utf-8")
    _git(repository, "add", "--force", "--", ".forge/local/should-stay-local.txt")

    with pytest.raises(IntegrityError, match="already tracks local-only"):
        inspect_repository_health(initialized.layout)

    assert local_file.read_text(encoding="utf-8") == "local-only"
    assert (
        _git(repository, "ls-files", "--", ".forge/local/should-stay-local.txt").stdout.strip()
        != b""
    )


def test_clean_worktree_policy_ignores_local_state_but_not_project_changes(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    _git_repository(repository)
    initialized = initialize_repository(repository, owner_display_name="Owner")
    _git(repository, "add", "--", ".gitignore", "forge.yaml")
    _git(
        repository,
        "-c",
        "user.name=FORGE Test",
        "-c",
        "user.email=forge@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "baseline",
    )
    (initialized.layout.cache_directory / "cache.txt").write_text("cache", encoding="utf-8")

    require_clean_worktree(initialized.layout)

    (repository / "project.txt").write_text("untracked change", encoding="utf-8")
    with pytest.raises(ConflictError, match="requires a clean Git worktree"):
        require_clean_worktree(initialized.layout)


def test_filesystem_only_repository_remains_supported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def not_a_worktree(*_: object, **__: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(["git"], 128, b"", b"not a worktree")

    monkeypatch.setattr(git_policy, "_run_git", not_a_worktree)
    initialized = initialize_repository(tmp_path, owner_display_name="Owner")

    report = inspect_repository_health(initialized.layout)
    git_report = inspect_git_policy(initialized.layout)

    assert git_report.inside_worktree is False
    assert any("filesystem-authoritative" in warning for warning in report.warnings)
    with pytest.raises(ConflictError, match="Cannot verify the configured clean-Git"):
        require_clean_worktree(initialized.layout)
