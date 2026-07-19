"""Read-only discovery and invocation preparation for installed Claude Code."""

from __future__ import annotations

import re

from forge.adapters._local_cli import LocalCliAgentAdapter


class ClaudeAgentAdapter(LocalCliAgentAdapter):
    """Inspect separately installed Claude Code without granting it FORGE authority."""

    _adapter_id = "claude"
    _display_name = "Anthropic Claude Code"
    _provider_name = "Claude Code"
    _executable_name = "claude"
    _executable_override = "FORGE_CLAUDE_EXECUTABLE"
    _version_patterns = (
        re.compile(
            r"(?:^|\s)claude(?:-code)?\s+v?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:^|\s)v?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)\s+\(Claude Code\)",
            re.IGNORECASE,
        ),
    )
    _help_arguments = ("--help",)
    _required_help_flags = (
        "--print",
        "--input-format",
        "--output-format",
        "--permission-mode",
        "--no-session-persistence",
        "--bare",
        "--tools",
        "--strict-mcp-config",
        "--no-chrome",
    )
    _authentication_arguments = ("auth", "status")
    _login_command = "claude auth login"
    _invocation_arguments = (
        "--print",
        "--input-format",
        "text",
        "--output-format",
        "stream-json",
        "--permission-mode",
        "plan",
        "--no-session-persistence",
        "--bare",
        "--tools",
        "Read,Glob,Grep",
        "--strict-mcp-config",
        "--no-chrome",
    )
    _diagnostic_environment_keys = ("CLAUDE_CONFIG_DIR",)
    _limitations = (
        "FORGE can inspect and prepare Claude but does not start a Claude worker in this increment",
        "Claude preparation disables writes, prompts, sessions, extensions, MCP, and browser "
        "access",
        "Use manual handoff until isolated output capture and governed runs are implemented",
    )
