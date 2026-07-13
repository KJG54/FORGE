"""Deterministic, non-destructive JSON Schema bundle export."""

import json
from pathlib import Path

from forge.contracts import CONTRACT_MODELS, SCHEMA_VERSION
from forge.errors import ConflictError


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def schema_bundle() -> dict[str, bytes]:
    """Build the deterministic file set without touching the filesystem."""
    files = {
        f"{name}.schema.json": _json_bytes(model.model_json_schema(mode="validation"))
        for name, model in sorted(CONTRACT_MODELS.items())
    }
    files["index.json"] = _json_bytes(
        {
            "schema_version": SCHEMA_VERSION,
            "schemas": {
                name: f"{name}.schema.json" for name in sorted(CONTRACT_MODELS)
            },
        }
    )
    return files


def export_schema_bundle(output_directory: Path, *, overwrite: bool = False) -> tuple[Path, ...]:
    """Export all public schemas, refusing unrelated conflicting bytes by default."""
    destination = output_directory.resolve()
    if destination.exists() and not destination.is_dir():
        raise ConflictError(f"Schema destination is not a directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    bundle = schema_bundle()
    conflicts = [
        destination / name
        for name, content in bundle.items()
        if (destination / name).exists()
        and (destination / name).read_bytes() != content
        and not overwrite
    ]
    if conflicts:
        joined = ", ".join(path.name for path in conflicts)
        raise ConflictError(
            f"Refusing to overwrite changed schema files: {joined}. Use --force to replace them."
        )

    written: list[Path] = []
    for name, content in bundle.items():
        target = destination / name
        if not target.exists() or target.read_bytes() != content:
            target.write_bytes(content)
        written.append(target)
    return tuple(written)
