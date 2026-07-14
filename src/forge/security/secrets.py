"""Heuristic secret screening for bytes entering governed preservation."""

from __future__ import annotations

import fnmatch
import re

from forge.errors import SecurityError

_RECOGNIZABLE_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,255}\b"),
    re.compile(
        r"(?im)^\s*(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)\s*"
        r"[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"
    ),
)


def _matches_path_pattern(path: str, pattern: str) -> bool:
    normalized_pattern = pattern.replace("\\", "/").lstrip("/")
    if normalized_pattern.endswith("/**"):
        prefix = normalized_pattern.removesuffix("/**").rstrip("/")
        return path == prefix or path.startswith(f"{prefix}/")
    return fnmatch.fnmatchcase(path, normalized_pattern)


def screen_governed_content(
    path: str,
    content: bytes,
    *,
    secret_path_patterns: tuple[str, ...],
) -> None:
    """Block configured secret locations and recognizable high-confidence patterns.

    This is deliberately heuristic defense in depth, not a guarantee that content is safe.
    """
    if path == ".forge" or path.startswith(".forge/"):
        raise SecurityError("FORGE-managed paths cannot be registered as project artifacts")
    matching = next(
        (pattern for pattern in secret_path_patterns if _matches_path_pattern(path, pattern)),
        None,
    )
    if matching is not None:
        raise SecurityError(
            f"Artifact path {path!r} matches configured secret location {matching!r}"
        )
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return
    if any(pattern.search(text) for pattern in _RECOGNIZABLE_SECRET_PATTERNS):
        raise SecurityError(
            f"Artifact {path!r} contains a recognizable credential pattern; secret screening "
            "is heuristic, so review the file and register only a redacted version"
        )
