"""Archived-predecessor validation for successor initiative creation."""

from __future__ import annotations

from uuid import UUID

from forge.contracts.artifacts import ArtifactRevision
from forge.contracts.events import AuditEvent
from forge.contracts.initiatives import Initiative, InitiativeReference
from forge.errors import ConfigurationError, ConflictError, IntegrityError
from forge.storage.repository import RepositoryLayout

SUCCESSOR_RELATIONSHIP = "successor-of"


def predecessor_artifact_source_reference(
    predecessor_id: UUID,
    revision_id: UUID,
) -> str:
    return (
        f".forge/archive/{predecessor_id}/artifacts/revisions/{revision_id}.json"
    )


def _reference(initiative_id: UUID) -> InitiativeReference:
    return InitiativeReference(
        initiative_id=initiative_id,
        relationship=SUCCESSOR_RELATIONSHIP,
        archive_reference=f".forge/archive/{initiative_id}",
    )


def build_predecessor_references(
    layout: RepositoryLayout,
    predecessor_ids: tuple[UUID, ...],
) -> tuple[InitiativeReference, ...]:
    """Validate repository archives and build canonical successor links."""
    from forge.core.archival import list_archive_ids, load_archive

    if len(set(predecessor_ids)) != len(predecessor_ids):
        raise ConfigurationError("Successor predecessor IDs must not contain duplicates")
    staging = tuple(
        item.name
        for item in layout.archive_directory.iterdir()
        if item.name.startswith(".") and item.name.endswith(".staging")
    )
    retired = tuple(
        item.name
        for item in layout.local_directory.iterdir()
        if item.name.startswith(("closed-active-", "abandoned-active-"))
    )
    if staging or retired:
        raise ConflictError(
            "A terminal archive transaction is incomplete; finish it before creating a successor"
        )
    archived_ids = list_archive_ids(layout)
    for archived_id in archived_ids:
        load_archive(layout, archived_id)
    if archived_ids and not predecessor_ids:
        raise ConflictError(
            "Successor-initiative creation requires at least one --predecessor archived "
            "initiative"
        )
    unknown = set(predecessor_ids) - set(archived_ids)
    if unknown:
        raise ConflictError(
            f"Successor predecessor IDs are not archived initiatives: {sorted(map(str, unknown))}"
        )
    return tuple(_reference(item) for item in sorted(predecessor_ids, key=str))


def validate_predecessor_references(
    layout: RepositoryLayout,
    initiative: Initiative,
    creation_event: AuditEvent,
) -> None:
    """Validate persisted successor links without inheriting predecessor state."""
    from forge.core.archival import load_archive

    references = initiative.predecessor_references
    identifiers = tuple(item.initiative_id for item in references)
    if len(set(identifiers)) != len(identifiers) or initiative.id in identifiers:
        raise IntegrityError("Initiative predecessor references are duplicate or self-referential")
    expected = [item.model_dump(mode="json") for item in references]
    if creation_event.metadata.get("predecessor_references", []) != expected:
        raise IntegrityError("Initiative predecessor references do not match its creation event")
    for reference in references:
        canonical = _reference(reference.initiative_id)
        if reference != canonical:
            raise IntegrityError("Initiative predecessor reference is not canonical")
        archive = load_archive(layout, reference.initiative_id)
        if archive.active.initiative.id != reference.initiative_id:
            raise IntegrityError("Initiative predecessor reference does not match its archive")
    if references and (
        not set(identifiers).issubset(initiative.affected_record_ids)
        or not set(identifiers).issubset(creation_event.affected_record_ids)
    ):
        raise IntegrityError("Initiative predecessor IDs are not bound to creation provenance")


def load_predecessor_artifact_revision(
    layout: RepositoryLayout,
    initiative: Initiative,
    revision_id: UUID,
) -> tuple[UUID, ArtifactRevision]:
    """Resolve one manifest-bound terminal revision from a declared predecessor."""
    from forge.core.archival import load_archive
    from forge.core.artifacts import load_artifact_revision

    for reference in initiative.predecessor_references:
        archive = load_archive(layout, reference.initiative_id)
        manifest_reference = next(
            (
                item
                for item in archive.manifest.object_references
                if item.artifact_revision_id == revision_id
            ),
            None,
        )
        if manifest_reference is None:
            continue
        revision = load_artifact_revision(archive.layout, revision_id)
        if (
            revision.initiative_id != reference.initiative_id
            or revision.content_digest != manifest_reference.content_digest
            or revision.byte_size != manifest_reference.byte_size
            or revision.preserved_object_path != manifest_reference.preserved_object_path
        ):
            raise IntegrityError(
                "Predecessor artifact revision does not match its archive manifest"
            )
        return reference.initiative_id, revision
    raise ConflictError(
        f"Artifact revision {revision_id} is not a terminal revision of a declared predecessor"
    )
