"""Explicit, owner-authorized remediation of definitively stale mutation locks."""

from __future__ import annotations

import hashlib
import socket
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from forge.contracts.actors import Actor, ActorType
from forge.contracts.base import utc_now
from forge.contracts.locking import LockRemediationRecord
from forge.core.authorization import require_owner
from forge.errors import ConflictError, IntegrityError, SecurityError
from forge.storage.atomic import sync_directory
from forge.storage.canonical import sha256_digest
from forge.storage.idempotency import request_digest
from forge.storage.locking import (
    LOCK_NAME,
    LockObservation,
    lock_owner_is_definitively_stale,
    observe_lock_path,
    observe_mutation_lock,
    stale_lock_remediation_guard,
)
from forge.storage.records import load_record, write_record
from forge.storage.repository import RepositoryLayout

_COMMAND = "remediate-lock"
_RECORD_NAME = "record.json"
_PRESERVED_NAME = "mutation.lock"


@dataclass(frozen=True)
class LockRemediationResult:
    record: LockRemediationRecord
    preserved_path: Path
    resumed: bool = False
    replayed: bool = False


def _operation_directory(layout: RepositoryLayout, key: str) -> Path:
    name = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return layout.lock_remediation_directory / name


def _ensure_directory(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise SecurityError(f"Lock-remediation directory is unsafe: {path}")
        return
    try:
        path.mkdir()
    except FileExistsError:
        if path.is_symlink() or not path.is_dir():
            raise SecurityError(f"Lock-remediation directory is unsafe: {path}") from None
    except OSError as error:
        raise IntegrityError(f"Cannot create lock-remediation directory {path}: {error}") from error


def _validate_operation_directory(path: Path) -> None:
    allowed = {_RECORD_NAME, _PRESERVED_NAME}
    unexpected = sorted(item.name for item in path.iterdir() if item.name not in allowed)
    if unexpected:
        raise IntegrityError(
            f"Unexpected lock-remediation operation entries at {path}: {unexpected}"
        )


def _created_at(observation: LockObservation) -> datetime:
    try:
        value = datetime.fromisoformat(observation.owner.created_at)
    except ValueError as error:
        raise IntegrityError("Mutation lock creation timestamp is invalid") from error
    if value.tzinfo is None:
        raise IntegrityError("Mutation lock creation timestamp must include a UTC offset")
    return value


def _require_remediable(observation: LockObservation) -> None:
    owner = observation.owner
    if owner.hostname != socket.gethostname():
        raise ConflictError(
            "Mutation lock belongs to another host and cannot be proven stale locally: "
            f"{owner.hostname}"
        )
    if not lock_owner_is_definitively_stale(owner):
        raise ConflictError(
            f"Mutation lock owner is still live on this host: pid={owner.pid} "
            f"command={owner.command!r}"
        )


def _verify_record_request(
    record: LockRemediationRecord,
    *,
    project_id: UUID,
    actor: Actor,
    key: str,
    expected_request_digest: str,
) -> None:
    if record.project_id != project_id or record.actor != actor:
        raise ConflictError("Lock-remediation idempotency key belongs to another authority context")
    if record.idempotency_key != key or record.request_digest != expected_request_digest:
        raise ConflictError(
            "Lock-remediation idempotency key was already used with another request"
        )


def _matches_record(observation: LockObservation, record: LockRemediationRecord) -> bool:
    owner = observation.owner
    return (
        len(observation.content) == record.source_lock_size
        and sha256_digest(observation.content) == record.source_lock_digest
        and owner.pid == record.source_owner_pid
        and owner.hostname == record.source_owner_hostname
        and owner.command == record.source_owner_command
        and _created_at(observation) == record.source_owner_created_at
        and sha256_digest(owner.token.encode("utf-8")) == record.source_owner_token_digest
    )


def _verify_preserved(path: Path, record: LockRemediationRecord) -> None:
    try:
        observation = observe_lock_path(path)
    except IntegrityError as error:
        raise IntegrityError(
            f"Preserved stale-lock evidence is invalid: {path}: {error}"
        ) from error
    if not _matches_record(observation, record):
        raise IntegrityError(
            f"Preserved stale-lock evidence failed size or digest validation: {path}"
        )


def _commit_removal(
    layout: RepositoryLayout,
    preserved_path: Path,
    record: LockRemediationRecord,
) -> None:
    observation = observe_mutation_lock(layout)
    if not _matches_record(observation, record):
        raise ConflictError(
            "Mutation lock changed after remediation authorization; refusing removal"
        )
    _require_remediable(observation)
    if preserved_path.exists() or preserved_path.is_symlink():
        raise ConflictError(
            f"Refusing to overwrite preserved stale-lock evidence: {preserved_path}"
        )
    source = layout.lock_directory / LOCK_NAME
    try:
        source.rename(preserved_path)
        sync_directory(source.parent)
        sync_directory(preserved_path.parent)
    except OSError as error:
        raise IntegrityError(
            f"Cannot atomically preserve and remove stale lock: {error}"
        ) from error
    _verify_preserved(preserved_path, record)


def validate_lock_remediation_store(
    layout: RepositoryLayout,
    *,
    project_id: UUID,
    owner_identity_id: UUID,
) -> int:
    """Validate every local remediation authorization and preserved lock pair."""
    directory = layout.lock_remediation_directory
    if directory.is_symlink() or not directory.is_dir():
        raise SecurityError(f"Lock-remediation directory is unsafe: {directory}")
    count = 0
    for operation in sorted(directory.iterdir(), key=lambda item: item.name):
        if operation.is_symlink() or not operation.is_dir():
            raise IntegrityError(f"Unexpected lock-remediation store entry: {operation}")
        _validate_operation_directory(operation)
        record = load_record(operation / _RECORD_NAME, LockRemediationRecord)
        if operation != _operation_directory(layout, record.idempotency_key):
            raise IntegrityError(
                f"Lock-remediation path does not match its idempotency key: {operation}"
            )
        if record.project_id != project_id:
            raise IntegrityError(f"Lock-remediation project identity mismatch: {operation}")
        if record.actor.id != owner_identity_id or record.actor.actor_type is not ActorType.OWNER:
            raise IntegrityError(f"Lock-remediation actor is not the configured owner: {operation}")
        expected_request = request_digest(_COMMAND, {"reason": record.reason})
        if record.request_digest != expected_request:
            raise IntegrityError(f"Lock-remediation request digest mismatch: {operation}")
        source_path = (layout.lock_directory / LOCK_NAME).relative_to(layout.root).as_posix()
        preserved = operation / _PRESERVED_NAME
        if (
            record.source_lock_path != source_path
            or record.preserved_lock_path != preserved.relative_to(layout.root).as_posix()
        ):
            raise IntegrityError(f"Lock-remediation paths are not canonical: {operation}")
        _verify_preserved(preserved, record)
        count += 1
    return count


def remediate_stale_lock(
    layout: RepositoryLayout,
    *,
    project_id: UUID,
    owner_identity_id: UUID,
    actor: Actor,
    reason: str,
    idempotency_key: str,
) -> LockRemediationResult:
    """Preserve and remove one same-host lock whose owner is definitively dead."""
    if not reason.strip():
        raise ConflictError("Stale-lock remediation requires a non-empty owner reason")
    require_owner(actor, owner_identity_id, "remediate a stale repository lock")
    expected_request_digest = request_digest(_COMMAND, {"reason": reason})

    _ensure_directory(layout.lock_remediation_directory)
    operation_directory = _operation_directory(layout, idempotency_key)
    record_path = operation_directory / _RECORD_NAME
    preserved_path = operation_directory / _PRESERVED_NAME

    with stale_lock_remediation_guard(layout, idempotency_key=idempotency_key):
        observation: LockObservation | None = None
        created_operation = not operation_directory.exists()
        if created_operation:
            observation = observe_mutation_lock(layout)
            _require_remediable(observation)
            _ensure_directory(operation_directory)
        _validate_operation_directory(operation_directory)
        if record_path.exists() or record_path.is_symlink():
            record = load_record(record_path, LockRemediationRecord)
            _verify_record_request(
                record,
                project_id=project_id,
                actor=actor,
                key=idempotency_key,
                expected_request_digest=expected_request_digest,
            )
            if preserved_path.exists() or preserved_path.is_symlink():
                _verify_preserved(preserved_path, record)
                return LockRemediationResult(record, preserved_path, replayed=True)
            observation = observe_mutation_lock(layout)
            if not _matches_record(observation, record):
                raise ConflictError(
                    "Mutation lock does not match the interrupted remediation; refusing removal"
                )
            _commit_removal(layout, preserved_path, record)
            return LockRemediationResult(record, preserved_path, resumed=True)

        if not created_operation:
            # An empty same-key directory is a safe pre-record interruption boundary.
            _validate_operation_directory(operation_directory)
        if observation is None:
            observation = observe_mutation_lock(layout)
            _require_remediable(observation)
        owner = observation.owner
        source_digest = sha256_digest(observation.content)
        record = LockRemediationRecord(
            id=uuid4(),
            project_id=project_id,
            actor=actor,
            reason=reason,
            idempotency_key=idempotency_key,
            request_digest=expected_request_digest,
            authorized_at=utc_now(),
            authorization_basis="configured owner explicitly remediated a definitively stale lock",
            source_lock_path=(layout.lock_directory / LOCK_NAME)
            .relative_to(layout.root)
            .as_posix(),
            source_lock_digest=source_digest,
            source_lock_size=len(observation.content),
            source_owner_pid=owner.pid,
            source_owner_hostname=owner.hostname,
            source_owner_command=owner.command,
            source_owner_created_at=_created_at(observation),
            source_owner_token_digest=sha256_digest(owner.token.encode("utf-8")),
            preserved_lock_path=preserved_path.relative_to(layout.root).as_posix(),
        )
        write_record(record_path, record)
        _commit_removal(layout, preserved_path, record)
        return LockRemediationResult(record, preserved_path)
