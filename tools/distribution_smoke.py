"""Validate a built FORGE wheel through an isolated venv or pipx installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import NoReturn, TextIO, cast

MATRIX_PATH = Path(__file__).resolve().parents[1] / "release" / "installation-matrix.json"
MATRIX_KEYS = {
    "schema_version",
    "python_implementation",
    "python_versions",
    "operating_systems",
    "installation_modes",
    "artifact",
    "expected_distribution",
    "expected_version",
    "expected_schema_count",
    "expected_bundled_packs",
}
OS_IDS = {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}
INSTALLATION_MODES = {"venv", "pipx"}


class SmokeError(RuntimeError):
    """A distribution smoke precondition or command failed."""


@dataclass(frozen=True)
class InstallationMatrix:
    """Validated release installation expectations."""

    python_implementation: str
    python_versions: tuple[str, ...]
    operating_systems: tuple[str, ...]
    installation_modes: tuple[str, ...]
    expected_distribution: str
    expected_version: str
    expected_schema_count: int
    expected_bundled_packs: tuple[str, ...]


def _fail(message: str) -> NoReturn:
    raise SmokeError(message)


def _text_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        _fail(f"{field} must be a non-empty list")
    result: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str) or not item:
            _fail(f"{field} entries must be non-empty strings")
        result.append(item)
    if len(set(result)) != len(result):
        _fail(f"{field} entries must be unique")
    return tuple(result)


def load_matrix(path: Path) -> InstallationMatrix:
    """Load the exact data-only matrix without interpreting executable content."""
    try:
        raw_document: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SmokeError(f"Cannot load installation matrix {path}: {error}") from error
    if not isinstance(raw_document, dict):
        _fail("Installation matrix must be a JSON object")
    document = cast(dict[str, object], raw_document)
    unknown = set(document) - MATRIX_KEYS
    missing = MATRIX_KEYS - set(document)
    if unknown or missing:
        _fail(
            "Installation matrix keys do not match the supported schema "
            f"(missing={sorted(missing)}, unknown={sorted(unknown)})"
        )
    if document["schema_version"] != "1.0":
        _fail("Unsupported installation matrix schema version")
    if document["artifact"] != "wheel":
        _fail("The installation acceptance artifact must be a wheel")

    systems_value = document["operating_systems"]
    if not isinstance(systems_value, list) or not systems_value:
        _fail("operating_systems must be a non-empty list")
    systems: list[str] = []
    for raw_item in cast(list[object], systems_value):
        if not isinstance(raw_item, dict):
            _fail("Each operating system must contain exactly id and runner")
        item = cast(dict[str, object], raw_item)
        if set(item) != {"id", "runner"}:
            _fail("Each operating system must contain exactly id and runner")
        system_id = item["id"]
        runner = item["runner"]
        if not isinstance(system_id, str) or not isinstance(runner, str):
            _fail("Operating-system ids and runners must be strings")
        systems.append(system_id)
    if len(set(systems)) != len(systems):
        _fail("Operating-system ids must be unique")

    implementation = document["python_implementation"]
    distribution = document["expected_distribution"]
    version = document["expected_version"]
    schema_count = document["expected_schema_count"]
    if (
        not isinstance(implementation, str)
        or not implementation
        or not isinstance(distribution, str)
        or not distribution
        or not isinstance(version, str)
        or not version
    ):
        _fail("Implementation, distribution, and version must be non-empty strings")
    if not isinstance(schema_count, int) or isinstance(schema_count, bool) or schema_count < 1:
        _fail("expected_schema_count must be a positive integer")

    modes = _text_tuple(document["installation_modes"], field="installation_modes")
    if set(modes) != INSTALLATION_MODES:
        _fail(f"installation_modes must be exactly {sorted(INSTALLATION_MODES)}")
    return InstallationMatrix(
        python_implementation=implementation,
        python_versions=_text_tuple(document["python_versions"], field="python_versions"),
        operating_systems=tuple(systems),
        installation_modes=modes,
        expected_distribution=distribution,
        expected_version=version,
        expected_schema_count=schema_count,
        expected_bundled_packs=_text_tuple(
            document["expected_bundled_packs"],
            field="expected_bundled_packs",
        ),
    )


def platform_id(system: str | None = None) -> str:
    """Return the matrix identifier for the current operating system."""
    detected = platform.system() if system is None else system
    try:
        return OS_IDS[detected]
    except KeyError as error:
        raise SmokeError(f"Unsupported operating system: {detected}") from error


def environment_python(environment: Path, system: str | None = None) -> Path:
    """Resolve a venv Python path without relying on shell activation."""
    return (
        environment / "Scripts" / "python.exe"
        if platform_id(system) == "windows"
        else environment / "bin" / "python"
    )


def console_script(bin_directory: Path, system: str | None = None) -> Path:
    """Resolve the installed FORGE console script path."""
    return (
        bin_directory / "forge.exe"
        if platform_id(system) == "windows"
        else bin_directory / "forge"
    )


def _render_command(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(command)


def echo_captured(value: str, stream: TextIO) -> None:
    """Echo child output without failing on a narrower parent console encoding."""
    encoding = stream.encoding or "utf-8"
    safe = value.encode(encoding, errors="backslashreplace").decode(encoding)
    stream.write(safe)
    if not safe.endswith("\n"):
        stream.write("\n")


def run_checked(
    command: Sequence[str | Path],
    *,
    environment: Mapping[str, str],
    cwd: Path,
    expected_output: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one exact argument vector and require a successful, expected result."""
    rendered = [str(item) for item in command]
    print(f"+ {_render_command(rendered)}", flush=True)
    result = subprocess.run(
        rendered,
        cwd=cwd,
        env=dict(environment),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        shell=False,
    )
    if result.stdout:
        echo_captured(result.stdout, sys.stdout)
    if result.stderr:
        echo_captured(result.stderr, sys.stderr)
    if result.returncode != 0:
        _fail(f"Command exited with status {result.returncode}: {_render_command(rendered)}")
    if expected_output is not None and expected_output not in result.stdout:
        _fail(f"Command output did not contain {expected_output!r}: {_render_command(rendered)}")
    return result


def _base_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def _inspect_python(
    python: Path,
    *,
    environment: Mapping[str, str],
    cwd: Path,
) -> tuple[str, str]:
    inspection = (
        "import json,platform,sys;"
        "print(json.dumps({'implementation':platform.python_implementation(),"
        "'version':f'{sys.version_info.major}.{sys.version_info.minor}'}))"
    )
    result = run_checked(
        [python, "-c", inspection],
        environment=environment,
        cwd=cwd,
    )
    try:
        raw_document: object = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise SmokeError(f"Cannot inspect target Python: {error}") from error
    if not isinstance(raw_document, dict):
        _fail("Target Python returned an invalid identity document")
    document = cast(dict[str, object], raw_document)
    if set(document) != {"implementation", "version"}:
        _fail("Target Python returned an invalid identity document")
    implementation = document["implementation"]
    version = document["version"]
    if not isinstance(implementation, str) or not isinstance(version, str):
        _fail("Target Python returned an invalid identity document")
    return implementation, version


def _validate_current_cell(
    matrix: InstallationMatrix,
    mode: str,
    *,
    implementation: str,
    python_version: str,
) -> tuple[str, str]:
    operating_system = platform_id()
    if implementation != matrix.python_implementation:
        _fail(
            f"Unsupported Python implementation {implementation}; "
            f"expected {matrix.python_implementation}"
        )
    if python_version not in matrix.python_versions:
        _fail(
            f"Python {python_version} is outside the acceptance matrix "
            f"{matrix.python_versions}"
        )
    if operating_system not in matrix.operating_systems:
        _fail(f"Operating system {operating_system} is outside the acceptance matrix")
    if mode not in matrix.installation_modes:
        _fail(f"Installation mode {mode} is outside the acceptance matrix")
    return python_version, operating_system


def _normalized_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).casefold()


def validate_wheel_metadata(wheel: Path, matrix: InstallationMatrix) -> None:
    try:
        with zipfile.ZipFile(wheel) as archive:
            metadata_paths = [
                name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata_paths) != 1:
                _fail("Wheel must contain exactly one .dist-info/METADATA file")
            info = archive.getinfo(metadata_paths[0])
            if info.file_size > 1024 * 1024:
                _fail("Wheel METADATA exceeds the 1 MiB inspection limit")
            message = BytesParser(policy=policy.default).parsebytes(
                archive.read(metadata_paths[0])
            )
    except (OSError, zipfile.BadZipFile) as error:
        raise SmokeError(f"Cannot inspect wheel metadata: {error}") from error
    name = message.get("Name")
    version = message.get("Version")
    if not isinstance(name, str) or not isinstance(version, str):
        _fail("Wheel metadata must contain one Name and Version")
    if _normalized_distribution_name(name) != _normalized_distribution_name(
        matrix.expected_distribution
    ):
        _fail(
            f"Wheel distribution is {name!r}; "
            f"expected {matrix.expected_distribution!r}"
        )
    if version != matrix.expected_version:
        _fail(f"Wheel version is {version!r}; expected {matrix.expected_version!r}")


def _install_with_venv(
    *,
    python: Path,
    wheel: Path,
    root: Path,
    environment: Mapping[str, str],
) -> Path:
    venv_directory = root / "venv"
    run_checked(
        [python, "-m", "venv", venv_directory],
        environment=environment,
        cwd=root,
    )
    installed_python = environment_python(venv_directory)
    run_checked(
        [
            installed_python,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            wheel,
        ],
        environment=environment,
        cwd=root,
    )
    executable = console_script(installed_python.parent)
    run_checked(
        [installed_python, "-m", "forge", "--version"],
        environment=environment,
        cwd=root,
    )
    return executable


def _install_with_pipx(
    *,
    python: Path,
    wheel: Path,
    root: Path,
    environment: dict[str, str],
) -> Path:
    pipx_home = root / "pipx-home"
    pipx_bin = root / "pipx-bin"
    environment.update(
        {
            "PIPX_BIN_DIR": str(pipx_bin),
            "PIPX_HOME": str(pipx_home),
            "PIPX_MAN_DIR": str(root / "pipx-man"),
            "PIPX_SHARED_LIBS": str(root / "pipx-shared"),
        }
    )
    run_checked(
        [python, "-m", "pipx", "--version"],
        environment=environment,
        cwd=root,
    )
    run_checked(
        [python, "-m", "pipx", "install", "--force", "--python", python, wheel],
        environment=environment,
        cwd=root,
    )
    return console_script(pipx_bin)


def _run_product_smoke(
    *,
    executable: Path,
    root: Path,
    environment: Mapping[str, str],
    matrix: InstallationMatrix,
) -> int:
    if not executable.is_file():
        _fail(f"Installed console script does not exist: {executable}")
    project = root / "project"
    schemas = root / "schemas"
    project.mkdir()
    run_checked(
        [executable, "--version"],
        environment=environment,
        cwd=root,
        expected_output=matrix.expected_version,
    )
    run_checked(
        [executable, "--help"],
        environment=environment,
        cwd=root,
        expected_output="Govern human-directed, AI-assisted work",
    )
    run_checked(
        [executable, "init", project, "--owner-name", "Distribution Smoke Owner"],
        environment=environment,
        cwd=root,
        expected_output="Initialized FORGE repository",
    )
    run_checked(
        [executable, "config", "validate", "-C", project],
        environment=environment,
        cwd=root,
        expected_output="Valid FORGE configuration 1.0",
    )
    for pack_id in matrix.expected_bundled_packs:
        run_checked(
            [executable, "pack", "validate", pack_id, "-C", project],
            environment=environment,
            cwd=root,
            expected_output=f"Valid data pack {pack_id}",
        )
    run_checked(
        [executable, "doctor", "-C", project],
        environment=environment,
        cwd=root,
        expected_output="FORGE repository health: healthy",
    )
    run_checked(
        [executable, "schema", "export", "--output", schemas],
        environment=environment,
        cwd=root,
        expected_output=f"Exported {matrix.expected_schema_count} contract schemas",
    )
    index_path = schemas / "index.json"
    try:
        raw_index: object = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SmokeError(f"Cannot inspect exported schema index: {error}") from error
    index = cast(dict[str, object], raw_index) if isinstance(raw_index, dict) else {}
    schema_index_value = index.get("schemas")
    schema_index = (
        cast(dict[str, object], schema_index_value)
        if isinstance(schema_index_value, dict)
        else None
    )
    if (
        not isinstance(schema_index, dict)
        or len(schema_index) != matrix.expected_schema_count
    ):
        _fail(
            f"Expected {matrix.expected_schema_count} schema index entries, "
            f"found {len(schema_index) if isinstance(schema_index, dict) else 'invalid index'}"
        )
    return len(schema_index)


def _wheel_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@contextmanager
def smoke_root(requested: Path | None) -> Generator[Path]:
    """Yield a fresh scratch root without deleting a caller-owned directory."""
    if requested is None:
        with tempfile.TemporaryDirectory(prefix="forge-distribution-smoke-") as temporary:
            yield Path(temporary)
        return
    resolved = requested.resolve()
    if resolved.exists():
        _fail(f"Refusing to use an existing smoke work directory: {resolved}")
    resolved.mkdir(parents=True)
    yield resolved


def run_smoke(
    *,
    wheel: Path,
    mode: str,
    python: Path,
    matrix_path: Path,
    work_directory: Path | None,
) -> dict[str, object]:
    """Install and exercise one exact acceptance-matrix cell."""
    matrix = load_matrix(matrix_path)
    resolved_wheel = wheel.resolve(strict=True)
    if not resolved_wheel.is_file() or resolved_wheel.suffix != ".whl":
        _fail(f"Expected a wheel file: {resolved_wheel}")
    validate_wheel_metadata(resolved_wheel, matrix)
    resolved_python = python.resolve(strict=True)
    environment = _base_environment()
    with smoke_root(work_directory) as root:
        implementation, inspected_version = _inspect_python(
            resolved_python,
            environment=environment,
            cwd=root,
        )
        python_version, operating_system = _validate_current_cell(
            matrix,
            mode,
            implementation=implementation,
            python_version=inspected_version,
        )
        if mode == "venv":
            executable = _install_with_venv(
                python=resolved_python,
                wheel=resolved_wheel,
                root=root,
                environment=environment,
            )
        else:
            executable = _install_with_pipx(
                python=resolved_python,
                wheel=resolved_wheel,
                root=root,
                environment=environment,
            )
        schema_count = _run_product_smoke(
            executable=executable,
            root=root,
            environment=environment,
            matrix=matrix,
        )
    return {
        "artifact": resolved_wheel.name,
        "installation_mode": mode,
        "operating_system": operating_system,
        "python_implementation": matrix.python_implementation,
        "python_version": python_version,
        "schema_count": schema_count,
        "status": "passed",
        "version": matrix.expected_version,
        "wheel_sha256": _wheel_digest(resolved_wheel),
    }


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install and smoke-test one FORGE release acceptance matrix cell.",
    )
    parser.add_argument("--wheel", required=True, type=Path, help="Exact wheel to install.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=sorted(INSTALLATION_MODES),
        help="Isolated installation mechanism.",
    )
    parser.add_argument(
        "--python",
        type=Path,
        default=Path(sys.executable),
        help="Exact CPython interpreter for this matrix cell.",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=MATRIX_PATH,
        help="Machine-readable installation acceptance matrix.",
    )
    parser.add_argument(
        "--work-directory",
        type=Path,
        help="Fresh nonexistent directory to retain for inspection; defaults to temporary.",
    )
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = parse_args(arguments)
    try:
        evidence = run_smoke(
            wheel=args.wheel,
            mode=args.mode,
            python=args.python,
            matrix_path=args.matrix,
            work_directory=args.work_directory,
        )
    except (OSError, SmokeError) as error:
        print(f"distribution smoke failed: {error}", file=sys.stderr)
        return 1
    print(
        "FORGE_DISTRIBUTION_SMOKE="
        + json.dumps(evidence, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
