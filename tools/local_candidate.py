"""Inspect and verify the exact unpublished Local Production-v1 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import zipfile
from collections.abc import Sequence
from email.parser import Parser
from pathlib import Path
from typing import Literal, NoReturn, TypedDict, cast

ROOT = Path(__file__).resolve().parents[1]
VERSION_CONTRACT = ROOT / "release" / "version-contract.json"
DEFAULT_ARTIFACT_DIRECTORY = ROOT / "dist" / "local-production-v1"
DEFAULT_MANIFEST = ROOT / "release" / "local-production-v1" / "candidate-manifest.json"
DEFAULT_HASHES = ROOT / "release" / "local-production-v1" / "SHA256SUMS"

ArtifactType = Literal["wheel", "sdist"]


class CandidateArtifact(TypedDict):
    """Exact identity of one local candidate distribution artifact."""

    type: ArtifactType
    filename: str
    sha256: str
    size_bytes: int


class CandidateInspection(TypedDict):
    """Validated identity of the exact local candidate artifact pair."""

    distribution: str
    version: str
    artifacts: list[CandidateArtifact]


class CandidateError(RuntimeError):
    """The local candidate artifacts or their recorded identity are invalid."""


def _fail(message: str) -> NoReturn:
    raise CandidateError(message)


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail(f"{label} must be a JSON object")
    return cast("dict[str, object]", value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{label} must be non-empty text")
    return value


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        _fail(f"{label} must be a non-negative integer")
    return value


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), label)
    except (OSError, json.JSONDecodeError) as error:
        raise CandidateError(f"Cannot load {label} at {path}: {error}") from error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _metadata_fields(text: str, label: str) -> tuple[str, str]:
    metadata = Parser().parsestr(text)
    name = metadata.get("Name")
    version = metadata.get("Version")
    if not name or not version:
        _fail(f"{label} metadata must contain Name and Version")
    return name, version


def _wheel_identity(path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(names) != 1:
                _fail(f"Wheel must contain exactly one METADATA file; found {len(names)}")
            text = archive.read(names[0]).decode("utf-8")
    except (OSError, UnicodeDecodeError, zipfile.BadZipFile) as error:
        raise CandidateError(f"Cannot inspect wheel {path}: {error}") from error
    return _metadata_fields(text, "wheel")


def _sdist_identity(path: Path) -> tuple[str, str]:
    try:
        with tarfile.open(path, mode="r:gz") as archive:
            members = [
                member
                for member in archive.getmembers()
                if member.name.endswith("/PKG-INFO")
            ]
            if len(members) != 1:
                _fail(f"Source distribution must contain one PKG-INFO; found {len(members)}")
            stream = archive.extractfile(members[0])
            if stream is None:
                _fail("Source-distribution PKG-INFO is not a regular file")
            text = stream.read().decode("utf-8")
    except (OSError, UnicodeDecodeError, tarfile.TarError) as error:
        raise CandidateError(f"Cannot inspect source distribution {path}: {error}") from error
    return _metadata_fields(text, "source distribution")


def inspect_candidate(
    artifact_directory: Path = DEFAULT_ARTIFACT_DIRECTORY,
) -> CandidateInspection:
    """Return exact artifact identity after validating names and embedded metadata."""
    contract = _load_json(VERSION_CONTRACT, "version contract")
    distribution = _object(contract.get("distribution"), "distribution contract")
    expected_name = _text(distribution.get("name"), "distribution name")
    expected_version = _text(distribution.get("version"), "distribution version")
    expected: tuple[tuple[ArtifactType, str], ...] = (
        ("wheel", _text(distribution.get("wheel_filename"), "wheel filename")),
        ("sdist", _text(distribution.get("sdist_filename"), "sdist filename")),
    )
    if not artifact_directory.is_dir():
        _fail(f"Artifact directory does not exist: {artifact_directory}")
    actual_names = sorted(
        path.name
        for path in artifact_directory.iterdir()
        if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
    )
    expected_names = sorted(filename for _, filename in expected)
    if actual_names != expected_names:
        _fail(f"Expected only {expected_names!r}; found {actual_names!r}")

    artifacts: list[CandidateArtifact] = []
    for artifact_type, filename in expected:
        path = artifact_directory / filename
        identity = _wheel_identity(path) if artifact_type == "wheel" else _sdist_identity(path)
        if identity != (expected_name, expected_version):
            _fail(
                f"{artifact_type} metadata differs: expected "
                f"{(expected_name, expected_version)!r}, found {identity!r}"
            )
        artifacts.append(
            {
                "type": artifact_type,
                "filename": filename,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "distribution": expected_name,
        "version": expected_version,
        "artifacts": artifacts,
    }


def _artifact_entries(value: object, label: str) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        _fail(f"{label} must contain exactly two artifact entries")
    items = cast("list[object]", value)
    if len(items) != 2:
        _fail(f"{label} must contain exactly two artifact entries")
    entries = tuple(_object(item, f"{label} entry") for item in items)
    if {entry.get("type") for entry in entries} != {"wheel", "sdist"}:
        _fail(f"{label} must contain one wheel and one sdist")
    for entry in entries:
        _text(entry.get("filename"), "artifact filename")
        digest = _text(entry.get("sha256"), "artifact SHA-256")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            _fail("Artifact SHA-256 must be 64 lowercase hexadecimal characters")
        _integer(entry.get("size_bytes"), "artifact size")
    return entries


def validate_manifest_contract(
    manifest_path: Path = DEFAULT_MANIFEST,
    hashes_path: Path = DEFAULT_HASHES,
) -> dict[str, object]:
    """Validate the tracked manifest and checksum file without requiring local artifacts."""
    manifest = _load_json(manifest_path, "candidate manifest")
    if manifest.get("schema_version") != 1:
        _fail("Candidate manifest schema_version must be 1")
    if manifest.get("status") != "unpublished-local-candidate":
        _fail("Candidate manifest status must be unpublished-local-candidate")
    contract = _load_json(VERSION_CONTRACT, "version contract")
    distribution = _object(contract.get("distribution"), "distribution contract")
    if manifest.get("distribution") != distribution.get("name"):
        _fail("Candidate manifest distribution differs from version contract")
    if manifest.get("version") != distribution.get("version"):
        _fail("Candidate manifest version differs from version contract")
    entries = _artifact_entries(manifest.get("artifacts"), "candidate artifacts")
    expected_filenames = {
        distribution.get("wheel_filename"),
        distribution.get("sdist_filename"),
    }
    if {entry.get("filename") for entry in entries} != expected_filenames:
        _fail("Candidate artifact filenames differ from version contract")
    wheel = next(entry for entry in entries if entry["type"] == "wheel")
    downstream = _object(manifest.get("downstream_installation"), "downstream installation")
    if downstream != {
        "artifact_type": "wheel",
        "filename": wheel["filename"],
        "sha256": wheel["sha256"],
    }:
        _fail("Downstream installation must bind the exact candidate wheel")
    publication = _object(manifest.get("publication"), "publication boundary")
    if publication.get("authorized") is not False or publication.get("tag_created") is not False:
        _fail("Candidate manifest must not authorize publication or claim a tag")

    try:
        lines = [line for line in hashes_path.read_text(encoding="utf-8").splitlines() if line]
    except OSError as error:
        raise CandidateError(f"Cannot load checksum file at {hashes_path}: {error}") from error
    expected_lines = sorted(f"{entry['sha256']}  {entry['filename']}" for entry in entries)
    if sorted(lines) != expected_lines:
        _fail("SHA256SUMS differs from the candidate manifest")
    return manifest


def verify_candidate(
    artifact_directory: Path = DEFAULT_ARTIFACT_DIRECTORY,
    manifest_path: Path = DEFAULT_MANIFEST,
    hashes_path: Path = DEFAULT_HASHES,
) -> dict[str, object]:
    """Verify local artifact bytes against the tracked candidate identity."""
    manifest = validate_manifest_contract(manifest_path, hashes_path)
    observed = inspect_candidate(artifact_directory)
    if observed["artifacts"] != manifest["artifacts"]:
        _fail("Local artifact bytes differ from the tracked candidate manifest")
    return {
        "status": "passed",
        "candidate_status": manifest["status"],
        **observed,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACT_DIRECTORY)
        if command == "verify":
            subparser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
            subparser.add_argument("--hashes", type=Path, default=DEFAULT_HASHES)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    try:
        report = (
            inspect_candidate(args.artifacts)
            if args.command == "inspect"
            else verify_candidate(args.artifacts, args.manifest, args.hashes)
        )
    except (OSError, CandidateError) as error:
        print(f"local candidate {args.command} failed: {error}")
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
