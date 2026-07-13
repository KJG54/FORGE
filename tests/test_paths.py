import os
from pathlib import Path

import pytest

from forge.errors import SecurityError
from forge.security.paths import normalize_repository_path, resolve_repository_path


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("docs/report.md", "docs/report.md"),
        (r"docs\report.md", "docs/report.md"),
        (".forge/active/state.json", ".forge/active/state.json"),
    ],
)
def test_repository_paths_are_portably_normalized(source: str, expected: str) -> None:
    assert normalize_repository_path(source) == expected


@pytest.mark.parametrize(
    "unsafe",
    ["", ".", "../outside", "docs/../../outside", "/absolute", r"C:\absolute", r"\\server\share"],
)
def test_repository_paths_reject_absolute_and_traversing_forms(unsafe: str) -> None:
    with pytest.raises(SecurityError):
        normalize_repository_path(unsafe)


def test_resolved_path_must_remain_within_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    target = repository / "docs" / "report.md"
    target.parent.mkdir()
    target.write_text("evidence", encoding="utf-8")

    assert resolve_repository_path(repository, "docs/report.md", must_exist=True) == target


def test_symlink_escape_is_rejected_when_platform_allows_symlinks(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    outside = tmp_path / "outside"
    repository.mkdir()
    outside.mkdir()
    link = repository / "escape"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")

    with pytest.raises(SecurityError, match="escapes the repository"):
        resolve_repository_path(repository, "escape/result.txt")
