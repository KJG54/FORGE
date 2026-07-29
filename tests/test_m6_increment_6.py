import json
from pathlib import Path

import pytest

from forge.storage.journal import read_journal
from tools.performance_review import (
    CASE_IDS,
    DEFAULT_POLICY,
    INSTALLATION_MATRIX,
    PerformanceReviewError,
    create_repository_fixture,
    create_synthetic_journal,
    load_policy,
    nearest_rank_percentile,
    validate_policy_against_installation_matrix,
)


def test_performance_policy_covers_the_exact_release_matrix_and_cases() -> None:
    policy = load_policy()
    matrix = json.loads(INSTALLATION_MATRIX.read_text(encoding="utf-8"))

    validate_policy_against_installation_matrix(policy)
    assert policy.python_implementation == matrix["python_implementation"]
    assert list(policy.python_versions) == matrix["python_versions"]
    assert list(policy.operating_systems) == [
        item["id"] for item in matrix["operating_systems"]
    ]
    assert set(policy.cases) == CASE_IDS
    assert policy.measurement.samples >= 20
    assert policy.measurement.percentile == 95
    assert all(
        set(case.budgets_ms) == set(policy.operating_systems)
        for case in policy.cases.values()
    )


def test_performance_policy_rejects_unknown_executable_fields(tmp_path: Path) -> None:
    document = json.loads(DEFAULT_POLICY.read_text(encoding="utf-8"))
    document["cases"]["startup"]["command"] = "forge --version"
    invalid = tmp_path / "performance.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(PerformanceReviewError, match=r"unknown=.*command"):
        load_policy(invalid)


def test_nearest_rank_percentile_is_deterministic() -> None:
    values = tuple(float(item) for item in range(1, 21))

    assert nearest_rank_percentile(values, 50) == 10.0
    assert nearest_rank_percentile(values, 95) == 19.0
    assert nearest_rank_percentile(tuple(reversed(values)), 95) == 19.0
    with pytest.raises(PerformanceReviewError, match="no values"):
        nearest_rank_percentile((), 95)


def test_synthetic_journal_has_exact_valid_hash_chained_workload(tmp_path: Path) -> None:
    journal = tmp_path / "events.jsonl"
    create_synthetic_journal(journal, 1000)

    events = read_journal(journal)
    assert len(events) == 1000
    assert events[0].previous_event_hash is None
    assert all(event.event_hash is not None for event in events)
    assert events[-1].previous_event_hash == events[-2].event_hash


def test_repository_fixture_uses_real_archives_and_open_decisions(tmp_path: Path) -> None:
    fixture = create_repository_fixture(
        tmp_path,
        archive_count=2,
        decision_count=3,
        journal_event_count=10,
    )

    assert len(fixture.archive_ids) == 2
    assert len(tuple(fixture.layout.archive_directory.iterdir())) == 2
    assert len(tuple(fixture.layout.decision_directory.glob("*.json"))) == 3
    assert len(read_journal(fixture.layout.event_journal_file)) == 4
    assert len(read_journal(fixture.journal_path)) == 10


def test_performance_harness_never_uses_shell_command_strings() -> None:
    source = (Path(__file__).parents[1] / "tools" / "performance_review.py").read_text(
        encoding="utf-8"
    )

    assert "shell=False" in source
    assert "shell=True" not in source
