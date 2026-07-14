"""Stable user-facing error categories introduced by M1 Increment 1."""

from enum import IntEnum


class ExitCode(IntEnum):
    USAGE = 2
    CONFIGURATION = 10
    AUTHORIZATION = 20
    TRANSITION = 21
    INTEGRITY = 30
    CONFLICT = 31
    SECURITY = 40
    EXTERNAL_TOOL = 50
    INTERNAL = 70


class ForgeError(Exception):
    """Base for actionable errors safe to show without a traceback."""

    exit_code = ExitCode.INTERNAL


class ConfigurationError(ForgeError):
    exit_code = ExitCode.CONFIGURATION


class ConflictError(ForgeError):
    exit_code = ExitCode.CONFLICT


class SecurityError(ForgeError):
    exit_code = ExitCode.SECURITY


class IntegrityError(ForgeError):
    exit_code = ExitCode.INTEGRITY
