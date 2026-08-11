"""The starter prompts must route a fresh agent to the current protocol.

These prompts are pasted into agents that know nothing about FORGE, so they are
the only thing standing between a fresh agent and a wrong `forge` tool. They were
authored against an older protocol; this module keeps them in step with the one
actually installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.core.agent_protocol import load_agent_protocol

ROOT = Path(__file__).resolve().parents[1]
STARTER_PROMPTS = ROOT / "docs" / "agent-starter-prompts.md"
OFFICIAL_REPOSITORY = "https://github.com/KJG54/FORGE"

# Routing essentials: without these a fresh agent cannot find FORGE at all.
ROUTING_REQUIREMENTS = (
    OFFICIAL_REPOSITORY,
    "Framework for Orchestrated Reasoning, Governance, and Execution",
    "forge --version",
    "forge agent protocol",
)

# Behaviour the installed protocol requires of a direct workspace agent.
PROTOCOL_REQUIREMENTS = (
    "document-first interview",
    "durably lives",
    "forge pack inspect",
    "skew",
    "owner-only",
    "preview",
)


def _prompt_text() -> str:
    return STARTER_PROMPTS.read_text(encoding="utf-8")


@pytest.mark.parametrize("requirement", ROUTING_REQUIREMENTS)
def test_starter_prompts_route_a_fresh_agent_to_forge(requirement: str) -> None:
    assert requirement in _prompt_text(), requirement


@pytest.mark.parametrize("requirement", PROTOCOL_REQUIREMENTS)
def test_starter_prompts_cover_current_protocol_behaviour(requirement: str) -> None:
    assert requirement.lower() in _prompt_text().lower(), requirement


def test_starter_prompts_warn_against_an_unrelated_forge_tool() -> None:
    text = _prompt_text().lower()

    assert "do not assume" in text
    assert "generic" in text or "different" in text or "another forge" in text


def test_starter_prompts_never_authorize_an_owner_gate() -> None:
    """A prompt may name the owner gates, but must never pre-authorize them."""
    text = _prompt_text()

    for gate in ("forge init", "forge pack trust", "forge create"):
        assert gate in text, gate

    assert "explicitly authorize" in text or "explicit authorization" in text
    # The gate commands must never appear as ready-to-run vectors with arguments.
    assert "--owner-name" not in text
    assert "--trust-pack-data" not in text


def test_starter_prompts_describe_the_collaboration_task_map() -> None:
    text = _prompt_text().lower()

    for party in ("owner tasks", "agent tasks", "either-party"):
        assert party in text, party


def test_every_prompt_block_is_closed() -> None:
    """Unbalanced fences would truncate a prompt when an owner copies it."""
    fences = _prompt_text().count("```")

    assert fences % 2 == 0, "starter prompt code fences are unbalanced"


def test_starter_prompts_do_not_pin_a_superseded_protocol_version() -> None:
    """Naming an exact version here would go stale on every protocol bump."""
    protocol = load_agent_protocol()
    text = _prompt_text()

    for candidate in ("1.0.0", "1.1.0", "1.2.0", "1.3.0", "1.4.0"):
        if candidate == protocol.version:
            continue
        assert f"protocol {candidate}" not in text, candidate
