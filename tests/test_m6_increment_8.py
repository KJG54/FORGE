from pathlib import Path
from typing import cast

import yaml

from tools.release_procedure_rehearsal import rehearsal_root

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci.yml"
PROCEDURE_TOOL = ROOT / "tools" / "release_procedure_rehearsal.py"


def _workflow() -> dict[str, object]:
    document: object = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    return _mapping(document)


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    untyped = cast("dict[object, object]", value)
    assert all(isinstance(key, str) for key in untyped)
    return cast("dict[str, object]", value)


def _sequence(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _matrix_size(job: object) -> int:
    matrix = _mapping(_mapping(_mapping(job)["strategy"])["matrix"])
    size = 1
    for values in matrix.values():
        size *= len(_sequence(values))
    return size


def test_closeout_ci_executes_supported_test_install_and_release_matrices() -> None:
    document = _workflow()
    triggers = _mapping(document["on"])
    jobs = _mapping(document["jobs"])

    assert _mapping(triggers["push"])["branches"] == ["main"]
    assert set(jobs) == {
        "quality",
        "test",
        "build",
        "installation",
        "release-scenarios",
    }
    assert _matrix_size(jobs["test"]) == 9
    assert _matrix_size(jobs["installation"]) == 18
    assert _matrix_size(jobs["release-scenarios"]) == 9

    installation = _mapping(jobs["installation"])
    scenarios = _mapping(jobs["release-scenarios"])
    assert installation["needs"] == "build"
    assert scenarios["needs"] == "build"
    rendered = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "tools.distribution_smoke" in rendered
    assert "tools.performance_review" in rendered
    assert "tools.example_workflow_smoke --example all" in rendered
    assert "tools.release_procedure_rehearsal" in rendered


def test_release_procedure_work_directory_must_be_fresh(tmp_path: Path) -> None:
    retained = tmp_path / "retained"
    with rehearsal_root(retained) as root:
        assert root == retained.resolve()
        assert root.is_dir()
    assert retained.is_dir()


def test_release_procedure_harness_never_uses_shell_command_strings() -> None:
    source = PROCEDURE_TOOL.read_text(encoding="utf-8")

    assert "shell=False" in source
    assert "shell=True" not in source
    assert {
        '"backup": "passed"',
        '"migration": "passed"',
        '"snapshot_recovery": "passed"',
        '"restore": "passed"',
        '"abandonment": "passed"',
        '"archive_access": "passed"',
        '"successor": "passed"',
    } <= {line.strip().removesuffix(",") for line in source.splitlines()}
