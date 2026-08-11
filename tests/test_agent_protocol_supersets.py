"""Protocol 1.4.0 must be a strict superset of the protocol it supersedes.

The supplied facilitation handoff was written against an older mental model and
omits several 1.3.0 requirements. Re-authoring the protocol from that handoff
would silently drop them, so superset-ness is enforced here rather than trusted.

Only the version-declaration line is permitted to differ.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.core.agent_context import generate_agent_context, superseded_protocol_copies
from forge.core.agent_protocol import (
    AGENT_PROTOCOL_DIGEST,
    AGENT_PROTOCOL_FILENAME,
    AGENT_PROTOCOL_VERSION,
    SUPERSEDED_AGENT_PROTOCOL_VERSIONS,
    load_agent_protocol,
)
from forge.core.authorization import owner_actor
from forge.core.diagnostics import inspect_repository_health
from forge.core.lifecycle import create_initiative
from forge.errors import IntegrityError
from forge.storage.objects import sha256_digest
from forge.storage.repository import InitializationResult, initialize_repository

RESOURCES = Path(__file__).resolve().parents[1] / "src" / "forge" / "resources"

# Requirements 1.3.0 introduced that the facilitation handoff never mentions.
CARRIED_FORWARD_REQUIREMENTS = (
    "Detect whether the working environment itself is durable",
    "durable project home",
    "forge pack inspect <pack-id>",
    "preview-required, owner-directed",
    "A workspace agent may cancel only the active run that represents its own current work",
    "First run read-only\n  `forge pack inspect <locked-pack-id>`",
)

# Behaviour 1.4.0 adds on top.
NEW_REQUIREMENTS = (
    "## Profile-aware collaboration and learning",
    "## Phase presentation and collaboration task map",
    "Never assume an unrelated `forge` command is this framework",
    "Report the skew and reconcile it before relying on either",
    "Collaboration style is conversational and ungoverned",
    "A task map is presentation. It never redefines authority",
)


def _read(version: str) -> str:
    return (RESOURCES / f"agent-protocol-{version}.md").read_text(encoding="utf-8")


def test_superseded_protocol_resources_are_still_shipped() -> None:
    for version in SUPERSEDED_AGENT_PROTOCOL_VERSIONS:
        resource = RESOURCES / f"agent-protocol-{version}.md"

        assert resource.is_file(), f"superseded protocol {version} must remain shipped"


def test_current_protocol_contains_every_line_of_the_superseded_protocol() -> None:
    current_lines = _read(AGENT_PROTOCOL_VERSION).splitlines()

    for version in SUPERSEDED_AGENT_PROTOCOL_VERSIONS:
        previous_lines = _read(version).splitlines()
        version_declaration = f"Protocol version: `{version}`"

        missing = [
            line
            for line in previous_lines
            if line != version_declaration and line not in current_lines
        ]

        assert not missing, (
            f"protocol {AGENT_PROTOCOL_VERSION} dropped {len(missing)} line(s) present in "
            f"{version}; the first is {missing[0]!r}"
        )


def test_current_protocol_preserves_named_requirements_of_the_superseded_protocol() -> None:
    current = _read(AGENT_PROTOCOL_VERSION)

    for requirement in CARRIED_FORWARD_REQUIREMENTS:
        assert requirement in current, (
            f"protocol {AGENT_PROTOCOL_VERSION} lost a requirement carried from an "
            f"earlier protocol: {requirement!r}"
        )


def test_current_protocol_declares_its_own_new_behaviour() -> None:
    current = _read(AGENT_PROTOCOL_VERSION)

    for requirement in NEW_REQUIREMENTS:
        assert requirement in current, requirement


def test_current_protocol_declares_only_its_own_version() -> None:
    current = _read(AGENT_PROTOCOL_VERSION)

    assert f"Protocol version: `{AGENT_PROTOCOL_VERSION}`" in current
    for version in SUPERSEDED_AGENT_PROTOCOL_VERSIONS:
        assert f"Protocol version: `{version}`" not in current


@pytest.mark.parametrize("version", (AGENT_PROTOCOL_VERSION, *SUPERSEDED_AGENT_PROTOCOL_VERSIONS))
def test_every_shipped_protocol_uses_utf8_without_bom_and_lf_newlines(version: str) -> None:
    content = (RESOURCES / f"agent-protocol-{version}.md").read_bytes()

    assert not content.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in content


def test_loaded_protocol_matches_its_pinned_identity() -> None:
    protocol = load_agent_protocol()

    assert protocol.version == AGENT_PROTOCOL_VERSION
    assert protocol.filename == AGENT_PROTOCOL_FILENAME
    assert protocol.digest == AGENT_PROTOCOL_DIGEST
    assert sha256_digest(protocol.content) == AGENT_PROTOCOL_DIGEST


def test_doctor_reports_no_protocol_skew_before_context_generation(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")

    report = inspect_repository_health(initialized.layout)

    assert (
        f"agent protocol {AGENT_PROTOCOL_VERSION} installed; no repository source or "
        "generated context"
        in report.checks
    )
    assert not _protocol_context_skew_warnings(report.warnings)


def test_doctor_reports_matching_protocol_after_context_generation(tmp_path: Path) -> None:
    initialized = _initialized_initiative(tmp_path)
    generate_agent_context(initialized.layout)

    report = inspect_repository_health(initialized.layout)

    assert (
        f"agent protocol {AGENT_PROTOCOL_VERSION} matches generated context" in report.checks
    )
    assert not _protocol_context_skew_warnings(report.warnings)


def test_doctor_refuses_when_installed_protocol_is_older_than_repository_source(
    tmp_path: Path,
) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    source = tmp_path / "src" / "forge" / "core"
    source.mkdir(parents=True)
    (source / "agent_protocol.py").write_text(
        'AGENT_PROTOCOL_VERSION = "9.0.0"\n',
        encoding="utf-8",
    )

    with pytest.raises(IntegrityError, match=r"older than repository source protocol 9\.0\.0"):
        inspect_repository_health(initialized.layout)


def test_doctor_cli_reports_source_protocol_skew_as_non_healthy(tmp_path: Path) -> None:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    source = tmp_path / "src" / "forge" / "core"
    source.mkdir(parents=True)
    (source / "agent_protocol.py").write_text(
        'AGENT_PROTOCOL_VERSION = "9.0.0"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["doctor", "-C", str(initialized.layout.root)])

    assert result.exit_code == 30
    assert "older than repository source protocol 9.0.0" in result.stderr
    assert "FORGE repository health: healthy" not in result.stdout


def test_doctor_reports_a_distinct_diagnostic_when_the_generated_protocol_is_superseded(
    tmp_path: Path,
) -> None:
    initialized = _initialized_initiative(tmp_path)
    generate_agent_context(initialized.layout)
    context_directory = initialized.layout.agent_context_directory
    current = context_directory / f"agent-protocol-{AGENT_PROTOCOL_VERSION}.md"
    # Simulate a repository whose context was generated by a different CLI build.
    current.rename(context_directory / "agent-protocol-0.9.0.md")

    report = inspect_repository_health(initialized.layout)

    assert (
        f"agent protocol {AGENT_PROTOCOL_VERSION} checked against the generated context"
        in report.checks
    )
    skew = _protocol_context_skew_warnings(report.warnings)
    assert len(skew) == 1
    assert "0.9.0" in skew[0]
    assert AGENT_PROTOCOL_VERSION in skew[0]
    assert "forge agent context" in skew[0]


def test_regeneration_removes_a_superseded_generated_protocol_copy(tmp_path: Path) -> None:
    initialized = _initialized_initiative(tmp_path)
    generate_agent_context(initialized.layout)
    context_directory = initialized.layout.agent_context_directory
    stale = context_directory / "agent-protocol-0.9.0.md"
    stale.write_text("superseded copy from an earlier build\n", encoding="utf-8")

    assert superseded_protocol_copies(initialized.layout) == (stale,)

    generate_agent_context(initialized.layout)

    assert not stale.exists()
    assert (context_directory / AGENT_PROTOCOL_FILENAME).is_file()
    assert superseded_protocol_copies(initialized.layout) == ()
    report = inspect_repository_health(initialized.layout)
    assert not _protocol_context_skew_warnings(report.warnings)


def _initialized_initiative(tmp_path: Path) -> InitializationResult:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    create_initiative(
        initialized.layout,
        objective="Produce a bounded implementation",
        declared_scope_summary="Only the accepted workflow outputs",
        actor=owner_actor(initialized.configuration.owner),
        trust_pack_data=True,
    )
    return initialized


def _protocol_context_skew_warnings(warnings: tuple[str, ...]) -> list[str]:
    return [
        warning
        for warning in warnings
        if warning.startswith("Generated agent context still carries protocol ")
    ]
