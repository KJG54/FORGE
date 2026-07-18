import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli.app import app
from forge.core.agent_context import AgentContextTarget
from forge.core.authorization import owner_actor
from forge.core.decisions import record_decision
from forge.core.lifecycle import create_initiative
from forge.core.vendor_context import (
    MANAGED_END,
    MANAGED_START,
    MAX_VENDOR_FILE_BYTES,
    VendorContextAction,
    apply_vendor_context,
    preview_vendor_context,
)
from forge.errors import ConflictError, SecurityError
from forge.storage.objects import sha256_digest
from forge.storage.repository import InitializationResult, initialize_repository

runner = CliRunner()


def _initiative(tmp_path: Path) -> InitializationResult:
    initialized = initialize_repository(tmp_path, owner_display_name="Repository Owner")
    actor = owner_actor(initialized.configuration.owner)
    create_initiative(
        initialized.layout,
        objective="Produce managed vendor context",
        declared_scope_summary="Only bounded vendor references",
        actor=actor,
        trust_pack_data=True,
    )
    return initialized


def _apply(initialized: InitializationResult, target: AgentContextTarget):
    preview = preview_vendor_context(initialized.layout, target=target)
    return apply_vendor_context(
        initialized.layout,
        target=target,
        expected_current_digest=preview.current_digest,
        expected_context_digest=preview.context_digest,
    )


def test_codex_preview_is_non_mutating_and_apply_is_idempotent(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    journal_before = initialized.layout.event_journal_file.read_bytes()
    vendor_path = tmp_path / "AGENTS.md"

    preview = preview_vendor_context(initialized.layout, target=AgentContextTarget.CODEX)

    assert preview.action is VendorContextAction.CREATE
    assert preview.current_digest is None
    assert not vendor_path.exists()
    assert not initialized.layout.agent_context_directory.exists()
    assert preview.context_digest.encode() in preview.managed_block
    assert b".forge/active/context/current.md" in preview.managed_block
    assert b"--target codex --apply" in preview.managed_block

    applied = apply_vendor_context(
        initialized.layout,
        target=AgentContextTarget.CODEX,
        expected_current_digest=preview.current_digest,
        expected_context_digest=preview.context_digest,
    )

    assert applied.vendor_changed
    assert vendor_path.read_bytes() == preview.proposed_bytes
    assert sha256_digest(applied.context.json_path.read_bytes()) == preview.context_digest
    assert initialized.layout.event_journal_file.read_bytes() == journal_before
    first_bytes = vendor_path.read_bytes()

    second_preview = preview_vendor_context(
        initialized.layout, target=AgentContextTarget.CODEX
    )
    assert second_preview.action is VendorContextAction.NO_CHANGE
    second = apply_vendor_context(
        initialized.layout,
        target=AgentContextTarget.CODEX,
        expected_current_digest=second_preview.current_digest,
        expected_context_digest=second_preview.context_digest,
    )
    assert not second.vendor_changed
    assert vendor_path.read_bytes() == first_bytes


def test_existing_crlf_user_content_and_tail_are_preserved_exactly(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    actor = owner_actor(initialized.configuration.owner)
    vendor_path = tmp_path / "AGENTS.md"
    user_prefix = b"# User instructions\r\n\r\nKeep this exact.\r\n"
    vendor_path.write_bytes(user_prefix)

    first = _apply(initialized, AgentContextTarget.CODEX)
    first_bytes = vendor_path.read_bytes()

    assert first.preview.action is VendorContextAction.APPEND
    assert first_bytes.startswith(user_prefix)
    assert b"\r\n" in first.preview.managed_block
    assert b"\n" not in first.preview.managed_block.replace(b"\r\n", b"")

    user_tail = b"# User tail\r\nPreserve after the managed block.\r\n"
    vendor_path.write_bytes(first_bytes + user_tail)
    record_decision(
        initialized.layout,
        decision_type="vendor-refresh",
        question="Should the context reference be refreshed?",
        considered_options=("Refresh", "Leave stale"),
        chosen_outcome="Refresh",
        rationale="Bind the reference to the current neutral context",
        actor=actor,
    )

    preview = preview_vendor_context(initialized.layout, target=AgentContextTarget.CODEX)
    assert preview.action is VendorContextAction.REPLACE
    apply_vendor_context(
        initialized.layout,
        target=AgentContextTarget.CODEX,
        expected_current_digest=preview.current_digest,
        expected_context_digest=preview.context_digest,
    )
    refreshed = vendor_path.read_bytes()
    assert refreshed.startswith(user_prefix)
    assert refreshed.endswith(user_tail)
    assert refreshed.count(MANAGED_START) == 1
    assert refreshed.count(MANAGED_END) == 1
    assert preview.context_digest.encode() in refreshed


def test_claude_target_does_not_modify_agents_file(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    agents_path = tmp_path / "AGENTS.md"
    agents_bytes = b"# User-owned Codex instructions\n"
    agents_path.write_bytes(agents_bytes)

    result = _apply(initialized, AgentContextTarget.CLAUDE)

    assert result.preview.path == tmp_path / "CLAUDE.md"
    assert b"--target claude --apply" in result.preview.managed_block
    assert (tmp_path / "CLAUDE.md").read_bytes() == result.preview.proposed_bytes
    assert agents_path.read_bytes() == agents_bytes


@pytest.mark.parametrize(
    "content",
    (
        MANAGED_START + b"\nmissing end\n",
        MANAGED_END + b"\nmissing start\n",
        MANAGED_START
        + b"\nfirst\n"
        + MANAGED_END
        + b"\n"
        + MANAGED_START
        + b"\nsecond\n"
        + MANAGED_END
        + b"\n",
        b"inline " + MANAGED_START + b"\ncontent\n" + MANAGED_END + b"\n",
    ),
)
def test_malformed_or_ambiguous_managed_markers_are_refused(
    tmp_path: Path,
    content: bytes,
) -> None:
    initialized = _initiative(tmp_path)
    vendor_path = tmp_path / "AGENTS.md"
    vendor_path.write_bytes(content)

    with pytest.raises(ConflictError, match=r"managed|markers"):
        preview_vendor_context(initialized.layout, target=AgentContextTarget.CODEX)
    assert vendor_path.read_bytes() == content
    assert not initialized.layout.agent_context_directory.exists()


def test_vendor_change_after_preview_is_refused_without_context_writes(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    preview = preview_vendor_context(initialized.layout, target=AgentContextTarget.CODEX)
    changed = b"# User edited after preview\n"
    (tmp_path / "AGENTS.md").write_bytes(changed)

    with pytest.raises(ConflictError, match="changed after preview"):
        apply_vendor_context(
            initialized.layout,
            target=AgentContextTarget.CODEX,
            expected_current_digest=preview.current_digest,
            expected_context_digest=preview.context_digest,
        )
    assert (tmp_path / "AGENTS.md").read_bytes() == changed
    assert not initialized.layout.agent_context_directory.exists()


@pytest.mark.parametrize(
    ("content", "message"),
    (
        (b"\xff\xfe", "UTF-8"),
        (b"x" * MAX_VENDOR_FILE_BYTES, "Managed vendor result exceeds"),
    ),
    ids=("non-utf8", "result-too-large"),
)
def test_unmanageable_vendor_content_is_refused_without_replacement(
    tmp_path: Path,
    content: bytes,
    message: str,
) -> None:
    initialized = _initiative(tmp_path)
    path = tmp_path / "AGENTS.md"
    path.write_bytes(content)

    with pytest.raises(ConflictError, match=message):
        preview_vendor_context(initialized.layout, target=AgentContextTarget.CODEX)
    assert path.read_bytes() == content


def test_neutral_context_change_after_preview_is_refused(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    actor = owner_actor(initialized.configuration.owner)
    preview = preview_vendor_context(initialized.layout, target=AgentContextTarget.CODEX)
    record_decision(
        initialized.layout,
        decision_type="context-change",
        question="Change the neutral context?",
        considered_options=("Yes", "No"),
        chosen_outcome="Yes",
        rationale="Exercise preview binding",
        actor=actor,
    )

    with pytest.raises(ConflictError, match="Neutral context changed after preview"):
        apply_vendor_context(
            initialized.layout,
            target=AgentContextTarget.CODEX,
            expected_current_digest=preview.current_digest,
            expected_context_digest=preview.context_digest,
        )
    assert not (tmp_path / "AGENTS.md").exists()
    assert not initialized.layout.agent_context_directory.exists()


def test_vendor_symlink_is_rejected_when_supported(tmp_path: Path) -> None:
    initialized = _initiative(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_bytes(b"outside")
    vendor_path = tmp_path / "AGENTS.md"
    try:
        os.symlink(outside, vendor_path)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")

    with pytest.raises(SecurityError, match="symbolic-link vendor"):
        preview_vendor_context(initialized.layout, target=AgentContextTarget.CODEX)
    assert outside.read_bytes() == b"outside"


def test_vendor_cli_previews_then_requires_apply(tmp_path: Path) -> None:
    _initiative(tmp_path)

    preview = runner.invoke(
        app,
        ["agent", "context", "--target", "codex", "-C", str(tmp_path)],
    )
    assert preview.exit_code == 0
    assert "Action: create" in preview.stdout
    assert "Preview only" in preview.stdout
    assert not (tmp_path / "AGENTS.md").exists()

    applied = runner.invoke(
        app,
        ["agent", "context", "--target", "codex", "--apply", "-C", str(tmp_path)],
    )
    assert applied.exit_code == 0
    assert "Updated:" in applied.stdout
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / ".forge" / "active" / "context" / "current.json").is_file()

    repeated = runner.invoke(
        app,
        ["agent", "context", "--target", "codex", "--apply", "-C", str(tmp_path)],
    )
    assert repeated.exit_code == 0
    assert "Action: no-change" in repeated.stdout
    assert "Already current:" in repeated.stdout

    invalid = runner.invoke(
        app,
        ["agent", "context", "--target", "neutral", "--apply", "-C", str(tmp_path)],
    )
    assert invalid.exit_code != 0
    assert "only valid for codex or claude" in invalid.stderr


def test_cli_preview_never_echoes_existing_user_content(tmp_path: Path) -> None:
    _initiative(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        "USER_VENDOR_CONTENT_SENTINEL\n", encoding="utf-8"
    )

    preview = runner.invoke(
        app,
        ["agent", "context", "--target", "codex", "-C", str(tmp_path)],
    )

    assert preview.exit_code == 0
    assert "Action: append" in preview.stdout
    assert "USER_VENDOR_CONTENT_SENTINEL" not in preview.stdout
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == (
        "USER_VENDOR_CONTENT_SENTINEL\n"
    )
