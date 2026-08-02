"""Parse stable identifiers from canonical FORGE transaction receipts."""

from __future__ import annotations

import re

_FIELD_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class ReceiptFieldError(RuntimeError):
    """A canonical receipt omitted a required stable field."""


def receipt_value(output: str, field: str) -> str:
    """Return one field from the authoritative Recorded line without echoing output."""

    if not _FIELD_PATTERN.fullmatch(field):
        raise ReceiptFieldError(f"Invalid canonical receipt field {field!r}")
    marker = f"{field}="
    for line in output.splitlines():
        if not line.startswith("Recorded -> "):
            continue
        _prefix, separator, remainder = line.partition(marker)
        if separator:
            value = remainder.split(";", 1)[0].split(")", 1)[0].strip()
            if value:
                return value
    raise ReceiptFieldError(f"Command receipt omitted required field {field!r}")
