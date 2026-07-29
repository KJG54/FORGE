from pathlib import Path

from forge.packs.loader import load_pack
from forge.security.secrets import screen_governed_content
from tools.example_workflow_smoke import SCENARIOS

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = ROOT / "examples"
BUNDLED_PACK_ROOT = ROOT / "src" / "forge" / "packs" / "bundled"


def test_example_scenarios_match_the_bundled_workflows() -> None:
    for scenario in SCENARIOS.values():
        workflow = load_pack(
            BUNDLED_PACK_ROOT / scenario.pack_id,
            bundled=True,
        ).workflow()
        assert tuple(step.step_id for step in scenario.steps) == tuple(
            step.id for step in workflow.steps
        )
        for scenario_step, workflow_step in zip(
            scenario.steps,
            workflow.steps,
            strict=True,
        ):
            assert scenario_step.outputs == workflow_step.required_outputs
            assert scenario_step.checks == workflow_step.check_requirements


def test_examples_contain_every_declared_output_and_documented_check() -> None:
    for scenario in SCENARIOS.values():
        example = EXAMPLES_ROOT / f"{scenario.example_id}-project"
        readme = (example / "README.md").read_text(encoding="utf-8")
        for step in scenario.steps:
            assert f"`{step.step_id}`" in readme
            for role in step.outputs:
                artifact = example / "artifacts" / f"{role}.md"
                assert artifact.is_file()
                assert artifact.read_text(encoding="utf-8").startswith("# ")
                assert f"`{role}`" in readme
            for check_id in step.checks:
                assert f"`{check_id}`" in readme


def test_examples_are_static_synthetic_content_without_managed_state() -> None:
    for example in sorted(EXAMPLES_ROOT.glob("*-project")):
        inventory = tuple(path for path in example.rglob("*") if path.is_file())
        assert inventory
        assert not (example / ".forge").exists()
        assert not (example / "forge.yaml").exists()
        assert all(path.suffix == ".md" for path in inventory)
        for path in inventory:
            relative = path.relative_to(example).as_posix()
            screen_governed_content(
                relative,
                path.read_bytes(),
                secret_path_patterns=(),
            )


def test_example_harness_cannot_target_an_existing_repository() -> None:
    source = (ROOT / "tools" / "example_workflow_smoke.py").read_text(encoding="utf-8")
    assert "TemporaryDirectory" in source
    assert "--directory" not in source
    assert "--work-directory" not in source
    assert "shell=False" in source
