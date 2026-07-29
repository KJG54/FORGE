from __future__ import annotations

import builtins
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from forge import __version__
from forge.cli import entrypoint


def test_exact_version_request_avoids_full_application_import(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> object:
        if name == "forge.cli.app":
            raise AssertionError("exact version request imported the full CLI application")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(sys, "argv", ["forge", "--version"])

    entrypoint.main()

    assert capsys.readouterr().out == f"{__version__}\n"


def test_non_version_request_delegates_to_full_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delegated = False

    def invoke_application() -> None:
        nonlocal delegated
        delegated = True

    monkeypatch.setattr(entrypoint, "_invoke_application", invoke_application)
    monkeypatch.setattr(sys, "argv", ["forge", "status"])

    entrypoint.main()

    assert delegated


def test_distribution_entry_point_uses_lightweight_dispatcher() -> None:
    project = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )

    assert 'forge = "forge.cli.entrypoint:main"' in project
