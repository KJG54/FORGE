"""Reproducible M6 dependency, license, vulnerability, and secret review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from importlib.metadata import Distribution, PackageNotFoundError, distribution
from pathlib import Path
from typing import cast

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "release" / "security-review-policy.json"
DEFAULT_GITLEAKS_IGNORE = ROOT / ".gitleaksignore"
MAX_SNAPSHOT_FILE_BYTES = 5 * 1024 * 1024
MAX_SNAPSHOT_TOTAL_BYTES = 50 * 1024 * 1024

_FINGERPRINT = re.compile(
    r"^[0-9a-f]{40}:[^:\r\n]+:[a-z0-9-]+:[1-9][0-9]*$"
)
_CLASSIFIER_LICENSES = {
    "License :: OSI Approved :: Apache Software License": "Apache-2.0",
    "License :: OSI Approved :: ISC License (ISCL)": "ISC",
    "License :: OSI Approved :: MIT License": "MIT",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
}
_LEGACY_LICENSES = {
    "ISC License": "ISC",
    "MIT": "MIT",
}


class ReviewError(RuntimeError):
    """Fail-closed release security review error."""


@dataclass(frozen=True)
class LicenseOverride:
    version: str
    expression: str
    license_file: str
    license_file_sha256: str
    reason: str


@dataclass(frozen=True)
class ReviewPolicy:
    project_name: str
    direct_requirements: dict[str, tuple[str, ...]]
    allowed_license_expressions: frozenset[str]
    license_overrides: dict[str, LicenseOverride]
    minimum_tool_versions: dict[str, str]
    secret_history_exceptions: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class PackageReview:
    name: str
    version: str
    license_expression: str
    license_source: str


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ReviewError(f"{label} must be a JSON object with string keys")
    untyped = cast("dict[object, object]", value)
    if any(not isinstance(key, str) for key in untyped):
        raise ReviewError(f"{label} must be a JSON object with string keys")
    return cast("dict[str, object]", value)


def _exact_keys(value: dict[str, object], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ReviewError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewError(f"{label} must be non-empty text")
    return value


def _text_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ReviewError(f"{label} must be a JSON array")
    items = cast("list[object]", value)
    result = tuple(_text(item, f"{label} item") for item in items)
    if len(result) != len(set(result)):
        raise ReviewError(f"{label} must not contain duplicates")
    return result


def load_policy(path: Path = DEFAULT_POLICY) -> ReviewPolicy:
    """Load a strict machine-readable release security policy."""

    try:
        raw = path.read_bytes()
        document = _object(json.loads(raw), "security review policy")
    except (OSError, json.JSONDecodeError) as error:
        raise ReviewError(f"Cannot load security review policy {path}: {error}") from error
    _exact_keys(
        document,
        {
            "schema_version",
            "project_name",
            "direct_requirements",
            "allowed_license_expressions",
            "license_overrides",
            "minimum_tool_versions",
            "secret_history_exceptions",
        },
        "security review policy",
    )
    if document["schema_version"] != 1:
        raise ReviewError("Security review policy schema_version must equal 1")

    direct_document = _object(document["direct_requirements"], "direct_requirements")
    _exact_keys(direct_document, {"build", "runtime", "development"}, "direct_requirements")
    direct_requirements = {
        scope: _text_tuple(direct_document[scope], f"direct_requirements.{scope}")
        for scope in ("build", "runtime", "development")
    }

    override_document = _object(document["license_overrides"], "license_overrides")
    overrides: dict[str, LicenseOverride] = {}
    for raw_name, raw_override in override_document.items():
        name = canonicalize_name(raw_name)
        value = _object(raw_override, f"license_overrides.{raw_name}")
        _exact_keys(
            value,
            {
                "version",
                "expression",
                "license_file",
                "license_file_sha256",
                "reason",
            },
            f"license_overrides.{raw_name}",
        )
        digest = _text(
            value["license_file_sha256"],
            f"license_overrides.{raw_name}.license_file_sha256",
        )
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ReviewError(f"License override digest is invalid for {raw_name}")
        overrides[name] = LicenseOverride(
            version=_text(value["version"], f"license_overrides.{raw_name}.version"),
            expression=_text(
                value["expression"],
                f"license_overrides.{raw_name}.expression",
            ),
            license_file=_text(
                value["license_file"],
                f"license_overrides.{raw_name}.license_file",
            ),
            license_file_sha256=digest,
            reason=_text(value["reason"], f"license_overrides.{raw_name}.reason"),
        )

    tool_document = _object(document["minimum_tool_versions"], "minimum_tool_versions")
    _exact_keys(tool_document, {"gitleaks", "pip-audit"}, "minimum_tool_versions")
    tool_versions = {
        name: _text(tool_document[name], f"minimum_tool_versions.{name}")
        for name in ("gitleaks", "pip-audit")
    }

    exceptions = _text_tuple(
        document["secret_history_exceptions"],
        "secret_history_exceptions",
    )
    if any(_FINGERPRINT.fullmatch(item) is None for item in exceptions):
        raise ReviewError("Every secret history exception must be one exact Gitleaks fingerprint")

    allowed = frozenset(
        _text_tuple(
            document["allowed_license_expressions"],
            "allowed_license_expressions",
        )
    )
    if not allowed:
        raise ReviewError("At least one license expression must be allowed")
    if any(item.expression not in allowed for item in overrides.values()):
        raise ReviewError("Every license override expression must be explicitly allowed")

    return ReviewPolicy(
        project_name=_text(document["project_name"], "project_name"),
        direct_requirements=direct_requirements,
        allowed_license_expressions=allowed,
        license_overrides=overrides,
        minimum_tool_versions=tool_versions,
        secret_history_exceptions=exceptions,
        digest=f"sha256:{hashlib.sha256(raw).hexdigest()}",
    )


def project_requirements(root: Path = ROOT) -> tuple[str, dict[str, tuple[str, ...]]]:
    """Return the project name and exact declared build/runtime/development requirements."""

    try:
        document = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        build = cast("dict[str, object]", document["build-system"])
        project = cast("dict[str, object]", document["project"])
        optional = cast("dict[str, object]", project["optional-dependencies"])
        name = cast(str, project["name"])
        requirements = {
            "build": tuple(cast("list[str]", build["requires"])),
            "runtime": tuple(cast("list[str]", project["dependencies"])),
            "development": tuple(cast("list[str]", optional["dev"])),
        }
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as error:
        raise ReviewError(f"Cannot read declared project requirements: {error}") from error
    return name, requirements


def validate_project_policy(policy: ReviewPolicy, root: Path = ROOT) -> None:
    """Require the security policy to name the exact current dependency declarations."""

    name, requirements = project_requirements(root)
    if name != policy.project_name:
        raise ReviewError(f"Policy project {policy.project_name!r} does not match {name!r}")
    if requirements != policy.direct_requirements:
        raise ReviewError("Security policy direct requirements do not match pyproject.toml")


def _requirement_names(requirements: tuple[str, ...]) -> tuple[str, ...]:
    names: list[str] = []
    for value in requirements:
        try:
            requirement = Requirement(value)
        except InvalidRequirement as error:
            raise ReviewError(f"Invalid requirement {value!r}: {error}") from error
        if requirement.marker is not None and not requirement.marker.evaluate({"extra": ""}):
            continue
        names.append(canonicalize_name(requirement.name))
    return tuple(names)


def dependency_closure(direct_requirements: tuple[str, ...]) -> dict[str, Distribution]:
    """Resolve one exact installed dependency closure without consulting a package index."""

    pending = list(_requirement_names(direct_requirements))
    resolved: dict[str, Distribution] = {}
    while pending:
        requested = pending.pop()
        if requested in resolved:
            continue
        try:
            installed = distribution(requested)
        except PackageNotFoundError as error:
            raise ReviewError(f"Declared dependency is not installed: {requested}") from error
        name = canonicalize_name(installed.metadata["Name"])
        resolved[name] = installed
        dependencies = tuple(installed.requires or ())
        pending.extend(
            name
            for name in _requirement_names(dependencies)
            if name not in resolved
        )
    return resolved


def _override_license(
    name: str,
    installed: Distribution,
    override: LicenseOverride,
) -> tuple[str, str]:
    if installed.version != override.version:
        raise ReviewError(
            f"License override for {name} covers {override.version}, not {installed.version}"
        )
    files = {str(item).replace("\\", "/"): item for item in installed.files or ()}
    relative = files.get(override.license_file)
    if relative is None:
        raise ReviewError(f"License override file is missing for {name}: {override.license_file}")
    path = Path(str(installed.locate_file(relative)))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != override.license_file_sha256:
        raise ReviewError(f"License file digest changed for {name} {installed.version}")
    return override.expression, f"reviewed-file:{override.license_file_sha256}"


def package_license(
    name: str,
    installed: Distribution,
    policy: ReviewPolicy,
) -> tuple[str, str]:
    """Resolve one SPDX expression, failing on ambiguous or unreviewed metadata."""

    override = policy.license_overrides.get(name)
    if override is not None:
        return _override_license(name, installed, override)

    expression = installed.metadata.get("License-Expression")
    if expression:
        return expression, "license-expression"
    legacy = installed.metadata.get("License")
    if legacy in _LEGACY_LICENSES:
        return _LEGACY_LICENSES[legacy], "license-field"
    classifiers = tuple(installed.metadata.get_all("Classifier", ()))
    matches = {
        expression
        for classifier, expression in _CLASSIFIER_LICENSES.items()
        if classifier in classifiers
    }
    if len(matches) == 1:
        return matches.pop(), "license-classifier"
    raise ReviewError(f"Dependency {name} {installed.version} has no unambiguous reviewed license")


def review_dependency_scopes(
    policy: ReviewPolicy,
    *,
    scopes: tuple[str, ...] = ("build", "runtime", "development"),
) -> tuple[dict[str, tuple[str, ...]], tuple[PackageReview, ...]]:
    """Review every installed package reachable from declared dependency scopes."""

    if not scopes or len(scopes) != len(set(scopes)):
        raise ReviewError("Dependency review scopes must be unique and non-empty")
    unknown_scopes = set(scopes) - set(policy.direct_requirements)
    if unknown_scopes:
        raise ReviewError(f"Unknown dependency review scopes: {sorted(unknown_scopes)}")
    scope_names: dict[str, tuple[str, ...]] = {}
    packages: dict[str, PackageReview] = {}
    for scope in scopes:
        direct = policy.direct_requirements[scope]
        closure = dependency_closure(direct)
        scope_names[scope] = tuple(sorted(closure))
        for name, installed in closure.items():
            expression, source = package_license(name, installed, policy)
            if expression not in policy.allowed_license_expressions:
                raise ReviewError(
                    f"Dependency {name} {installed.version} uses unapproved license {expression!r}"
                )
            packages[name] = PackageReview(
                name=name,
                version=installed.version,
                license_expression=expression,
                license_source=source,
            )
    return scope_names, tuple(packages[name] for name in sorted(packages))


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+)+", value)
    if match is None:
        raise ReviewError(f"Tool did not report a parseable version: {value!r}")
    return tuple(int(item) for item in match.group(0).split("."))


def _run(
    arguments: list[str],
    *,
    cwd: Path,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        shell=False,
        timeout=timeout,
    )


def tool_version(
    arguments: list[str],
    *,
    minimum: str,
    root: Path = ROOT,
) -> str:
    result = _run(arguments, cwd=root, timeout=30)
    if result.returncode != 0:
        raise ReviewError(f"Required review tool failed version discovery: {arguments[0]}")
    output = f"{result.stdout}\n{result.stderr}".strip()
    actual = _version_tuple(output)
    required = _version_tuple(minimum)
    width = max(len(actual), len(required))
    if (*actual, *(0 for _ in range(width - len(actual)))) < (
        *required,
        *(0 for _ in range(width - len(required))),
    ):
        raise ReviewError(
            f"Review tool {arguments[0]} is {actual}, below required {required}"
        )
    return ".".join(str(item) for item in actual)


def audit_vulnerabilities(
    runtime_packages: tuple[PackageReview, ...],
    *,
    python_executable: Path,
    root: Path = ROOT,
) -> dict[str, object]:
    """Audit exact installed runtime versions without dependency re-resolution."""

    with tempfile.TemporaryDirectory(prefix="forge-pip-audit-") as temporary:
        requirements = Path(temporary) / "runtime-requirements.txt"
        requirements.write_text(
            "".join(f"{item.name}=={item.version}\n" for item in runtime_packages),
            encoding="utf-8",
        )
        result = _run(
            [
                str(python_executable),
                "-m",
                "pip_audit",
                "--requirement",
                str(requirements),
                "--no-deps",
                "--disable-pip",
                "--strict",
                "--format",
                "json",
                "--progress-spinner",
                "off",
                "--desc",
                "off",
            ],
            cwd=root,
            timeout=120,
        )
    try:
        report = _object(json.loads(result.stdout), "pip-audit report")
        dependencies = cast("list[dict[str, object]]", report["dependencies"])
    except (json.JSONDecodeError, KeyError, TypeError, ReviewError) as error:
        raise ReviewError("pip-audit did not return a valid JSON report") from error
    findings = [
        {
            "package": _text(item.get("name"), "pip-audit dependency name"),
            "version": _text(item.get("version"), "pip-audit dependency version"),
            "ids": sorted(
                _text(vulnerability.get("id"), "pip-audit vulnerability ID")
                for vulnerability in cast("list[dict[str, object]]", item.get("vulns", []))
            ),
        }
        for item in dependencies
        if item.get("vulns")
    ]
    if result.returncode != 0 or findings:
        raise ReviewError(f"Known dependency vulnerabilities found: {findings}")
    expected = {item.name for item in runtime_packages}
    observed = {
        canonicalize_name(_text(item.get("name"), "pip-audit dependency name"))
        for item in dependencies
    }
    if observed != expected:
        raise ReviewError(
            f"pip-audit package set differs: missing={sorted(expected - observed)}, "
            f"unknown={sorted(observed - expected)}"
        )
    return {
        "audited_packages": len(dependencies),
        "findings": [],
        "service": "PyPI",
        "status": "passed",
    }


def _read_ignore_fingerprints(path: Path) -> tuple[str, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ReviewError(f"Cannot read Gitleaks ignore file: {error}") from error
    return tuple(
        line.strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    )


def validate_secret_exceptions(
    policy: ReviewPolicy,
    ignore_path: Path = DEFAULT_GITLEAKS_IGNORE,
) -> None:
    observed = _read_ignore_fingerprints(ignore_path)
    if observed != policy.secret_history_exceptions:
        raise ReviewError("Gitleaks ignore fingerprints do not match the exact review policy")
    if any(_FINGERPRINT.fullmatch(item) is None for item in observed):
        raise ReviewError("Gitleaks ignore file contains a non-exact exception")


def _snapshot_review_files(root: Path, destination: Path) -> int:
    inventory = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
        shell=False,
        timeout=30,
    )
    if inventory.returncode != 0:
        raise ReviewError("Git could not enumerate the current review snapshot")
    total = 0
    count = 0
    for encoded in inventory.stdout.split(b"\0"):
        if not encoded:
            continue
        relative_text = os.fsdecode(encoded)
        relative = Path(relative_text)
        if relative.is_absolute() or ".." in relative.parts:
            raise ReviewError(f"Git returned an unsafe review path: {relative_text!r}")
        source = root / relative
        if source.is_symlink() or not source.is_file():
            raise ReviewError(f"Review snapshot contains an irregular path: {relative_text!r}")
        size = source.stat().st_size
        if size > MAX_SNAPSHOT_FILE_BYTES:
            raise ReviewError(f"Review snapshot file exceeds the size limit: {relative_text!r}")
        total += size
        if total > MAX_SNAPSHOT_TOTAL_BYTES:
            raise ReviewError("Review snapshot exceeds the aggregate size limit")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        count += 1
    return count


def _gitleaks_findings(path: Path) -> list[dict[str, object]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReviewError("Gitleaks did not return a valid redacted JSON report") from error
    if not isinstance(value, list):
        raise ReviewError("Gitleaks report root must be a JSON array")
    return cast("list[dict[str, object]]", value)


def _run_gitleaks(
    arguments: list[str],
    *,
    report_path: Path,
    root: Path,
) -> None:
    result = _run(
        [
            *arguments,
            "--redact=100",
            "--report-format",
            "json",
            "--report-path",
            str(report_path),
            "--no-banner",
            "--no-color",
            "--gitleaks-ignore-path",
            str(DEFAULT_GITLEAKS_IGNORE),
        ],
        cwd=root,
        timeout=120,
    )
    findings = _gitleaks_findings(report_path)
    if result.returncode != 0 or findings:
        summary = [
            {
                "file": item.get("File"),
                "line": item.get("StartLine"),
                "rule": item.get("RuleID"),
            }
            for item in findings
        ]
        raise ReviewError(f"Gitleaks found unreviewed secret patterns: {summary}")


def scan_secrets(
    policy: ReviewPolicy,
    *,
    gitleaks_executable: Path,
    root: Path = ROOT,
) -> dict[str, object]:
    """Scan full Git history and a bounded current review snapshot with redaction."""

    validate_secret_exceptions(policy, root / ".gitleaksignore")
    with tempfile.TemporaryDirectory(prefix="forge-gitleaks-") as temporary:
        scratch = Path(temporary)
        history_report = scratch / "history.json"
        _run_gitleaks(
            [str(gitleaks_executable), "git", str(root)],
            report_path=history_report,
            root=root,
        )
        snapshot = scratch / "snapshot"
        snapshot.mkdir()
        file_count = _snapshot_review_files(root, snapshot)
        snapshot_report = scratch / "snapshot.json"
        _run_gitleaks(
            [str(gitleaks_executable), "dir", str(snapshot)],
            report_path=snapshot_report,
            root=root,
        )
    return {
        "exceptions": len(policy.secret_history_exceptions),
        "history": "passed",
        "snapshot": "passed",
        "snapshot_files": file_count,
    }


def run_review(
    policy: ReviewPolicy,
    *,
    python_executable: Path,
    gitleaks_executable: Path,
    root: Path = ROOT,
) -> dict[str, object]:
    """Run the complete Increment 5 review and return a secret-free JSON result."""

    validate_project_policy(policy, root)
    scopes, packages = review_dependency_scopes(policy)
    runtime_names = set(scopes["runtime"])
    runtime_packages = tuple(item for item in packages if item.name in runtime_names)
    pip_audit_version = tool_version(
        [str(python_executable), "-m", "pip_audit", "--version"],
        minimum=policy.minimum_tool_versions["pip-audit"],
        root=root,
    )
    gitleaks_version = tool_version(
        [str(gitleaks_executable), "version"],
        minimum=policy.minimum_tool_versions["gitleaks"],
        root=root,
    )
    vulnerabilities = audit_vulnerabilities(
        runtime_packages,
        python_executable=python_executable,
        root=root,
    )
    secrets = scan_secrets(
        policy,
        gitleaks_executable=gitleaks_executable,
        root=root,
    )
    return {
        "schema_version": 1,
        "status": "passed",
        "policy_digest": policy.digest,
        "environment": {
            "operating_system": platform.system().lower(),
            "python_implementation": platform.python_implementation(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "tools": {
            "gitleaks": gitleaks_version,
            "pip-audit": pip_audit_version,
        },
        "dependencies": {
            "direct_requirements": policy.direct_requirements,
            "scopes": scopes,
            "packages": [
                {
                    "name": item.name,
                    "version": item.version,
                    "license_expression": item.license_expression,
                    "license_source": item.license_source,
                }
                for item in packages
            ],
        },
        "vulnerabilities": vulnerabilities,
        "secrets": secrets,
        "limitations": [
            "The dependency and license inventory covers this exact installed environment.",
            "The advisory result is point-in-time evidence, not a future vulnerability guarantee.",
            "Secret detection is heuristic and cannot prove the repository secret-free.",
            "Cross-platform and clean-wheel repetition remain M6 closeout evidence.",
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review FORGE dependencies, licenses, vulnerabilities, and Git secrets."
    )
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument(
        "--python",
        type=Path,
        default=Path(sys.executable),
        help="Python environment containing FORGE, packaging, and pip-audit.",
    )
    parser.add_argument(
        "--gitleaks",
        type=Path,
        default=Path(shutil.which("gitleaks") or "gitleaks"),
    )
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        policy = load_policy(arguments.policy.resolve(strict=True))
        python_executable = arguments.python.resolve(strict=True)
        gitleaks_executable = arguments.gitleaks.resolve(strict=True)
        report = run_review(
            policy,
            python_executable=python_executable,
            gitleaks_executable=gitleaks_executable,
        )
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if arguments.output is None:
            sys.stdout.write(rendered)
        else:
            output = arguments.output.resolve()
            if output.exists():
                raise ReviewError(f"Refusing to overwrite review output: {output}")
            output.write_text(rendered, encoding="utf-8")
    except (OSError, ReviewError, subprocess.TimeoutExpired) as error:
        print(f"release security review failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
