"""Exact repository-independent protocol for direct workspace agents."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files

from forge.errors import IntegrityError
from forge.storage.objects import sha256_digest

AGENT_PROTOCOL_VERSION = "1.3.0"
AGENT_PROTOCOL_FILENAME = f"agent-protocol-{AGENT_PROTOCOL_VERSION}.md"
AGENT_PROTOCOL_DIGEST = "sha256:34ee8ddcda6ae147f87caf5863aa4e7ca20c34310807e441b065d8d8553eaa00"


@dataclass(frozen=True)
class AgentProtocol:
    """One exact installed protocol resource and its stable identity."""

    version: str
    filename: str
    digest: str
    content: bytes


def load_agent_protocol() -> AgentProtocol:
    """Load and validate the exact protocol without repository discovery."""

    resource = files("forge.resources").joinpath(AGENT_PROTOCOL_FILENAME)
    try:
        content = resource.read_bytes()
        decoded = content.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise IntegrityError(f"Cannot load installed agent protocol: {error}") from error
    if content.startswith(b"\xef\xbb\xbf") or b"\r" in content:
        raise IntegrityError("Installed agent protocol must use UTF-8 without BOM and LF newlines")
    required_fragments = (
        f"Protocol version: `{AGENT_PROTOCOL_VERSION}`",
        "## First contact and state detection",
        "Detect whether the working environment itself is durable",
        "## Document-first interview",
        "## Exact owner confirmation before bootstrap",
        "## Exact owner-gate command templates",
        "## Bootstrap next action",
        "## Git, delegation, and threat model",
        "For an ordinary gap, run `forge recap`.",
        "Caller attribution is not authentication",
    )
    missing = tuple(fragment for fragment in required_fragments if fragment not in decoded)
    if missing:
        raise IntegrityError(f"Installed agent protocol is incomplete: {', '.join(missing)}")
    digest = sha256_digest(content)
    if digest != AGENT_PROTOCOL_DIGEST:
        raise IntegrityError(
            "Installed agent protocol does not match its versioned expected digest"
        )
    return AgentProtocol(
        version=AGENT_PROTOCOL_VERSION,
        filename=AGENT_PROTOCOL_FILENAME,
        digest=digest,
        content=content,
    )
