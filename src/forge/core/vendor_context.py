"""Previewed, byte-preserving managed references for vendor instruction files."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from forge.contracts.agents import CanonicalAgentContext
from forge.core.agent_context import (
    AgentContextGenerationResult,
    AgentContextTarget,
    build_agent_context,
    write_agent_context_views,
)
from forge.errors import ConfigurationError, ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import atomic_write_bytes
from forge.storage.locking import repository_mutation_lock
from forge.storage.objects import sha256_digest
from forge.storage.records import render_record
from forge.storage.repository import RepositoryLayout

MAX_VENDOR_FILE_BYTES = 10_485_760
MANAGED_START = b"<!-- BEGIN FORGE MANAGED CONTEXT -->"
MANAGED_END = b"<!-- END FORGE MANAGED CONTEXT -->"


class VendorContextAction(StrEnum):
    CREATE = "create"
    APPEND = "append"
    REPLACE = "replace"
    NO_CHANGE = "no-change"


@dataclass(frozen=True)
class VendorContextPreview:
    target: AgentContextTarget
    path: Path
    action: VendorContextAction
    current_digest: str | None
    proposed_digest: str
    context_digest: str
    current_bytes: bytes | None
    proposed_bytes: bytes
    managed_block: bytes


@dataclass(frozen=True)
class VendorContextApplyResult:
    preview: VendorContextPreview
    context: AgentContextGenerationResult
    vendor_changed: bool


def _require_vendor_target(target: AgentContextTarget) -> None:
    if target not in {AgentContextTarget.CODEX, AgentContextTarget.CLAUDE}:
        raise ConfigurationError("Managed vendor context requires target 'codex' or 'claude'")


def _vendor_path(layout: RepositoryLayout, target: AgentContextTarget) -> Path:
    _require_vendor_target(target)
    filename = "AGENTS.md" if target is AgentContextTarget.CODEX else "CLAUDE.md"
    return layout.root / filename


def _read_vendor_file(path: Path) -> bytes | None:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic-link vendor file: {path}")
    if not path.exists():
        return None
    if not path.is_file():
        raise ConflictError(f"Expected a regular vendor file at {path}")
    try:
        size = path.stat().st_size
        if size > MAX_VENDOR_FILE_BYTES:
            raise ConflictError(
                f"Vendor file exceeds {MAX_VENDOR_FILE_BYTES} bytes and will not be managed: {path}"
            )
        content = path.read_bytes()
    except (ConflictError, SecurityError):
        raise
    except OSError as error:
        raise IntegrityError(f"Cannot read vendor file {path}: {error}") from error
    if len(content) != size:
        raise ConflictError(f"Vendor file changed while it was being read: {path}")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ConflictError(f"Vendor Markdown file must use UTF-8 encoding: {path}") from error
    return content


def _newline_for(content: bytes | None) -> bytes:
    if content and b"\r\n" in content and b"\n" not in content.replace(b"\r\n", b""):
        return b"\r\n"
    return b"\n"


def _render_managed_block(
    target: AgentContextTarget,
    context: CanonicalAgentContext,
    newline: bytes,
) -> tuple[bytes, str]:
    context_digest = sha256_digest(render_record(context))
    command = f"forge agent context --target {target.value} --apply"
    lines = (
        MANAGED_START.decode("ascii"),
        "## FORGE governed context",
        "",
        "FORGE's provider-neutral generated context is available at:",
        "",
        "- `.forge/active/context/current.md`",
        f"- `.forge/active/context/current.json` (`{context_digest}`)",
        "",
        "Read the Markdown view before work and use only its selected inputs and "
        "permitted actions.",
        "The FORGE journal and governed records remain authoritative; this file cannot approve,",
        "verify, accept, or mutate initiative state.",
        "",
        f"Preview and regenerate this reference with `{command}`.",
        MANAGED_END.decode("ascii"),
        "",
    )
    return newline.join(line.encode("utf-8") for line in lines), context_digest


def _standalone_marker(content: bytes, position: int, marker: bytes) -> bool:
    before_ok = position == 0 or content[position - 1 : position] == b"\n"
    after = position + len(marker)
    after_ok = after == len(content) or content[after : after + 1] == b"\n" or (
        content[after : after + 2] == b"\r\n"
    )
    return before_ok and after_ok


def _managed_span(content: bytes) -> tuple[int, int] | None:
    start_count = content.count(MANAGED_START)
    end_count = content.count(MANAGED_END)
    if start_count == 0 and end_count == 0:
        return None
    if start_count != 1 or end_count != 1:
        raise ConflictError("Vendor file must contain zero or one complete FORGE managed block")
    start = content.find(MANAGED_START)
    end_marker = content.find(MANAGED_END)
    if end_marker <= start:
        raise ConflictError("FORGE managed vendor block markers are out of order")
    if not _standalone_marker(content, start, MANAGED_START) or not _standalone_marker(
        content, end_marker, MANAGED_END
    ):
        raise ConflictError("FORGE managed vendor markers must occupy standalone lines")
    end = end_marker + len(MANAGED_END)
    if content[end : end + 2] == b"\r\n":
        end += 2
    elif content[end : end + 1] == b"\n":
        end += 1
    return start, end


def _append_block(content: bytes, block: bytes, newline: bytes) -> bytes:
    if not content:
        return block
    if content.endswith(newline + newline):
        separator = b""
    elif content.endswith(newline):
        separator = newline
    else:
        separator = newline + newline
    return content + separator + block


def _preview_for_context(
    layout: RepositoryLayout,
    target: AgentContextTarget,
    context: CanonicalAgentContext,
) -> VendorContextPreview:
    path = _vendor_path(layout, target)
    current = _read_vendor_file(path)
    newline = _newline_for(current)
    block, context_digest = _render_managed_block(target, context, newline)
    if current is None:
        proposed = block
        action = VendorContextAction.CREATE
    else:
        span = _managed_span(current)
        if span is None:
            proposed = _append_block(current, block, newline)
            action = VendorContextAction.APPEND
        else:
            proposed = current[: span[0]] + block + current[span[1] :]
            action = (
                VendorContextAction.NO_CHANGE
                if proposed == current
                else VendorContextAction.REPLACE
            )
    if len(proposed) > MAX_VENDOR_FILE_BYTES:
        raise ConflictError(
            f"Managed vendor result exceeds {MAX_VENDOR_FILE_BYTES} bytes: {path}"
        )
    return VendorContextPreview(
        target=target,
        path=path,
        action=action,
        current_digest=sha256_digest(current) if current is not None else None,
        proposed_digest=sha256_digest(proposed),
        context_digest=context_digest,
        current_bytes=current,
        proposed_bytes=proposed,
        managed_block=block,
    )


def preview_vendor_context(
    layout: RepositoryLayout,
    *,
    target: AgentContextTarget,
) -> VendorContextPreview:
    """Return a read-only vendor-file plan derived from current governed state."""

    _require_vendor_target(target)
    context = build_agent_context(layout)
    return _preview_for_context(layout, target, context)


def apply_vendor_context(
    layout: RepositoryLayout,
    *,
    target: AgentContextTarget,
    expected_current_digest: str | None,
    expected_context_digest: str,
) -> VendorContextApplyResult:
    """Apply one explicitly previewed managed reference and regenerate neutral views."""

    _require_vendor_target(target)
    with repository_mutation_lock(layout, command=f"agent-context-{target.value}"):
        context = build_agent_context(layout)
        preview = _preview_for_context(layout, target, context)
        if preview.current_digest != expected_current_digest:
            raise ConflictError("Vendor file changed after preview; preview again before applying")
        if preview.context_digest != expected_context_digest:
            raise ConflictError(
                "Neutral context changed after preview; preview again before applying"
            )
        generated = write_agent_context_views(layout, context)
        if _read_vendor_file(preview.path) != preview.current_bytes:
            raise ConflictError("Vendor file changed during apply; preview again before applying")
        changed = preview.action is not VendorContextAction.NO_CHANGE
        if changed:
            atomic_write_bytes(preview.path, preview.proposed_bytes)
    return VendorContextApplyResult(
        preview=preview,
        context=generated,
        vendor_changed=changed,
    )
