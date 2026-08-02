import json
import tomllib
import zipfile
from io import BytesIO, TextIOWrapper
from pathlib import Path

import pytest

from forge import __version__
from forge.contracts import CONTRACT_MODELS
from tools.distribution_smoke import (
    INSTALLATION_MODES,
    SmokeError,
    console_script,
    echo_captured,
    environment_python,
    load_matrix,
    platform_id,
    smoke_root,
    validate_wheel_metadata,
)

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "release" / "installation-matrix.json"


def test_installation_matrix_covers_every_supported_cell() -> None:
    matrix = load_matrix(MATRIX_PATH)

    assert matrix.python_implementation == "CPython"
    assert matrix.python_versions == ("3.12", "3.13", "3.14")
    assert set(matrix.operating_systems) == {"linux", "macos", "windows"}
    assert set(matrix.installation_modes) == INSTALLATION_MODES
    assert (
        len(matrix.python_versions)
        * len(matrix.operating_systems)
        * len(matrix.installation_modes)
        == 18
    )


def test_installation_matrix_matches_current_public_package() -> None:
    matrix = load_matrix(MATRIX_PATH)
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    metadata = project["project"]

    assert metadata["name"] == matrix.expected_distribution
    assert metadata["version"] == matrix.expected_version == __version__
    assert metadata["requires-python"] == ">=3.12"
    assert matrix.expected_schema_count == len(CONTRACT_MODELS)
    assert set(matrix.expected_bundled_packs) == {"research-basic", "software-basic"}
    for version in matrix.python_versions:
        assert f"Programming Language :: Python :: {version}" in metadata["classifiers"]


def test_distribution_build_prunes_local_runtime_state_before_traversal() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    build = project["tool"]["hatch"]["build"]

    assert build["exclude"] == ["/.forge/local/**"]
    assert build["skip-excluded-dirs"] is True


def test_cross_platform_installed_executable_paths_are_explicit(tmp_path: Path) -> None:
    assert environment_python(tmp_path, "Windows") == tmp_path / "Scripts" / "python.exe"
    assert environment_python(tmp_path, "Linux") == tmp_path / "bin" / "python"
    assert environment_python(tmp_path, "Darwin") == tmp_path / "bin" / "python"
    assert console_script(tmp_path, "Windows") == tmp_path / "forge.exe"
    assert console_script(tmp_path, "Linux") == tmp_path / "forge"
    assert console_script(tmp_path, "Darwin") == tmp_path / "forge"


def test_unknown_operating_system_fails_closed() -> None:
    with pytest.raises(SmokeError, match="Unsupported operating system"):
        platform_id("Plan9")


def test_captured_unicode_is_safe_for_a_narrow_windows_console() -> None:
    buffer = BytesIO()
    stream = TextIOWrapper(buffer, encoding="cp1252")
    echo_captured("help ─ boundary\n", stream)
    stream.flush()

    assert buffer.getvalue().decode("cp1252").splitlines() == [r"help \u2500 boundary"]


def test_matrix_rejects_executable_or_unknown_fields(tmp_path: Path) -> None:
    document = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    document["command"] = "forge --help"
    invalid = tmp_path / "matrix.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(SmokeError, match=r"unknown=.*command"):
        load_matrix(invalid)


def test_wheel_metadata_must_match_the_matrix(tmp_path: Path) -> None:
    matrix = load_matrix(MATRIX_PATH)
    wheel = tmp_path / "other-0.1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "other-0.1.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: other\nVersion: 0.1\n",
        )

    with pytest.raises(SmokeError, match="Wheel distribution"):
        validate_wheel_metadata(wheel, matrix)


def test_smoke_work_directory_must_be_fresh(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    with (
        pytest.raises(SmokeError, match="Refusing to use an existing"),
        smoke_root(existing),
    ):
        raise AssertionError("unreachable")

    retained = tmp_path / "retained"
    with smoke_root(retained) as root:
        assert root == retained.resolve()
        assert root.is_dir()
    assert retained.is_dir()
