import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.contracts import CONTRACT_MODELS
from forge.core.agent_context import AgentContextTarget, generate_agent_context
from forge.core.agent_protocol import AGENT_PROTOCOL_DIGEST, load_agent_protocol
from forge.core.authorization import owner_actor
from forge.core.lifecycle import create_initiative
from forge.core.vendor_context import (
    MANAGED_END,
    MANAGED_START,
    VendorContextAction,
    apply_vendor_context,
    preview_vendor_context,
)
from forge.errors import SecurityError
from forge.storage.objects import sha256_digest
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> InitializationResult:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Deliver a bounded first milestone",
        declared_scope_summary="Only the reviewed first milestone",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized


def test_protocol_command_works_before_repository_initialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    protocol = load_agent_protocol()

    result = runner.invoke(app, ["agent", "protocol"])

    assert result.exit_code == 0
    assert f"FORGE agent protocol version: {protocol.version}" in result.stdout
    assert f"Protocol digest: {protocol.digest}" in result.stdout
    assert protocol.content.decode("utf-8") in result.stdout
    assert not (tmp_path / "forge.yaml").exists()
    assert not (tmp_path / ".forge").exists()


def test_protocol_is_exact_and_covers_the_l2_bootstrap_contract() -> None:
    protocol = load_agent_protocol()
    text = protocol.content.decode("utf-8")

    assert protocol.filename == "agent-protocol-1.0.0.md"
    assert protocol.digest == AGENT_PROTOCOL_DIGEST == sha256_digest(protocol.content)
    assert len(CONTRACT_MODELS) == 51
    for required in (
        "forge --version",
        "forge agent protocol",
        "Document-first interview",
        "product vision and intended users",
        "first milestone objective and definition of done",
        "standing labor split",
        "abandonment conditions",
        "Ask focused follow-ups for those gaps",
        "Exact owner confirmation before bootstrap",
        "forge init <repository> --owner-name <display-name>",
        "--trust-pack-data",
        "Bootstrap next action",
        "forge agent context --target <codex|claude> --apply",
        "same-user threat model",
    ):
        assert required in text


def test_neutral_context_installs_the_exact_protocol_without_governance_events(
    tmp_path: Path,
) -> None:
    initialized = _initiative(tmp_path)
    protocol = load_agent_protocol()
    journal_before = initialized.layout.event_journal_file.read_bytes()

    result = generate_agent_context(initialized.layout)

    assert result.protocol_version == protocol.version
    assert result.protocol_digest == protocol.digest
    assert result.protocol_path.name == protocol.filename
    assert result.protocol_path.read_bytes() == protocol.content
    assert initialized.layout.event_journal_file.read_bytes() == journal_before


@pytest.mark.parametrize("target", (AgentContextTarget.CODEX, AgentContextTarget.CLAUDE))
def test_managed_vendor_reference_binds_and_installs_protocol(
    tmp_path: Path,
    target: AgentContextTarget,
) -> None:
    initialized = _initiative(tmp_path)
    protocol = load_agent_protocol()

    preview = preview_vendor_context(initialized.layout, target=target)

    assert preview.protocol_version == protocol.version
    assert preview.protocol_digest == protocol.digest
    assert f".forge/active/context/{protocol.filename}".encode() in preview.managed_block
    assert protocol.digest.encode() in preview.managed_block
    assert f"Protocol version: `{protocol.version}`".encode() in preview.managed_block

    applied = apply_vendor_context(
        initialized.layout,
        target=target,
        expected_current_digest=preview.current_digest,
        expected_context_digest=preview.context_digest,
    )

    assert applied.context.protocol_path.read_bytes() == protocol.content
    assert applied.preview.path.read_bytes() == preview.proposed_bytes


def test_legacy_managed_span_refresh_preserves_owner_bytes_and_newlines(
    tmp_path: Path,
) -> None:
    initialized = _initiative(tmp_path)
    vendor_path = tmp_path / "AGENTS.md"
    owner_prefix = b"# Owner instructions\r\n\r\nKeep this exact prefix.\r\n\r\n"
    legacy_block = (
        MANAGED_START
        + b"\r\n## FORGE governed context\r\n\r\n"
        + b"Legacy managed reference.\r\n"
        + MANAGED_END
        + b"\r\n"
    )
    owner_suffix = b"\r\n## Owner suffix\r\nKeep this exact suffix.\r\n"
    vendor_path.write_bytes(owner_prefix + legacy_block + owner_suffix)

    preview = preview_vendor_context(initialized.layout, target=AgentContextTarget.CODEX)

    assert preview.action is VendorContextAction.REPLACE
    assert preview.proposed_bytes.startswith(owner_prefix)
    assert preview.proposed_bytes.endswith(owner_suffix)
    assert b"\n" not in preview.managed_block.replace(b"\r\n", b"")
    apply_vendor_context(
        initialized.layout,
        target=AgentContextTarget.CODEX,
        expected_current_digest=preview.current_digest,
        expected_context_digest=preview.context_digest,
    )
    refreshed = vendor_path.read_bytes()
    assert refreshed.startswith(owner_prefix)
    assert refreshed.endswith(owner_suffix)
    assert refreshed.count(MANAGED_START) == 1
    assert refreshed.count(MANAGED_END) == 1


def test_symbolic_protocol_target_is_refused_when_supported(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    protocol = load_agent_protocol()
    initialized.layout.agent_context_directory.mkdir()
    outside = tmp_path / "outside-protocol.md"
    outside.write_bytes(b"OWNER_OUTSIDE_SENTINEL")
    protocol_path = initialized.layout.agent_context_directory / protocol.filename
    try:
        os.symlink(outside, protocol_path)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")

    with pytest.raises(SecurityError, match="symbolic-link context view"):
        generate_agent_context(initialized.layout)

    assert outside.read_bytes() == b"OWNER_OUTSIDE_SENTINEL"
    assert not initialized.layout.current_agent_context_json_file.exists()
    assert not initialized.layout.current_agent_context_markdown_file.exists()
