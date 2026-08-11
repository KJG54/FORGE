import json
from pathlib import Path
from typing import TypedDict, cast

import pytest
from pydantic import ValidationError

from forge.contracts import CONTRACT_MODELS
from forge.contracts.base import SCHEMA_VERSION
from forge.storage.journal import read_journal
from forge.storage.migrations import (
    HASH_CHAIN_JOURNAL_FORMAT,
    LEGACY_JOURNAL_FORMAT,
    plan_event_journal_migration,
    registered_migrations,
    render_migrated_journal,
)

FIXTURES = Path(__file__).parent / "fixtures" / "compatibility"


class AcceptedBaseline(TypedDict):
    added_models: list[str]
    commit: str
    milestone: str
    public_model_count: int


class ContractSchemaVersion(TypedDict):
    fixture: str
    schema_version: str
    status: str


class JournalFormat(TypedDict):
    fixture: str
    format: str
    migration_id: str | None
    mutation_support: str
    schema_version: str


class CompatibilityManifest(TypedDict):
    accepted_baselines: list[AcceptedBaseline]
    contract_schema_versions: list[ContractSchemaVersion]
    journal_formats: list[JournalFormat]
    manifest_version: int
    public_pre_v1_releases: list[str]


class RecordFixture(TypedDict):
    expected_current_defaults: dict[str, object]
    model: str
    payload: dict[str, object]


def _load_manifest() -> CompatibilityManifest:
    return cast(
        "CompatibilityManifest",
        json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8")),
    )


def _load_record_fixtures() -> list[RecordFixture]:
    return cast(
        "list[RecordFixture]",
        json.loads((FIXTURES / "schema-1.0-records.json").read_text(encoding="utf-8")),
    )


def _nested_value(value: object, path: str) -> object:
    current = value
    for part in path.split("."):
        if isinstance(current, dict):
            current = cast("dict[str, object]", current)[part]
        else:
            raise AssertionError(f"{path!r} does not resolve through a JSON object")
    return current


def test_pre_v1_manifest_covers_every_accepted_public_model() -> None:
    manifest = _load_manifest()
    assert manifest["manifest_version"] == 1
    assert manifest["public_pre_v1_releases"] == []

    cumulative: set[str] = set()
    # Baselines are labelled by the body of work that changed the public contract.
    # M6 and M7 are absent because neither added a public model.
    expected_milestones = ["M1", "M2", "M3", "M4", "M5", "profile-aware-facilitation"]
    baselines = manifest["accepted_baselines"]
    assert [item["milestone"] for item in baselines] == expected_milestones
    for baseline in baselines:
        additions = baseline["added_models"]
        assert not cumulative.intersection(additions)
        cumulative.update(additions)
        assert len(cumulative) == baseline["public_model_count"]

    assert cumulative == set(CONTRACT_MODELS)
    assert [item["schema_version"] for item in manifest["contract_schema_versions"]] == [
        SCHEMA_VERSION
    ]


def test_schema_1_0_fixtures_load_with_additive_current_defaults() -> None:
    fixtures = _load_record_fixtures()
    for fixture in fixtures:
        model = CONTRACT_MODELS[fixture["model"]]
        restored = model.model_validate(fixture["payload"])
        rendered = restored.model_dump(mode="json")
        assert rendered["schema_version"] == SCHEMA_VERSION
        for path, expected in fixture["expected_current_defaults"].items():
            assert _nested_value(rendered, path) == expected


def test_schema_1_0_fixtures_reject_unsupported_future_versions() -> None:
    fixtures = _load_record_fixtures()
    for fixture in fixtures:
        model = CONTRACT_MODELS[fixture["model"]]
        future = {**fixture["payload"], "schema_version": "2.0"}
        with pytest.raises(ValidationError, match=r"Input should be '1\.0'"):
            model.model_validate(future)


def test_manifest_covers_the_exact_migration_registry_and_journal_formats() -> None:
    manifest = _load_manifest()
    formats = {item["format"]: item for item in manifest["journal_formats"]}
    assert set(formats) == {LEGACY_JOURNAL_FORMAT, HASH_CHAIN_JOURNAL_FORMAT}
    assert formats[LEGACY_JOURNAL_FORMAT]["mutation_support"] == "migration-required"
    assert formats[HASH_CHAIN_JOURNAL_FORMAT]["mutation_support"] == "current"

    manifest_migrations = {
        item["migration_id"] for item in manifest["journal_formats"] if item["migration_id"]
    }
    registry = registered_migrations()
    assert manifest_migrations == {item.id for item in registry}
    for definition in registry:
        source = formats[definition.source_format]
        target = formats[definition.target_format]
        assert source["schema_version"] == definition.source_schema_version
        assert target["schema_version"] == definition.target_schema_version
        assert (FIXTURES / source["fixture"]).is_file()
        assert (FIXTURES / target["fixture"]).is_file()


def test_frozen_m1_journal_migrates_to_the_exact_frozen_m2_bytes() -> None:
    legacy_path = FIXTURES / "m1-unhashed-events.jsonl"
    current_path = FIXTURES / "m2-hash-chained-events.jsonl"
    legacy_events = read_journal(legacy_path)
    current_events = read_journal(current_path)

    plan = plan_event_journal_migration(legacy_events)
    assert plan.required
    assert plan.current_format == LEGACY_JOURNAL_FORMAT
    assert plan.target_format == HASH_CHAIN_JOURNAL_FORMAT

    unsealed_migration = current_events[-1].model_copy(
        update={"previous_event_hash": None, "event_hash": None}
    )
    rendered, migrated = render_migrated_journal(legacy_events, unsealed_migration)
    assert rendered == current_path.read_bytes()
    assert migrated == current_events

    current_plan = plan_event_journal_migration(current_events)
    assert not current_plan.required
    assert current_plan.current_format == HASH_CHAIN_JOURNAL_FORMAT
    assert current_plan.target_format == HASH_CHAIN_JOURNAL_FORMAT
