"""Strict deterministic JSON and SHA-256 primitives for governed hashing."""

from __future__ import annotations

import hashlib
import json

from forge.errors import IntegrityError


def canonical_json_bytes(payload: object) -> bytes:
    """Serialize the approved FORGE canonical JSON profile as UTF-8 bytes."""
    try:
        rendered = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise IntegrityError(f"Value cannot be represented as canonical JSON: {error}") from error
    return rendered.encode("utf-8")


def sha256_digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def canonical_json_digest(payload: object) -> str:
    return sha256_digest(canonical_json_bytes(payload))
