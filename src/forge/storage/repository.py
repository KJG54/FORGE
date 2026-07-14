"""Non-destructive FORGE repository discovery and initialization."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from forge.contracts.actors import OwnerIdentity
from forge.contracts.base import utc_now
from forge.contracts.configuration import ProjectConfiguration
from forge.errors import ConfigurationError, ConflictError, SecurityError
from forge.security.paths import resolve_repository_path
from forge.storage.configuration import create_configuration, load_configuration

CONFIGURATION_FILE = "forge.yaml"
FORGE_DIRECTORY = ".forge"
GITIGNORE_RULE = ".forge/local/"
GITIGNORE_BLOCK = ("# FORGE local state", GITIGNORE_RULE)


@dataclass(frozen=True)
class RepositoryLayout:
    """Resolved locations owned by FORGE inside one project repository."""

    root: Path
    configuration_file: Path
    forge_directory: Path
    active_directory: Path
    archive_directory: Path
    objects_directory: Path
    object_directory: Path
    local_directory: Path
    lock_directory: Path
    import_staging_directory: Path
    run_directory: Path
    cache_directory: Path
    secret_directory: Path

    @classmethod
    def at(cls, root: Path) -> RepositoryLayout:
        resolved = root.resolve(strict=True)
        forge_directory = resolved / FORGE_DIRECTORY
        local_directory = forge_directory / "local"
        return cls(
            root=resolved,
            configuration_file=resolved / CONFIGURATION_FILE,
            forge_directory=forge_directory,
            active_directory=forge_directory / "active",
            archive_directory=forge_directory / "archive",
            objects_directory=forge_directory / "objects",
            object_directory=forge_directory / "objects" / "sha256",
            local_directory=local_directory,
            lock_directory=local_directory / "locks",
            import_staging_directory=local_directory / "import-staging",
            run_directory=local_directory / "runs",
            cache_directory=local_directory / "cache",
            secret_directory=local_directory / "secrets",
        )

    @property
    def required_directories(self) -> tuple[Path, ...]:
        return (
            self.forge_directory,
            self.active_directory,
            self.archive_directory,
            self.objects_directory,
            self.object_directory,
            self.local_directory,
            self.lock_directory,
            self.import_staging_directory,
            self.run_directory,
            self.cache_directory,
            self.secret_directory,
        )

    @property
    def event_journal_file(self) -> Path:
        return self.active_directory / "events.jsonl"

    @property
    def state_file(self) -> Path:
        return self.active_directory / "state.json"

    @property
    def initiative_file(self) -> Path:
        return self.active_directory / "initiative.json"

    @property
    def workflow_lock_file(self) -> Path:
        return self.active_directory / "workflow.lock.json"

    @property
    def pack_lock_file(self) -> Path:
        return self.active_directory / "pack.lock.json"

    @property
    def pack_trust_file(self) -> Path:
        return self.active_directory / "pack-trust.json"

    @property
    def governed_run_directory(self) -> Path:
        return self.active_directory / "runs"

    @property
    def artifact_directory(self) -> Path:
        return self.active_directory / "artifacts"

    @property
    def artifact_record_directory(self) -> Path:
        return self.artifact_directory / "records"

    @property
    def artifact_revision_directory(self) -> Path:
        return self.artifact_directory / "revisions"

    @property
    def claim_directory(self) -> Path:
        return self.active_directory / "claims"

    @property
    def check_directory(self) -> Path:
        return self.active_directory / "checks"

    @property
    def evidence_directory(self) -> Path:
        return self.active_directory / "evidence"

    @property
    def acceptance_directory(self) -> Path:
        return self.active_directory / "acceptance"

    @property
    def revocation_directory(self) -> Path:
        return self.active_directory / "revocations"

    @property
    def decision_directory(self) -> Path:
        return self.active_directory / "decisions"

    @property
    def decision_supersession_directory(self) -> Path:
        return self.active_directory / "decision-supersessions"


@dataclass(frozen=True)
class InitializationResult:
    layout: RepositoryLayout
    configuration: ProjectConfiguration
    created: bool
    gitignore_changed: bool


def _assert_managed_entry_is_not_symlink(path: Path) -> None:
    if path.is_symlink():
        raise SecurityError(f"Refusing to manage a symbolic link: {path}")


def _validate_root(root: Path) -> Path:
    try:
        resolved = root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ConfigurationError(f"Repository directory does not exist: {root}") from error
    if not resolved.is_dir():
        raise ConfigurationError(f"Repository location is not a directory: {resolved}")
    return resolved


def _preflight_managed_paths(layout: RepositoryLayout) -> None:
    for relative in (CONFIGURATION_FILE, FORGE_DIRECTORY, ".gitignore"):
        candidate = layout.root / relative
        _assert_managed_entry_is_not_symlink(candidate)
        if candidate.exists():
            resolve_repository_path(layout.root, relative, must_exist=True)
    if layout.configuration_file.exists() and not layout.configuration_file.is_file():
        raise ConflictError(f"Expected a file at {layout.configuration_file}")
    if layout.forge_directory.exists() and not layout.forge_directory.is_dir():
        raise ConflictError(f"Expected a directory at {layout.forge_directory}")
    for directory in layout.required_directories:
        if not directory.exists():
            continue
        _assert_managed_entry_is_not_symlink(directory)
        relative = directory.relative_to(layout.root).as_posix()
        resolve_repository_path(layout.root, relative, must_exist=True)


def _read_gitignore(path: Path) -> bytes:
    if not path.exists():
        return b""
    if not path.is_file():
        raise ConflictError(f"Expected a file at {path}")
    try:
        content = path.read_bytes()
        content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ConfigurationError(f"Cannot safely merge non-UTF-8 .gitignore: {path}") from error
    except OSError as error:
        raise ConfigurationError(f"Cannot read .gitignore: {path}") from error
    return content


def _has_gitignore_rule(content: bytes) -> bool:
    text = content.decode("utf-8-sig")
    accepted = {".forge/local", ".forge/local/", ".forge/local/**"}
    return any(line.strip().lstrip("/") in accepted for line in text.splitlines())


def _merge_gitignore(path: Path, original: bytes) -> bool:
    if _has_gitignore_rule(original):
        return False
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    prefix = b"" if not original or original.endswith((b"\n", b"\r")) else newline
    block = prefix + newline.join(line.encode() for line in GITIGNORE_BLOCK) + newline
    try:
        if path.exists():
            with path.open("ab") as stream:
                stream.write(block)
        else:
            with path.open("xb") as stream:
                stream.write(block)
    except OSError as error:
        raise ConfigurationError(f"Cannot add the FORGE rule to .gitignore: {path}") from error
    return True


def _create_required_directories(layout: RepositoryLayout) -> tuple[Path, ...]:
    created: list[Path] = []
    try:
        for directory in layout.required_directories:
            if directory.exists() and not directory.is_dir():
                raise ConflictError(f"Expected a directory at {directory}")
            if not directory.exists():
                directory.mkdir()
                created.append(directory)
    except ConflictError:
        _remove_empty_directories(tuple(created))
        raise
    except OSError as error:
        _remove_empty_directories(tuple(created))
        raise ConfigurationError(f"Cannot create FORGE repository directories: {error}") from error
    return tuple(created)


def _remove_empty_directories(directories: tuple[Path, ...]) -> None:
    for directory in reversed(directories):
        with suppress(OSError):
            directory.rmdir()


def _validate_available_packs(
    layout: RepositoryLayout,
    configuration: ProjectConfiguration,
) -> None:
    # Local import avoids a module cycle: pack discovery consumes RepositoryLayout.
    from forge.packs.loader import available_packs

    available_packs(layout, configuration)


def discover_repository(start: Path) -> RepositoryLayout:
    """Find the nearest initialized FORGE repository at or above ``start``."""
    if not start.exists():
        raise ConfigurationError(f"Repository search location does not exist: {start}")
    resolved = _validate_root(start.parent if start.is_file() else start)
    for candidate in (resolved, *resolved.parents):
        configuration_file = candidate / CONFIGURATION_FILE
        if configuration_file.exists():
            layout = RepositoryLayout.at(candidate)
            _preflight_managed_paths(layout)
            load_configuration(layout.configuration_file)
            if not layout.forge_directory.is_dir():
                raise ConfigurationError(
                    f"FORGE configuration exists but {layout.forge_directory} is missing"
                )
            return layout
    raise ConfigurationError(
        f"No initialized FORGE repository found at or above {resolved}; run 'forge init' first"
    )


def initialize_repository(
    root: Path, *, owner_display_name: str | None = None
) -> InitializationResult:
    """Initialize a repository while preserving all unrelated content."""
    resolved = _validate_root(root)
    layout = RepositoryLayout.at(resolved)
    _preflight_managed_paths(layout)
    gitignore_path = layout.root / ".gitignore"
    original_gitignore = _read_gitignore(gitignore_path)

    if layout.configuration_file.exists():
        configuration = load_configuration(layout.configuration_file)
        _validate_available_packs(layout, configuration)
        _create_required_directories(layout)
        changed = _merge_gitignore(gitignore_path, original_gitignore)
        return InitializationResult(layout, configuration, False, changed)

    if layout.forge_directory.exists() and any(layout.forge_directory.iterdir()):
        raise ConflictError(
            f"Refusing to adopt non-empty {layout.forge_directory} without an existing forge.yaml"
        )
    if owner_display_name is None or not owner_display_name.strip():
        raise ConfigurationError("An owner display name is required for first initialization")

    configuration = ProjectConfiguration(
        project_id=uuid4(),
        owner=OwnerIdentity(
            id=uuid4(),
            display_name=owner_display_name,
            created_at=utc_now(),
        ),
    )
    _validate_available_packs(layout, configuration)
    created_directories = _create_required_directories(layout)
    configuration_created = False
    try:
        create_configuration(layout.configuration_file, configuration)
        configuration_created = True
        changed = _merge_gitignore(gitignore_path, original_gitignore)
    except Exception:
        try:
            if configuration_created:
                layout.configuration_file.unlink(missing_ok=True)
        finally:
            _remove_empty_directories(created_directories)
        raise
    return InitializationResult(layout, configuration, True, changed)
