"""Bounded, read-only filesystem path discovery for agent-context review."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from uuid import UUID

from forge.contracts.artifacts import ArtifactRecord, ArtifactRevision
from forge.core.artifacts import assert_working_revision_current
from forge.core.lifecycle import ActiveInitiative, load_active_initiative
from forge.core.scope_amendments import effective_scope_summary
from forge.errors import ConfigurationError, ConflictError, IntegrityError
from forge.security.paths import normalize_repository_path
from forge.security.secrets import matching_secret_path_pattern
from forge.storage.configuration import load_configuration
from forge.storage.records import load_record
from forge.storage.repository import RepositoryLayout

CONTEXT_DISCOVERY_PROFILE = "bounded-path-v1"
MAX_DISCOVERY_DEPTH = 8
MAX_DIRECTORY_ENTRIES = 2_000
MAX_INSPECTED_FILES = 4_000
MAX_DISCOVERY_CANDIDATES = 32
MAX_DISCOVERY_FILE_BYTES = 1_048_576
MAX_DISCOVERY_TOTAL_BYTES = 10_485_760
MAX_DISCOVERY_PATH_LENGTH = 512
GIT_DISCOVERY_TIMEOUT_SECONDS = 10

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "accepted",
    "active",
    "after",
    "against",
    "and",
    "before",
    "complete",
    "context",
    "current",
    "declared",
    "define",
    "from",
    "into",
    "only",
    "output",
    "outputs",
    "produce",
    "project",
    "required",
    "step",
    "that",
    "the",
    "this",
    "within",
    "with",
    "work",
}
_DISCOVERABLE_SUFFIXES = {
    ".adoc",
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".csv",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".py",
    ".rb",
    ".rs",
    ".rst",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
_DISCOVERABLE_EXTENSIONLESS_NAMES = {"readme"}
_EXCLUDED_DIRECTORY_NAMES = {
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "target",
    "venv",
}
_EXCLUDED_CONTROL_FILES = {
    ".gitignore",
    "agents.md",
    "claude.md",
    "forge.yaml",
}


class ContextSufficiencyStatus(StrEnum):
    """Structural result of one bounded discovery pass."""

    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class ContextDiscoveryCandidate:
    """One bounded path suggestion; content is never embedded or authorized."""

    path: str
    byte_size: int
    score: int
    matched_terms: tuple[str, ...]
    registered_roles: tuple[str, ...]
    current_required_input: bool


@dataclass(frozen=True)
class ContextDiscoveryReport:
    """Disposable measurement and ranked path suggestions for one active step."""

    profile: str
    step_id: str
    selection_terms: tuple[str, ...]
    candidates: tuple[ContextDiscoveryCandidate, ...]
    inspected_file_count: int
    eligible_file_count: int
    ignored_file_count: int
    policy_excluded_count: int
    symlink_excluded_count: int
    oversized_file_count: int
    unsupported_file_count: int
    required_input_roles: tuple[str, ...]
    covered_required_input_roles: tuple[str, ...]
    current_required_input_roles: tuple[str, ...]
    ignore_policy_enforced: bool
    inventory_truncated: bool
    candidate_budget_exhausted: bool
    sufficiency_status: ContextSufficiencyStatus
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]

    @property
    def required_input_coverage(self) -> float:
        if not self.required_input_roles:
            return 1.0
        return len(self.current_required_input_roles) / len(self.required_input_roles)


@dataclass(frozen=True)
class ContextDiscoveryMeasurement:
    """Ground-truth evaluation used to decide whether bounded discovery is enough."""

    expected_paths: tuple[str, ...]
    discovered_paths: tuple[str, ...]
    matched_paths: tuple[str, ...]
    missed_paths: tuple[str, ...]
    unexpected_paths: tuple[str, ...]
    precision: float
    recall: float
    minimum_precision: float
    minimum_recall: float
    sufficient: bool


@dataclass(frozen=True)
class _ObservedPath:
    path: str
    byte_size: int


def _empty_warnings() -> list[str]:
    return []


@dataclass
class _Inventory:
    paths: list[_ObservedPath]
    inspected_file_count: int = 0
    policy_excluded_count: int = 0
    symlink_excluded_count: int = 0
    oversized_file_count: int = 0
    unsupported_file_count: int = 0
    truncated: bool = False
    warnings: list[str] = field(default_factory=_empty_warnings)


@dataclass(frozen=True)
class _RegisteredPath:
    role: str
    current_required_input: bool


def _tokens(*values: str) -> tuple[str, ...]:
    selected: set[str] = set()
    for value in values:
        for match in _TOKEN_PATTERN.finditer(value[:8_192].lower()):
            token = match.group(0)
            if len(token) >= 3 and token not in _STOP_WORDS:
                selected.add(token)
            if len(selected) >= 64:
                break
        if len(selected) >= 64:
            break
    return tuple(sorted(selected))


def _is_discoverable_file(path: Path) -> bool:
    return (
        path.suffix.lower() in _DISCOVERABLE_SUFFIXES
        or path.name.lower() in _DISCOVERABLE_EXTENSIONLESS_NAMES
    )


def _directory_is_excluded(name: str) -> bool:
    lowered = name.lower()
    return (
        name.startswith(".")
        or lowered in _EXCLUDED_DIRECTORY_NAMES
        or lowered.endswith((".egg-info", ".dist-info"))
    )


def _scan_repository(
    layout: RepositoryLayout,
    *,
    secret_path_patterns: tuple[str, ...],
) -> _Inventory:
    inventory = _Inventory(paths=[])
    stack: list[tuple[Path, int]] = [(layout.root, 0)]
    stop = False
    while stack and not stop:
        directory, depth = stack.pop()
        try:
            entries: list[os.DirEntry[str]] = []
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    if len(entries) >= MAX_DIRECTORY_ENTRIES:
                        inventory.truncated = True
                        relative = directory.relative_to(layout.root).as_posix() or "."
                        inventory.warnings.append(
                            f"Directory entry limit reached at {relative}"
                        )
                        break
                    entries.append(entry)
        except OSError as error:
            inventory.truncated = True
            relative = directory.relative_to(layout.root).as_posix() or "."
            inventory.warnings.append(f"Cannot inspect {relative}: {error}")
            continue

        child_directories: list[Path] = []
        for entry in sorted(entries, key=lambda item: item.name.casefold()):
            candidate = Path(entry.path)
            relative = candidate.relative_to(layout.root).as_posix()
            if len(relative) > MAX_DISCOVERY_PATH_LENGTH:
                inventory.policy_excluded_count += 1
                continue
            try:
                if entry.is_symlink():
                    inventory.symlink_excluded_count += 1
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if _directory_is_excluded(entry.name):
                        inventory.policy_excluded_count += 1
                        continue
                    if matching_secret_path_pattern(relative, secret_path_patterns) is not None:
                        inventory.policy_excluded_count += 1
                        continue
                    if depth >= MAX_DISCOVERY_DEPTH:
                        inventory.truncated = True
                        inventory.warnings.append(
                            f"Discovery depth limit reached at {relative}"
                        )
                        continue
                    child_directories.append(candidate)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    inventory.policy_excluded_count += 1
                    continue
            except OSError as error:
                inventory.truncated = True
                inventory.warnings.append(f"Cannot classify {relative}: {error}")
                continue

            if inventory.inspected_file_count >= MAX_INSPECTED_FILES:
                inventory.truncated = True
                inventory.warnings.append("Repository file inspection limit reached")
                stop = True
                break
            inventory.inspected_file_count += 1
            if (
                entry.name.startswith(".")
                or entry.name.casefold() in _EXCLUDED_CONTROL_FILES
            ):
                inventory.policy_excluded_count += 1
                continue
            if matching_secret_path_pattern(relative, secret_path_patterns) is not None:
                inventory.policy_excluded_count += 1
                continue
            if not _is_discoverable_file(candidate):
                inventory.unsupported_file_count += 1
                continue
            try:
                byte_size = entry.stat(follow_symlinks=False).st_size
            except OSError as error:
                inventory.truncated = True
                inventory.warnings.append(f"Cannot inspect size for {relative}: {error}")
                continue
            if byte_size > MAX_DISCOVERY_FILE_BYTES:
                inventory.oversized_file_count += 1
                continue
            inventory.paths.append(_ObservedPath(relative, byte_size))

        for child in reversed(child_directories):
            stack.append((child, depth + 1))
    return inventory


def _git_ignored_paths(
    layout: RepositoryLayout,
    paths: tuple[str, ...],
) -> tuple[set[str], bool, str | None]:
    try:
        probe = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=layout.root,
            capture_output=True,
            check=False,
            timeout=GIT_DISCOVERY_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return set(), False, "Git is unavailable; unregistered path suggestions are withheld"
    except (OSError, subprocess.TimeoutExpired) as error:
        return set(), False, f"Git ignore inspection is unavailable: {error}"
    if probe.returncode != 0 or probe.stdout.strip() != b"true":
        return (
            set(),
            False,
            "Repository is not in a Git worktree; unregistered path suggestions are withheld",
        )
    if not paths:
        return set(), True, None
    payload = b"\0".join(path.encode("utf-8") for path in paths) + b"\0"
    try:
        completed = subprocess.run(
            ["git", "check-ignore", "-z", "--stdin"],
            cwd=layout.root,
            input=payload,
            capture_output=True,
            check=False,
            timeout=GIT_DISCOVERY_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return set(), False, f"Git ignore inspection failed: {error}"
    if completed.returncode not in {0, 1}:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        return set(), False, f"Git ignore inspection failed{suffix}"
    ignored = {
        item.decode("utf-8", errors="strict")
        for item in completed.stdout.split(b"\0")
        if item
    }
    return ignored, True, None


def _selection_terms(active: ActiveInitiative, step_id: str) -> tuple[str, ...]:
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise IntegrityError(f"Current workflow step {step_id!r} is missing from its lock")
    return _tokens(
        active.initiative.objective,
        effective_scope_summary(active),
        step.id,
        step.purpose,
        step.instructions,
        *step.context_selection_rules,
        *step.required_inputs,
        *step.required_outputs,
    )


def _registered_paths(
    active: ActiveInitiative,
    *,
    required_roles: tuple[str, ...],
) -> tuple[dict[str, list[_RegisteredPath]], tuple[str, ...], tuple[str, ...], list[str]]:
    revisions: dict[tuple[UUID, int], ArtifactRevision] = {}
    for path in active.layout.artifact_revision_directory.glob("*.json"):
        revision = load_record(path, ArtifactRevision)
        key = (revision.artifact_id, revision.revision_number)
        if key in revisions:
            raise IntegrityError(
                f"Artifact {revision.artifact_id} revision {revision.revision_number} "
                "has duplicate records"
            )
        revisions[key] = revision

    registered: dict[str, list[_RegisteredPath]] = {}
    covered_roles: set[str] = set()
    current_roles: set[str] = set()
    warnings: list[str] = []
    for artifact_id, revision_number in sorted(
        active.state.current_artifact_revisions.items(),
        key=lambda item: str(item[0]),
    ):
        record = load_record(
            active.layout.artifact_record_directory / f"{artifact_id}.{revision_number}.json",
            ArtifactRecord,
        )
        revision = revisions.get((artifact_id, revision_number))
        if revision is None:
            raise IntegrityError(
                f"Artifact {artifact_id} current revision {revision_number} is missing"
            )
        current_required = False
        if record.role in required_roles:
            covered_roles.add(record.role)
            try:
                assert_working_revision_current(active.layout, revision)
            except ConflictError as error:
                warnings.append(str(error))
            else:
                current_roles.add(record.role)
                current_required = True
        registered.setdefault(revision.path, []).append(
            _RegisteredPath(
                role=record.role,
                current_required_input=current_required,
            )
        )
    return (
        registered,
        tuple(role for role in required_roles if role in covered_roles),
        tuple(role for role in required_roles if role in current_roles),
        warnings,
    )


def discover_context(
    layout: RepositoryLayout,
    *,
    max_candidates: int = MAX_DISCOVERY_CANDIDATES,
) -> ContextDiscoveryReport:
    """Return bounded path suggestions without reading or authorizing file content."""

    if max_candidates < 1 or max_candidates > MAX_DISCOVERY_CANDIDATES:
        raise ConfigurationError(
            f"Context discovery candidate limit must be between 1 and "
            f"{MAX_DISCOVERY_CANDIDATES}"
        )
    active = load_active_initiative(layout, allow_paused=True)
    step_id = active.state.current_step_id
    if step_id is None:
        raise ConfigurationError("Active initiative has no current step for context discovery")
    step = next((item for item in active.workflow.steps if item.id == step_id), None)
    if step is None:
        raise IntegrityError(f"Current workflow step {step_id!r} is missing from its lock")
    terms = _selection_terms(active, step_id)
    configuration = load_configuration(layout.configuration_file)
    inventory = _scan_repository(
        layout,
        secret_path_patterns=configuration.security.secret_path_patterns,
    )
    required_roles = tuple(step.required_inputs)
    registered, covered_roles, current_roles, required_warnings = _registered_paths(
        active,
        required_roles=required_roles,
    )

    inventory_paths = tuple(item.path for item in inventory.paths)
    ignored, ignore_enforced, ignore_warning = _git_ignored_paths(layout, inventory_paths)
    warnings = [*inventory.warnings, *required_warnings]
    if ignore_warning is not None:
        warnings.append(ignore_warning)

    ranked: list[ContextDiscoveryCandidate] = []
    eligible_count = 0
    ignored_count = 0
    for observation in inventory.paths:
        path = observation.path
        registrations = registered.get(path, [])
        is_registered = bool(registrations)
        if path in ignored and not is_registered:
            ignored_count += 1
            continue
        if not ignore_enforced and not is_registered:
            continue
        eligible_count += 1
        path_terms = set(_tokens(Path(path).stem))
        matched_terms = tuple(sorted(path_terms.intersection(terms)))
        registered_roles = tuple(sorted({item.role for item in registrations}))
        current_required = any(item.current_required_input for item in registrations)
        if not matched_terms and not current_required:
            continue
        score = len(matched_terms) * 10
        if is_registered:
            score += 100
        if current_required:
            score += 1_000
        ranked.append(
            ContextDiscoveryCandidate(
                path=path,
                byte_size=observation.byte_size,
                score=score,
                matched_terms=matched_terms,
                registered_roles=registered_roles,
                current_required_input=current_required,
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.path.casefold(), item.path))
    selected: list[ContextDiscoveryCandidate] = []
    total_bytes = 0
    budget_exhausted = False
    for candidate in ranked:
        if len(selected) >= max_candidates:
            budget_exhausted = True
            break
        if total_bytes + candidate.byte_size > MAX_DISCOVERY_TOTAL_BYTES:
            budget_exhausted = True
            continue
        selected.append(candidate)
        total_bytes += candidate.byte_size

    if len(current_roles) != len(required_roles):
        sufficiency = ContextSufficiencyStatus.INSUFFICIENT
    elif not ignore_enforced:
        sufficiency = ContextSufficiencyStatus.INDETERMINATE
    elif inventory.truncated or budget_exhausted:
        sufficiency = ContextSufficiencyStatus.INSUFFICIENT
    else:
        sufficiency = ContextSufficiencyStatus.SUFFICIENT

    return ContextDiscoveryReport(
        profile=CONTEXT_DISCOVERY_PROFILE,
        step_id=step_id,
        selection_terms=terms,
        candidates=tuple(selected),
        inspected_file_count=inventory.inspected_file_count,
        eligible_file_count=eligible_count,
        ignored_file_count=ignored_count,
        policy_excluded_count=inventory.policy_excluded_count,
        symlink_excluded_count=inventory.symlink_excluded_count,
        oversized_file_count=inventory.oversized_file_count,
        unsupported_file_count=inventory.unsupported_file_count,
        required_input_roles=required_roles,
        covered_required_input_roles=covered_roles,
        current_required_input_roles=current_roles,
        ignore_policy_enforced=ignore_enforced,
        inventory_truncated=inventory.truncated,
        candidate_budget_exhausted=budget_exhausted,
        sufficiency_status=sufficiency,
        warnings=tuple(warnings),
        limitations=(
            "Discovery uses bounded path metadata and lexical terms; it does not read file content "
            "or establish semantic relevance, completeness, quality, currency, or factual truth.",
            "Candidates are suggestions only and do not register artifacts, grant worker access, "
            "change canonical context, create evidence, verify work, or record acceptance.",
            "SQLite FTS, semantic retrieval, repository indexing, and external lookup are not "
            "used.",
        ),
    )


def measure_discovery_sufficiency(
    report: ContextDiscoveryReport,
    *,
    expected_relevant_paths: tuple[str, ...],
    minimum_precision: float = 0.5,
    minimum_recall: float = 1.0,
) -> ContextDiscoveryMeasurement:
    """Compare one report with explicit scenario ground truth."""

    if not 0 <= minimum_precision <= 1 or not 0 <= minimum_recall <= 1:
        raise ConfigurationError("Discovery measurement thresholds must be between 0 and 1")
    expected = tuple(sorted({normalize_repository_path(item) for item in expected_relevant_paths}))
    discovered = tuple(sorted({item.path for item in report.candidates}))
    expected_set = set(expected)
    discovered_set = set(discovered)
    matched = tuple(sorted(expected_set.intersection(discovered_set)))
    missed = tuple(sorted(expected_set.difference(discovered_set)))
    unexpected = tuple(sorted(discovered_set.difference(expected_set)))
    precision = len(matched) / len(discovered) if discovered else float(not expected)
    recall = len(matched) / len(expected) if expected else 1.0
    sufficient = (
        report.sufficiency_status is ContextSufficiencyStatus.SUFFICIENT
        and precision >= minimum_precision
        and recall >= minimum_recall
    )
    return ContextDiscoveryMeasurement(
        expected_paths=expected,
        discovered_paths=discovered,
        matched_paths=matched,
        missed_paths=missed,
        unexpected_paths=unexpected,
        precision=precision,
        recall=recall,
        minimum_precision=minimum_precision,
        minimum_recall=minimum_recall,
        sufficient=sufficient,
    )
