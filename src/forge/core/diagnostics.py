"""Non-mutating M1 repository diagnostics."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from forge.contracts.state import IntegrityState
from forge.core.agent_protocol import AGENT_PROTOCOL_VERSION
from forge.core.git_policy import inspect_git_policy
from forge.core.local_audit import list_local_audit_events
from forge.core.lock_remediation import validate_lock_remediation_store
from forge.core.status import inspect_status
from forge.errors import IntegrityError
from forge.packs.loader import available_packs
from forge.storage.configuration import load_configuration
from forge.storage.idempotency import validate_idempotency_store
from forge.storage.locking import lock_diagnostic, remediation_lock_diagnostic
from forge.storage.repository import (
    GITIGNORE_RULE,
    RepositoryLayout,
    gitignore_has_hybrid_policy,
)

_PROTOCOL_PREFIX = "agent-protocol-"
_PROTOCOL_SUFFIX = ".md"


@dataclass(frozen=True)
class _RepositoryProtocolSource:
    version: str
    path: Path


@dataclass(frozen=True)
class DiagnosticReport:
    checks: tuple[str, ...]
    warnings: tuple[str, ...]


def _generated_protocol_versions(layout: RepositoryLayout) -> tuple[str, ...]:
    """Return protocol versions the generated agent context currently carries."""
    directory = layout.agent_context_directory
    if not directory.is_dir() or directory.is_symlink():
        return ()
    return tuple(
        sorted(
            path.name[len(_PROTOCOL_PREFIX) : -len(_PROTOCOL_SUFFIX)]
            for path in directory.glob(f"{_PROTOCOL_PREFIX}*{_PROTOCOL_SUFFIX}")
            if path.is_file() and not path.is_symlink()
        )
    )


def _version_key(version: str) -> tuple[int, int, int]:
    core = version.split("-", 1)[0].split("+", 1)[0]
    parts = core.split(".")
    if len(parts) != 3:
        raise ValueError(f"not a semantic version: {version!r}")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def _literal_agent_protocol_version(path: Path) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as error:
        message = f"Cannot inspect repository source protocol version: {error}"
        raise IntegrityError(message) from error
    for node in tree.body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        if (
            isinstance(target, ast.Name)
            and target.id == "AGENT_PROTOCOL_VERSION"
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            return value.value
    return None


def _version_contract_agent_protocol_version(path: Path) -> str | None:
    try:
        loaded: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        message = f"Cannot inspect repository version contract protocol version: {error}"
        raise IntegrityError(message) from error
    if not isinstance(loaded, dict):
        return None
    contract = cast(dict[str, object], loaded)
    persisted = contract.get("persisted_contracts")
    if not isinstance(persisted, dict):
        return None
    persisted_contracts = cast(dict[str, object], persisted)
    version = persisted_contracts.get("agent_protocol_version")
    return version if isinstance(version, str) else None


def _repository_source_protocol_version(
    layout: RepositoryLayout,
) -> _RepositoryProtocolSource | None:
    """Return the protocol version declared by this checkout when it is FORGE source."""
    candidates: list[_RepositoryProtocolSource] = []
    source_constant = layout.root / "src" / "forge" / "core" / "agent_protocol.py"
    if source_constant.is_file() and not source_constant.is_symlink():
        version = _literal_agent_protocol_version(source_constant)
        if version is not None:
            candidates.append(_RepositoryProtocolSource(version, source_constant))
    version_contract = layout.root / "release" / "version-contract.json"
    if version_contract.is_file() and not version_contract.is_symlink():
        version = _version_contract_agent_protocol_version(version_contract)
        if version is not None:
            candidates.append(_RepositoryProtocolSource(version, version_contract))
    if not candidates:
        return None
    versions = {candidate.version for candidate in candidates}
    if len(versions) != 1:
        details = ", ".join(f"{item.path}: {item.version}" for item in candidates)
        raise IntegrityError(
            "Repository source declares conflicting agent protocol versions: "
            f"{details}"
        )
    return candidates[0]


def _protocol_diagnostic(layout: RepositoryLayout) -> tuple[str, str | None]:
    """Compare installed protocol identity against observable repository protocol surfaces.

    Repository source skew is an integrity failure because it means the CLI running
    `doctor` is not the source revision under review. Generated-context skew remains
    a warning: ordinary projects can repair it by regenerating derived context.
    """
    source = _repository_source_protocol_version(layout)
    if source is not None:
        try:
            installed_key = _version_key(AGENT_PROTOCOL_VERSION)
            source_key = _version_key(source.version)
        except ValueError as error:
            raise IntegrityError(f"Cannot compare agent protocol versions: {error}") from error
        if source.version != AGENT_PROTOCOL_VERSION:
            relation = "older than" if installed_key < source_key else "newer than"
            raise IntegrityError(
                f"Installed CLI agent protocol {AGENT_PROTOCOL_VERSION} is {relation} "
                f"repository source protocol {source.version} declared by {source.path}; "
                "install or run the matching FORGE source revision before relying on "
                "doctor, agent protocol, or generated context."
            )
    generated = _generated_protocol_versions(layout)
    if not generated:
        if source is None:
            return (
                f"agent protocol {AGENT_PROTOCOL_VERSION} installed; no repository source "
                "or generated context",
                None,
            )
        return (
            f"agent protocol {AGENT_PROTOCOL_VERSION} matches repository source; "
            "no generated context",
            None,
        )
    if generated == (AGENT_PROTOCOL_VERSION,):
        if source is None:
            return f"agent protocol {AGENT_PROTOCOL_VERSION} matches generated context", None
        return (
            f"agent protocol {AGENT_PROTOCOL_VERSION} matches repository source and "
            "generated context",
            None,
        )
    superseded = tuple(item for item in generated if item != AGENT_PROTOCOL_VERSION)
    remedy = (
        "regenerate it with 'forge agent context --target <codex|claude>', previewing "
        "before you apply"
        if AGENT_PROTOCOL_VERSION not in generated
        else "remove the superseded copy by regenerating with "
        "'forge agent context --target <codex|claude>', previewing before you apply"
    )
    return (
        # The doctor prefixes every check with "OK:", so this line states what ran
        # rather than passing judgement; the warning carries the problem.
        f"agent protocol {AGENT_PROTOCOL_VERSION} checked against the generated context",
        f"Generated agent context still carries protocol {', '.join(superseded)} while the "
        f"installed CLI provides {AGENT_PROTOCOL_VERSION}; an agent reading the stale copy "
        f"follows a superseded contract. To fix, {remedy}.",
    )


def inspect_repository_health(layout: RepositoryLayout) -> DiagnosticReport:
    """Validate implemented storage, pack, archive, and hybrid Git boundaries."""
    configuration = load_configuration(layout.configuration_file)
    packs = available_packs(layout, configuration)
    optional_after_git_checkout = {
        layout.active_directory,
        *(
            path
            for path in layout.required_directories
            if path == layout.local_directory or layout.local_directory in path.parents
        ),
    }
    missing = [
        str(path)
        for path in layout.required_directories
        if not path.is_dir()
        and (
            path not in optional_after_git_checkout
            or path.exists()
            or path.is_symlink()
        )
    ]
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
    remediation_status = remediation_lock_diagnostic(layout)
    if remediation_status is not None:
        warnings = (*warnings, remediation_status)
    protocol_check, protocol_warning = _protocol_diagnostic(layout)
    if protocol_warning is not None:
        warnings = (*warnings, protocol_warning)
    git_report = inspect_git_policy(layout)
    warnings = (*warnings, *git_report.warnings)
    receipt_count = validate_idempotency_store(layout)
    remediation_count = validate_lock_remediation_store(
        layout,
        project_id=configuration.project_id,
        owner_identity_id=configuration.owner.id,
    )
    local_audit_count = len(list_local_audit_events(layout))
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
        f"local stale-lock remediations ({remediation_count})",
        f"local audit events ({local_audit_count})",
        git_check,
        protocol_check,
        "capabilities and adapters (none configured)",
    )
    return DiagnosticReport(checks, warnings)
