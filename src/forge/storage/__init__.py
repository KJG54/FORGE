"""Repository discovery and initialization for M1 Increment 1.

Journal, replay, snapshots, and atomic mutation primitives are intentionally absent
until Increment 2 is authorized.
"""

from forge.storage.repository import (
    InitializationResult,
    RepositoryLayout,
    discover_repository,
    initialize_repository,
)

__all__ = [
    "InitializationResult",
    "RepositoryLayout",
    "discover_repository",
    "initialize_repository",
]
