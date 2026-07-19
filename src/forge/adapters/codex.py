"""Read-only discovery and invocation preparation for the installed Codex CLI."""

from __future__ import annotations

import re

from forge.adapters._local_cli import LocalCliAgentAdapter


class CodexAgentAdapter(LocalCliAgentAdapter):
    """Inspect a separately installed Codex CLI without granting it FORGE authority."""

    _adapter_id = "codex"
    _display_name = "OpenAI Codex CLI"
    _provider_name = "Codex CLI"
    _executable_name = "codex"
    _executable_override = "FORGE_CODEX_EXECUTABLE"
    _version_patterns = (
        re.compile(
            r"(?:^|\s)codex(?:-cli)?\s+v?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)\b",
            re.IGNORECASE,
        ),
    )
    _help_arguments = ("exec", "--help")
    _required_help_flags = (
        "--json",
        "--ephemeral",
        "--sandbox",
        "--ask-for-approval",
    )
    _authentication_arguments = ("login", "status")
    _login_command = "codex login"
    _invocation_arguments = (
        "exec",
        "--json",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "never",
        "-",
    )
    _diagnostic_environment_keys = ("CODEX_HOME",)
    _limitations = (
        "FORGE can inspect and prepare Codex but does not start a Codex worker in this increment",
        "Codex preparation is forced to read-only sandboxing with approval prompts disabled",
        "Use manual handoff until isolated output capture and governed runs are implemented",
    )
