"""Lightweight console dispatch before the full command application is needed."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from forge import __version__

VERSION_ARGUMENTS = ("--version",)


def _is_exact_version_request(arguments: Sequence[str]) -> bool:
    return tuple(arguments) == VERSION_ARGUMENTS


def _invoke_application() -> None:
    from forge.cli.app import main as application_main

    application_main()


def main() -> None:
    """Handle the exact version query cheaply and delegate every other invocation."""
    if _is_exact_version_request(sys.argv[1:]):
        sys.stdout.write(f"{__version__}\n")
        return
    _invoke_application()
