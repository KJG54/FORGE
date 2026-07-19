import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from forge.contracts import (
    CONTRACT_MODELS,
    Actor,
    ActorType,
    AuditEvent,
    MaterializedState,
    OwnerIdentity,
    RepositoryState,
    RunRecord,
)
from forge.contracts.base import SCHEMA_VERSION, utc_now
from forge.errors import ConflictError
from forge.schemas.export import export_schema_bundle, schema_bundle


def test_every_public_contract_exports_a_strict_versioned_schema() -> None:
    assert len(CONTRACT_MODELS) >= 30
    for name, model in CONTRACT_MODELS.items():
        schema = model.model_json_schema()
        assert schema["type"] == "object", name
        assert schema["properties"]["schema_version"]["default"] == SCHEMA_VERSION, name
        assert schema["additionalProperties"] is False, name


def test_contracts_reject_unknown_fields_and_future_schema_versions() -> None:
    values = {
        "id": uuid4(),
        "display_name": "Repository Owner",
        "created_at": utc_now(),
    }
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        OwnerIdentity.model_validate({**values, "unexpected": True})
    with pytest.raises(ValidationError, match=r"Input should be '1\.0'"):
        OwnerIdentity.model_validate({**values, "schema_version": "2.0"})


def test_increment6_run_records_default_to_no_capability_approval_binding() -> None:
    assert RunRecord.model_fields["capability_approval_ids"].default == ()


def test_contracts_require_aware_timestamps() -> None:
    with pytest.raises(ValidationError, match="timezone info"):
        OwnerIdentity(id=uuid4(), display_name="Owner", created_at=datetime(2026, 1, 1))


def test_contracts_normalize_aware_timestamps_to_utc() -> None:
    owner = OwnerIdentity(
        id=uuid4(),
        display_name="Owner",
        created_at=datetime(2026, 1, 1, 7, tzinfo=timezone(timedelta(hours=2))),
    )
    assert owner.created_at == datetime(2026, 1, 1, 5, tzinfo=UTC)
    assert owner.model_dump(mode="json")["created_at"].endswith("Z")


def test_materialized_state_requires_positive_artifact_revisions() -> None:
    with pytest.raises(ValidationError, match="revision numbers must be positive"):
        MaterializedState(
            repository_state=RepositoryState.INITIALIZED,
            current_artifact_revisions={uuid4(): 0},
        )


def test_audit_event_json_round_trip_preserves_independent_state_metadata() -> None:
    actor = Actor(
        id=uuid4(),
        actor_type=ActorType.FORGE_CLI,
        display_label="FORGE CLI",
        tool_reference="forge 0.1.0a0",
    )
    event = AuditEvent(
        id=uuid4(),
        initiative_id=uuid4(),
        sequence=1,
        timestamp=utc_now(),
        event_type="initiative-created",
        actor=actor,
        authorization_basis="owner invoked supported CLI command",
    )
    restored = AuditEvent.model_validate_json(event.model_dump_json())
    assert restored == event


def test_schema_bundle_is_deterministic_and_self_describing(tmp_path: Path) -> None:
    first = schema_bundle()
    second = schema_bundle()
    assert first == second

    exported = export_schema_bundle(tmp_path / "schemas")
    assert len(exported) == len(CONTRACT_MODELS) + 1
    index = json.loads((tmp_path / "schemas" / "index.json").read_text(encoding="utf-8"))
    assert index["schema_version"] == SCHEMA_VERSION
    assert set(index["schemas"]) == set(CONTRACT_MODELS)


def test_schema_export_refuses_changed_generated_files_without_force(tmp_path: Path) -> None:
    destination = tmp_path / "schemas"
    export_schema_bundle(destination)
    target = destination / "owner-identity.schema.json"
    target.write_text("changed\n", encoding="utf-8")

    with pytest.raises(ConflictError, match="Refusing to overwrite"):
        export_schema_bundle(destination)
    export_schema_bundle(destination, overwrite=True)
    assert target.read_bytes() == schema_bundle()[target.name]
