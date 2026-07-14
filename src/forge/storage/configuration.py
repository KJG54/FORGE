"""Bounded YAML loading and deterministic writing for ``forge.yaml``."""

import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast

import yaml
from pydantic import ValidationError
from yaml.tokens import AliasToken, AnchorToken

from forge.contracts.configuration import ProjectConfiguration
from forge.errors import ConfigurationError, ConflictError

MAX_CONFIGURATION_BYTES = 1_048_576
_CREDENTIAL_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)


def _contains_recognizable_credential(value: object) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in _CREDENTIAL_PATTERNS)
    if isinstance(value, dict):
        values = cast("dict[object, object]", value).values()
        return any(_contains_recognizable_credential(item) for item in values)
    if isinstance(value, list):
        items = cast("list[object]", value)
        return any(_contains_recognizable_credential(item) for item in items)
    return False


def render_configuration(configuration: ProjectConfiguration) -> bytes:
    """Serialize configuration in a stable, human-readable field order."""
    data = configuration.model_dump(mode="json")
    rendered = yaml.safe_dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return rendered.encode("utf-8")


def load_configuration(path: Path) -> ProjectConfiguration:
    """Read and strictly validate a bounded project configuration."""
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ConfigurationError(f"Cannot read FORGE configuration: {path}") from error
    if len(raw) > MAX_CONFIGURATION_BYTES:
        raise ConfigurationError(
            f"FORGE configuration exceeds the {MAX_CONFIGURATION_BYTES}-byte limit: {path}"
        )
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ConfigurationError(f"FORGE configuration must be UTF-8: {path}") from error
    try:
        scan_yaml = cast(
            "Callable[[str], Iterable[object]]",
            yaml.scan,  # pyright: ignore[reportUnknownMemberType]
        )
        if any(isinstance(token, (AliasToken, AnchorToken)) for token in scan_yaml(text)):
            raise ConfigurationError("FORGE configuration must not contain YAML anchors or aliases")
        data = cast(object, yaml.safe_load(text))
    except ConfigurationError:
        raise
    except yaml.YAMLError as error:
        raise ConfigurationError(f"FORGE configuration is not valid safe YAML: {path}") from error
    if not isinstance(data, dict):
        raise ConfigurationError("FORGE configuration must contain a YAML mapping at its root")
    if _contains_recognizable_credential(cast("dict[object, object]", data)):
        raise ConfigurationError(
            "FORGE configuration appears to contain a credential; keep secrets outside forge.yaml"
        )
    try:
        return ProjectConfiguration.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        raise ConfigurationError(f"Invalid FORGE configuration: {details}") from error


def create_configuration(path: Path, configuration: ProjectConfiguration) -> None:
    """Create configuration exclusively; never overwrite existing content."""
    if _contains_recognizable_credential(configuration.model_dump(mode="json")):
        raise ConfigurationError(
            "Refusing to write a recognizable credential to tracked forge.yaml"
        )
    try:
        with path.open("xb") as stream:
            stream.write(render_configuration(configuration))
    except FileExistsError as error:
        raise ConflictError(f"Refusing to overwrite existing configuration: {path}") from error
    except OSError as error:
        raise ConfigurationError(f"Cannot create FORGE configuration: {path}") from error
