import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
CONFIG_PATH = ROOT / ".gitleaks.toml"
UUID_PATTERN = (
    "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    "[0-9a-f]{4}-[0-9a-f]{12}$"
)
MILESTONE_KEY_PATTERN = (
    r"^(?:m[0-9]+-increment-[0-9]+|local-v1-l[0-9]+)"
    r"(?:-[a-z0-9]+)+(?:-[0-9]{8})?$"
)
GOVERNED_PATHS = {
    r"(?:^|/)\.forge/active/events\.jsonl$",
    (
        r"(?:^|/)\.forge/archive/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
        r"[0-9a-f]{4}-[0-9a-f]{12}/events\.jsonl$"
    ),
    r"(?:^|/)\.forge/idempotency/[0-9a-f]{64}\.json$",
}


def test_gitleaks_exception_is_rule_idempotency_value_and_path_scoped() -> None:
    document = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert document["extend"] == {"useDefault": True}
    assert len(document["rules"]) == 1
    rule = document["rules"][0]
    assert set(rule) == {"id", "allowlists"}
    assert rule["id"] == "generic-api-key"
    assert len(rule["allowlists"]) == 1

    allowlist = rule["allowlists"][0]
    assert allowlist["condition"] == "AND"
    assert allowlist["regexTarget"] == "secret"
    assert allowlist["regexes"] == [UUID_PATTERN, MILESTONE_KEY_PATTERN]
    assert set(allowlist["paths"]) == GOVERNED_PATHS
