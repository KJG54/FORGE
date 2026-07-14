"""Non-mutating M1 repository diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forge.contracts.state import IntegrityState
from forge.core.status import inspect_status
from forge.errors import IntegrityError
from forge.packs.loader import available_packs
from forge.storage.configuration import load_configuration
from forge.storage.locking import lock_diagnostic
from forge.storage.repository import GITIGNORE_RULE, RepositoryLayout


@dataclass(frozen=True)
class DiagnosticReport:
    checks: tuple[str, ...]
    warnings: tuple[str, ...]


def _gitignore_protects_local_state(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    accepted = {".forge/local", ".forge/local/", ".forge/local/**"}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    return any(line.strip().lstrip("/") in accepted for line in lines)


def inspect_repository_health(layout: RepositoryLayout) -> DiagnosticReport:
    """Validate implemented M1 storage, pack, archive, and Git policy boundaries."""
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
    if not _gitignore_protects_local_state(gitignore):
        raise IntegrityError(
            f"Git policy does not ignore {GITIGNORE_RULE}; rerun 'forge init'"
        )
    warnings = tuple(
        blocker
        for blocker in status.blockers
        if blocker.startswith("Working copy changed for artifact")
    )
    lock_status = lock_diagnostic(layout)
    if lock_status is not None:
        warnings = (*warnings, lock_status)
    checks = (
        f"configuration schema {configuration.schema_version}",
        f"repository layout ({len(layout.required_directories)} managed directories)",
        f"validated data packs ({len(packs)})",
        "journal, snapshot, locked workflow, and governed records",
        f"archives ({len(status.archived_initiative_ids)})",
        f"Git policy ({GITIGNORE_RULE})",
        "capabilities and adapters (none configured)",
    )
    return DiagnosticReport(checks, warnings)
