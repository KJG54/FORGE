"""Shared constants for the FORGE test suite.

Bundled pack versions are read from the packs themselves rather than repeated as
literals. A pack version bump is a deliberate, reviewed act recorded in the version
contract and in the append-only identity table in `test_profile_aware_guidance.py`;
it should not additionally require editing unrelated CLI and trust assertions.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUNDLED_PACKS = ROOT / "src" / "forge" / "packs" / "bundled"


def bundled_pack_version(pack_id: str) -> str:
    """Return the declared version of a bundled pack manifest."""
    manifest = yaml.safe_load(
        (BUNDLED_PACKS / pack_id / "manifest.yaml").read_text(encoding="utf-8")
    )
    return str(manifest["version"])


SOFTWARE_BASIC_VERSION = bundled_pack_version("software-basic")
RESEARCH_BASIC_VERSION = bundled_pack_version("research-basic")
