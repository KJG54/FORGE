import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AUDIENCE_ROUTES = {
    "user": ROOT / "docs" / "user-guide" / "README.md",
    "pack-author": ROOT / "docs" / "pack-author-guide.md",
    "adapter-author": ROOT / "docs" / "adapter-author-guide.md",
    "architecture": ROOT / "docs" / "architecture.md",
    "security": ROOT / "docs" / "security.md",
    "troubleshooting": ROOT / "docs" / "troubleshooting.md",
    "recovery": ROOT / "docs" / "recovery.md",
}

NAVIGATION_DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "SECURITY.md",
    ROOT / "docs" / "README.md",
    *AUDIENCE_ROUTES.values(),
)

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")


def test_every_required_audience_has_a_documented_route() -> None:
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")

    for audience, path in AUDIENCE_ROUTES.items():
        assert path.is_file(), audience
        content = path.read_text(encoding="utf-8")
        assert content.startswith("# ")
        assert len(content.splitlines()) >= 20
        assert path.relative_to(ROOT / "docs").as_posix() in index


def test_navigation_documents_have_no_broken_local_links() -> None:
    for document in NAVIGATION_DOCUMENTS:
        content = document.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(content):
            target = raw_target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (document.parent / target).resolve()
            assert resolved.exists(), f"{document.relative_to(ROOT)} -> {raw_target}"


def test_guides_preserve_core_authority_and_security_boundaries() -> None:
    user_guide = " ".join(
        AUDIENCE_ROUTES["user"].read_text(encoding="utf-8").lower().split()
    )
    pack_guide = " ".join(
        AUDIENCE_ROUTES["pack-author"].read_text(encoding="utf-8").lower().split()
    )
    adapter_guide = " ".join(
        AUDIENCE_ROUTES["adapter-author"].read_text(encoding="utf-8").lower().split()
    )
    security_guide = " ".join(
        AUDIENCE_ROUTES["security"].read_text(encoding="utf-8").lower().split()
    )

    for term in ("claim", "check", "evidence", "verification", "owner acceptance"):
        assert term in user_guide
    assert "cannot contain executable code" in pack_guide
    assert "no dynamic third-party adapter discovery" in adapter_guide
    assert "not a hostile-code sandbox" in security_guide
    assert "does not prove content secret-free" in security_guide


def test_troubleshooting_maps_every_stable_exit_code() -> None:
    troubleshooting = AUDIENCE_ROUTES["troubleshooting"].read_text(encoding="utf-8")
    for code in (2, 10, 20, 21, 30, 31, 40, 50, 70):
        assert f"| {code} |" in troubleshooting
    for command in (
        "forge recover",
        "forge recover-command",
        "forge remediate-lock",
        "forge migrate",
    ):
        assert f"`{command}`" in troubleshooting
