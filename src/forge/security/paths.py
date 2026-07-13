"""Cross-platform repository-boundary checks for governed paths."""

from pathlib import Path

from forge.contracts.base import validate_repository_relative_path
from forge.errors import SecurityError


def normalize_repository_path(value: str) -> str:
    """Return the portable form of a safe lexical repository-relative path."""
    try:
        return validate_repository_relative_path(value)
    except (TypeError, ValueError) as error:
        raise SecurityError(f"Unsafe repository path {value!r}: {error}") from error


def resolve_repository_path(
    repository_root: Path,
    relative_path: str,
    *,
    must_exist: bool = False,
) -> Path:
    """Resolve a governed path and reject traversal or symlink escape."""
    try:
        root = repository_root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise SecurityError(
            f"Repository root cannot be resolved safely: {repository_root}"
        ) from error
    if not root.is_dir():
        raise SecurityError(f"Repository root is not a directory: {root}")

    normalized = normalize_repository_path(relative_path)
    lexical_target = root.joinpath(*normalized.split("/"))
    try:
        resolved_target = lexical_target.resolve(strict=must_exist)
    except (OSError, RuntimeError) as error:
        raise SecurityError(f"Governed path cannot be resolved safely: {normalized}") from error

    if not resolved_target.is_relative_to(root):
        raise SecurityError(
            f"Governed path escapes the repository through traversal or a symlink: {normalized}"
        )
    return resolved_target
