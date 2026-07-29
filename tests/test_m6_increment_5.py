import json
from dataclasses import replace
from pathlib import Path

import pytest

from tools.release_security_review import (
    DEFAULT_GITLEAKS_IGNORE,
    DEFAULT_POLICY,
    ReviewError,
    dependency_closure,
    load_policy,
    project_requirements,
    review_dependency_scopes,
    validate_project_policy,
    validate_secret_exceptions,
)

ROOT = Path(__file__).resolve().parents[1]


def test_security_policy_matches_exact_project_dependency_declarations() -> None:
    policy = load_policy()
    project_name, requirements = project_requirements()

    assert project_name == policy.project_name == "forge-governance"
    assert requirements == policy.direct_requirements
    validate_project_policy(policy)


def test_installed_dependency_scopes_have_only_allowed_reviewed_licenses() -> None:
    policy = load_policy()
    scopes, packages = review_dependency_scopes(policy)

    assert {"build", "runtime", "development"} == set(scopes)
    assert {"pydantic", "pyyaml", "typer"} <= set(scopes["runtime"])
    assert {"hatchling", "build", "pytest", "pyright", "ruff"} <= {
        name for names in scopes.values() for name in names
    }
    assert packages
    assert all(
        item.license_expression in policy.allowed_license_expressions
        for item in packages
    )


def test_dependency_closure_fails_when_a_declared_package_is_missing() -> None:
    with pytest.raises(ReviewError, match="not installed"):
        dependency_closure(("definitely-not-a-real-forge-package==1",))


def test_policy_rejects_unknown_fields(tmp_path: Path) -> None:
    document = json.loads(DEFAULT_POLICY.read_text(encoding="utf-8"))
    document["command"] = "pip-audit"
    invalid = tmp_path / "policy.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ReviewError, match=r"unknown=.*command"):
        load_policy(invalid)


def test_secret_exception_is_one_exact_historical_fixture_fingerprint() -> None:
    policy = load_policy()
    validate_secret_exceptions(policy)

    assert policy.secret_history_exceptions == (
        "d73226943b208c8482e0fd7e919cb4070cf14b47:"
        "tests/test_artifacts_and_evidence.py:generic-api-key:307",
    )
    assert "tests/test_artifacts_and_evidence.py" in DEFAULT_GITLEAKS_IGNORE.read_text(
        encoding="utf-8"
    )


def test_secret_exception_policy_cannot_hide_a_whole_path(tmp_path: Path) -> None:
    policy = load_policy()
    broad_ignore = tmp_path / ".gitleaksignore"
    broad_ignore.write_text("tests/test_artifacts_and_evidence.py\n", encoding="utf-8")

    with pytest.raises(ReviewError, match="do not match"):
        validate_secret_exceptions(policy, broad_ignore)

    broad_policy = replace(
        policy,
        secret_history_exceptions=("tests/test_artifacts_and_evidence.py",),
    )
    broad_ignore.write_text("tests/test_artifacts_and_evidence.py\n", encoding="utf-8")
    with pytest.raises(ReviewError, match="non-exact"):
        validate_secret_exceptions(broad_policy, broad_ignore)
