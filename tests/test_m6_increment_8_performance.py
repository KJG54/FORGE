import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
POLICY_PATH = ROOT / "release" / "performance-budgets.json"


def test_macos_budgets_cover_the_slowest_supported_python_cell() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    assert policy["cases"]["startup"]["budget_ms"] == {
        "linux": 500,
        "macos": 600,
        "windows": 750,
    }
    assert policy["cases"]["status"]["budget_ms"] == {
        "linux": 1000,
        "macos": 2500,
        "windows": 1500,
    }
    assert policy["cases"]["context_generation"]["budget_ms"] == {
        "linux": 1000,
        "macos": 2000,
        "windows": 1500,
    }
    assert policy["cases"]["archive_access"]["budget_ms"] == {
        "linux": 1000,
        "macos": 2000,
        "windows": 1500,
    }
    assert policy["measurement"] == {
        "clock": "perf_counter_ns",
        "warmups": 3,
        "samples": 20,
        "percentile": 95,
        "timeout_seconds": 15,
    }
