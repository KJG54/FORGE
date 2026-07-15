import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_project_files_exist() -> None:
    required = {
        "README.md",
        "LICENSE",
        "NOTICE",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "CHANGELOG.md",
        "docs/constitution.md",
        "docs/glossary.md",
    }
    missing = sorted(path for path in required if not (ROOT / path).is_file())
    assert not missing, f"Missing foundational files: {missing}"


def test_m2_increment_10_does_not_contain_later_milestone_modules() -> None:
    package = ROOT / "src" / "forge"
    deferred = {"agents", "capabilities"}
    present = sorted(name for name in deferred if (package / name).exists())
    assert not present, f"M2 Increment 10 created deferred implementation modules: {present}"

    core = package / "core"
    forbidden_core = {
        "context.py",
        "evidence.py",
    }
    present_core = sorted(path.name for path in core.glob("*.py") if path.name in forbidden_core)
    assert not present_core, f"Later-increment core exists prematurely: {present_core}"

def test_local_markdown_links_resolve() -> None:
    markdown_files = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
    ]
    pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    broken: list[str] = []
    for document in markdown_files:
        for target in pattern.findall(document.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            path = target.split("#", maxsplit=1)[0]
            if not (document.parent / path).exists():
                broken.append(f"{document.name}: {target}")
    assert not broken, f"Broken local documentation links: {broken}"
