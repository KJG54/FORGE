"""Deterministic persistence for individual governed JSON records."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes

MAX_RECORD_BYTES = 10_485_760


def render_record(record: BaseModel) -> bytes:
    payload = json.dumps(
        record.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return payload.encode("utf-8") + b"\n"


def load_record[RecordModel: BaseModel](
    path: Path,
    model: type[RecordModel],
) -> RecordModel:
    if path.is_symlink():
        raise SecurityError(f"Refusing to read a governed record through a symbolic link: {path}")
    if not path.is_file():
        raise IntegrityError(f"Governed record is missing or not a regular file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise IntegrityError(f"Cannot read governed record {path}: {error}") from error
    if len(raw) > MAX_RECORD_BYTES:
        raise IntegrityError(f"Governed record exceeds {MAX_RECORD_BYTES} bytes: {path}")
    try:
        return model.model_validate_json(raw)
    except ValidationError as error:
        raise IntegrityError(f"Invalid governed record {path}: {error}") from error


def write_record(path: Path, record: BaseModel, *, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise ConflictError(f"Refusing to overwrite governed record: {path}")
    rendered = render_record(record)
    if len(rendered) > MAX_RECORD_BYTES:
        raise IntegrityError(f"Governed record exceeds {MAX_RECORD_BYTES} bytes: {path}")

    def validate_temporary(temporary: Path) -> None:
        try:
            restored = type(record).model_validate_json(temporary.read_bytes())
        except (OSError, ValidationError) as error:
            raise IntegrityError(f"Temporary governed record is invalid: {error}") from error
        if restored != record:
            raise IntegrityError("Temporary governed record did not reproduce requested content")

    atomic_write_bytes(path, rendered, validator=validate_temporary)
