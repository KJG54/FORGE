"""Non-mutating M1 repository diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

from forge.contracts.state import IntegrityState
from forge.core.git_policy import inspect_git_policy
from forge.core.status import inspect_status
from forge.errors import IntegrityError
from forge.packs.loader import available_packs
from forge.storage.configuration import load_configuration
from forge.storage.idempotency import validate_idempotency_store
from forge.storage.locking import lock_diagnostic
from forge.storage.repository import (
    GITIGNORE_RULE,
    RepositoryLayout,
    gitignore_has_hybrid_policy,
)


@dataclass(frozen=True)
class DiagnosticReport:
    checks: tuple[str, ...]
    warnings: tuple[str, ...]


def inspect_repository_health(layout: RepositoryLayout) -> DiagnosticReport:
    """Validate implemented storage, pack, archive, and hybrid Git boundaries."""
    configuration = load_configuration(layout.configuration_file)
    packs = available_packs(layout, configuration)
    missing = [str(path) for path in layout.required_directories if not path.is_dir()]
    if missing:
        raise IntegrityError(
            f"Required FORGE directories are missing: {missing}; rerun 'forge init'"
        )
    status = inspect_status(layout)
    if status.integrity_state is not IntegrityState.HEALTHY:
        details = "; ".join(status.blockers) or "unknown repository integrity error"
        raise IntegrityError(f"Repository health validation failed: {details}")
    gitignore = layout.root / ".gitignore"
    try:
        gitignore_content = gitignore.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read Git policy file {gitignore}: {error}") from error
    if gitignore.is_symlink() or not gitignore_has_hybrid_policy(gitignore_content):
        raise IntegrityError(
            "Git policy does not preserve governed FORGE paths while ignoring "
            f"{GITIGNORE_RULE}; rerun 'forge init'"
        )
    warnings = tuple(
        blocker
        for blocker in status.blockers
        if blocker.startswith("Working copy changed for artifact")
    )
    lock_status = lock_diagnostic(layout)
    if lock_status is not None:
        warnings = (*warnings, lock_status)
    git_report = inspect_git_policy(layout)
    warnings = (*warnings, *git_report.warnings)
    receipt_count = validate_idempotency_store(layout)
    git_check = (
        f"Git worktree policy ({git_report.tracked_governed_count} tracked governed files)"
        if git_report.inside_worktree
        else f"filesystem-only Git policy ({GITIGNORE_RULE} ignored)"
    )
    checks = (
        f"configuration schema {configuration.schema_version}",
        f"repository layout ({len(layout.required_directories)} managed directories)",
        f"validated data packs ({len(packs)})",
        "journal, snapshot, locked workflow, and governed records",
        f"archives ({len(status.archived_initiative_ids)})",
        f"idempotency receipts ({receipt_count})",
        git_check,
        "capabilities and adapters (none configured)",
    )
    return DiagnosticReport(checks, warnings)
