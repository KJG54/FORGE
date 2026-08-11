"""Single-source Production-v1 version and compatibility consistency review."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import sysconfig
import tomllib
from pathlib import Path
from typing import NoReturn, cast

from typer.main import get_command

from forge import __version__
from forge.cli.app import app
from forge.contracts import CONTRACT_MODELS
from forge.contracts.base import SCHEMA_VERSION
from forge.core.agent_protocol import AGENT_PROTOCOL_DIGEST, AGENT_PROTOCOL_VERSION
from forge.packs.loader import load_pack
from forge.schemas.export import schema_bundle
from forge.storage.migrations import (
    HASH_CHAIN_JOURNAL_FORMAT,
    LEGACY_JOURNAL_FORMAT,
    registered_migrations,
)
from tools.local_candidate import validate_manifest_contract

ROOT = Path(__file__).resolve().parents[1]
VERSION_CONTRACT = ROOT / "release" / "version-contract.json"
INSTALLATION_MATRIX = ROOT / "release" / "installation-matrix.json"
COMPATIBILITY_MANIFEST = ROOT / "tests" / "fixtures" / "compatibility" / "manifest.json"


class VersionConsistencyError(RuntimeError):
    """The current release inputs disagree with the frozen version contract."""


def _fail(message: str) -> NoReturn:
    raise VersionConsistencyError(message)


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail(f"{label} must be a JSON object with text keys")
    untyped = cast("dict[object, object]", value)
    if any(not isinstance(key, str) for key in untyped):
        _fail(f"{label} must be a JSON object with text keys")
    return cast("dict[str, object]", untyped)


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        _fail(f"{label} must be a JSON array")
    return cast("list[object]", value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{label} must be non-empty text")
    return value


def _text_tuple(value: object, label: str) -> tuple[str, ...]:
    return tuple(_text(item, f"{label} item") for item in _array(value, label))


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), label)
    except (OSError, json.JSONDecodeError) as error:
        raise VersionConsistencyError(f"Cannot load {label} at {path}: {error}") from error


def _require_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        _fail(f"{label} differs: expected {expected!r}, found {actual!r}")


def _cli_command_paths() -> tuple[str, ...]:
    pending: list[tuple[str, object]] = [("", get_command(app))]
    paths: list[str] = []
    while pending:
        prefix, command = pending.pop()
        children_value = getattr(command, "commands", None)
        if not isinstance(children_value, dict):
            continue
        children = cast("dict[object, object]", children_value)
        for name, child in children.items():
            if not isinstance(name, str):
                _fail("CLI command names must be text")
            path = f"{prefix} {name}".strip()
            paths.append(path)
            pending.append((path, child))
    return tuple(sorted(paths))


def _default_forge_executable() -> Path:
    executable_name = "forge.exe" if os.name == "nt" else "forge"
    return Path(sysconfig.get_path("scripts")) / executable_name


def _runtime_version(executable: Path) -> str:
    try:
        resolved = executable.resolve(strict=True)
        result = subprocess.run(
            [str(resolved), "--version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            shell=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise VersionConsistencyError(
            f"Cannot run FORGE version command at {executable}: {error}"
        ) from error
    if result.returncode != 0:
        _fail(f"FORGE version command exited with {result.returncode}")
    return result.stdout.strip()


def _pack_contract(
    entries_value: object,
    *,
    bundled: bool,
) -> tuple[tuple[str, str, str], ...]:
    entries = _array(entries_value, "pack contract entries")
    actual: list[tuple[str, str, str]] = []
    for entry_value in entries:
        entry = _object(entry_value, "pack contract entry")
        pack_id = _text(entry.get("id"), "pack id")
        version = _text(entry.get("version"), f"{pack_id} version")
        compatibility = _text(
            entry.get("schema_compatibility"),
            f"{pack_id} schema compatibility",
        )
        root = (
            ROOT / "src" / "forge" / "packs" / "bundled" / pack_id
            if bundled
            else ROOT / "packs" / pack_id
        )
        pack = load_pack(root, bundled=bundled)
        _require_equal(pack.manifest.id, pack_id, f"{pack_id} manifest ID")
        _require_equal(pack.manifest.version, version, f"{pack_id} manifest version")
        _require_equal(
            pack.manifest.schema_compatibility,
            (compatibility,),
            f"{pack_id} schema compatibility",
        )
        if any(workflow.version != version for workflow in pack.workflows):
            _fail(f"{pack_id} workflow versions differ from its manifest version")
        if any(
            workflow.compatibility_constraints != (compatibility,)
            for workflow in pack.workflows
        ):
            _fail(f"{pack_id} workflow compatibility differs from its manifest")
        actual.append((pack_id, version, compatibility))
    return tuple(sorted(actual))


def validate_version_consistency(
    *,
    forge_executable: Path | None = None,
) -> dict[str, object]:
    """Validate every current Production-v1 version boundary against one contract."""
    contract = _load_json(VERSION_CONTRACT, "version contract")
    _require_equal(contract.get("schema_version"), 1, "version contract schema")
    distribution = _object(contract.get("distribution"), "distribution")
    expected_name = _text(distribution.get("name"), "distribution name")
    expected_version = _text(distribution.get("version"), "distribution version")
    import_package = _text(distribution.get("import_package"), "import package")
    console_script = _text(distribution.get("console_script"), "console script")
    expected_entry_point = _text(distribution.get("entry_point"), "entry point")
    wheel_filename = _text(distribution.get("wheel_filename"), "wheel filename")
    sdist_filename = _text(distribution.get("sdist_filename"), "sdist filename")
    normalized_distribution = expected_name.replace("-", "_")
    _require_equal(import_package, "forge", "import package")
    _require_equal(
        wheel_filename,
        f"{normalized_distribution}-{expected_version}-py3-none-any.whl",
        "derived wheel filename",
    )
    _require_equal(
        sdist_filename,
        f"{normalized_distribution}-{expected_version}.tar.gz",
        "derived source-distribution filename",
    )
    _require_equal(
        distribution.get("release_tag"),
        f"v{expected_version}",
        "release tag",
    )

    try:
        pyproject_value = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise VersionConsistencyError(f"Cannot load pyproject.toml: {error}") from error
    project = _object(pyproject_value.get("project"), "pyproject project")
    scripts = _object(project.get("scripts"), "pyproject scripts")
    _require_equal(project.get("name"), expected_name, "package distribution")
    _require_equal(project.get("version"), expected_version, "package version")
    _require_equal(
        scripts.get(console_script),
        expected_entry_point,
        "forge entry point",
    )
    _require_equal(__version__, expected_version, "imported runtime version")
    _require_equal(
        _runtime_version(forge_executable or _default_forge_executable()),
        expected_version,
        "forge --version",
    )

    matrix = _load_json(INSTALLATION_MATRIX, "installation matrix")
    support = _object(contract.get("support"), "support")
    _require_equal(
        matrix.get("python_implementation"),
        support.get("python_implementation"),
        "Python implementation",
    )
    _require_equal(matrix.get("python_versions"), support.get("python_versions"), "Python versions")
    _require_equal(
        tuple(
            _text(_object(item, "operating system").get("id"), "operating system ID")
            for item in _array(matrix.get("operating_systems"), "operating systems")
        ),
        _text_tuple(support.get("operating_systems"), "supported operating systems"),
        "operating systems",
    )
    _require_equal(
        matrix.get("installation_modes"),
        support.get("installation_modes"),
        "installation modes",
    )
    _require_equal(matrix.get("expected_distribution"), expected_name, "matrix distribution")
    _require_equal(matrix.get("expected_version"), expected_version, "matrix version")
    _require_equal(matrix.get("artifact"), "wheel", "matrix artifact type")

    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    if workflow.count(wheel_filename) != 2:
        _fail("CI must reference the exact wheel filename twice")
    installation = (ROOT / "docs" / "installation.md").read_text(encoding="utf-8")
    if wheel_filename not in installation:
        _fail("Installation documentation does not reference the exact wheel filename")
    if expected_version not in installation:
        _fail("Installation documentation does not reference the exact candidate version")

    persisted = _object(contract.get("persisted_contracts"), "persisted contracts")
    _require_equal(
        _text_tuple(persisted.get("schema_versions"), "contract schema versions"),
        (SCHEMA_VERSION,),
        "contract schema versions",
    )
    _require_equal(
        persisted.get("public_model_count"),
        len(CONTRACT_MODELS),
        "public model count",
    )
    _require_equal(
        matrix.get("expected_schema_count"),
        len(CONTRACT_MODELS),
        "matrix schema count",
    )
    # Agents treat the protocol version as a public surface and route themselves by it,
    # so a stale pin here is the same class of defect as a stale installed CLI.
    _require_equal(
        persisted.get("agent_protocol_version"),
        AGENT_PROTOCOL_VERSION,
        "agent protocol version",
    )
    _require_equal(
        persisted.get("agent_protocol_digest"),
        AGENT_PROTOCOL_DIGEST,
        "agent protocol digest",
    )
    compatibility = _text(
        persisted.get("pack_schema_compatibility"),
        "pack schema compatibility",
    )
    index = _object(
        json.loads(schema_bundle()["index.json"].decode("utf-8")),
        "schema index",
    )
    _require_equal(index.get("forge_version"), expected_version, "schema index version")
    _require_equal(index.get("schema_version"), SCHEMA_VERSION, "schema index contract version")
    _require_equal(
        index.get("pack_schema_compatibility"),
        compatibility,
        "schema index pack compatibility",
    )
    _require_equal(
        set(_object(index.get("schemas"), "schema index files")),
        set(CONTRACT_MODELS),
        "schema index model set",
    )

    compatibility_manifest = _load_json(COMPATIBILITY_MANIFEST, "compatibility manifest")
    _require_equal(
        tuple(
            _text(_object(item, "schema entry").get("schema_version"), "schema version")
            for item in _array(
                compatibility_manifest.get("contract_schema_versions"),
                "compatibility schema versions",
            )
        ),
        (SCHEMA_VERSION,),
        "compatibility manifest schema versions",
    )
    journal_entries = {
        _text(entry.get("id"), "journal format ID"): entry
        for entry in (
            _object(item, "journal format")
            for item in _array(persisted.get("journal_formats"), "journal formats")
        )
    }
    _require_equal(
        set(journal_entries),
        {LEGACY_JOURNAL_FORMAT, HASH_CHAIN_JOURNAL_FORMAT},
        "journal format set",
    )
    _require_equal(
        {
            _text(entry.get("migration_id"), "migration ID")
            for entry in journal_entries.values()
            if entry.get("migration_id") is not None
        },
        {migration.id for migration in registered_migrations()},
        "migration registry",
    )

    packs = _object(contract.get("packs"), "packs")
    bundled = _pack_contract(packs.get("bundled"), bundled=True)
    repository_local = _pack_contract(packs.get("repository_local"), bundled=False)
    _require_equal(
        _text_tuple(matrix.get("expected_bundled_packs"), "matrix bundled packs"),
        tuple(item[0] for item in bundled),
        "matrix bundled packs",
    )
    _require_equal(
        _text_tuple(contract.get("public_python_surface"), "public Python surface"),
        ("forge.__version__", "forge.contracts", "forge.schemas"),
        "public Python surface",
    )
    _require_equal(
        _cli_command_paths(),
        _text_tuple(contract.get("cli_command_paths"), "CLI command paths"),
        "CLI command paths",
    )

    publication = _object(contract.get("publication_metadata"), "publication metadata")
    classifiers = _text_tuple(project.get("classifiers"), "project classifiers")
    _require_equal(
        publication.get("development_status_classifier") in classifiers,
        True,
        "development-status classifier",
    )
    urls_complete = publication.get("project_urls_complete")
    _require_equal(isinstance(project.get("urls"), dict), urls_complete, "project URL completeness")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    dated_complete = publication.get("dated_changelog_section_complete")
    _require_equal("## [1.0.0]" in changelog, dated_complete, "dated changelog completeness")
    _require_equal(
        publication.get("status"),
        "not-authorized-local-candidate",
        "publication metadata status",
    )
    _require_equal(
        publication.get("public_publication_authorized"),
        False,
        "public publication authorization",
    )
    _require_equal(publication.get("release_tag_created"), False, "release tag state")

    local_candidate = _object(contract.get("local_candidate"), "local candidate")
    _require_equal(
        local_candidate.get("status"),
        "unpublished-local-candidate",
        "local candidate status",
    )
    _require_equal(
        local_candidate.get("downstream_installation_artifact"),
        "wheel",
        "local candidate downstream artifact",
    )
    _require_equal(local_candidate.get("integration_increment"), "L8", "integration increment")
    _require_equal(local_candidate.get("validation_increment"), "L9", "validation increment")
    manifest = validate_manifest_contract()
    _require_equal(manifest.get("distribution"), expected_name, "candidate distribution")
    _require_equal(manifest.get("version"), expected_version, "candidate version")

    return {
        "schema_version": 1,
        "status": "passed",
        "distribution": expected_name,
        "version": expected_version,
        "wheel_filename": wheel_filename,
        "sdist_filename": sdist_filename,
        "contract_schema_version": SCHEMA_VERSION,
        "public_model_count": len(CONTRACT_MODELS),
        "agent_protocol_version": AGENT_PROTOCOL_VERSION,
        "cli_command_count": len(_cli_command_paths()),
        "bundled_packs": [item[0] for item in bundled],
        "repository_local_packs": [item[0] for item in repository_local],
        "publication_metadata_status": publication.get("status"),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the frozen Production-v1 version and compatibility contract."
    )
    parser.add_argument("--forge", type=Path, help="Exact forge console executable to inspect.")
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        report = validate_version_consistency(forge_executable=arguments.forge)
    except (OSError, VersionConsistencyError) as error:
        print(f"version consistency failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
