import json
from pathlib import Path

from stackpilot.hardware.gpu_selector import select_primary_gpu
from stackpilot.hardware.windows_gpu import parse_windows_gpu_controllers
from stackpilot.models import GpuDevice


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "hardware"
REQUIRED_ENV_TOOLS = {"python", "git", "docker", "wsl"}


def load_feedback_fixtures() -> list[tuple[Path, dict]]:
    fixtures = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        if "machine_profile" in fixture and "environment_tools" in fixture:
            fixtures.append((path, fixture))
    return fixtures


def parsed_fixture_cases() -> list[tuple[Path, dict, list[GpuDevice], GpuDevice | None, str]]:
    cases = []
    for path, fixture in load_feedback_fixtures():
        gpus = parse_windows_gpu_controllers(fixture["raw_windows_video_controllers"])
        selected, reason = select_primary_gpu(gpus)
        cases.append((path, fixture, gpus, selected, reason))
    return cases


def test_v05_feedback_fixtures_have_machine_and_environment_context():
    fixtures = load_feedback_fixtures()

    assert len(fixtures) >= 5
    for path, fixture in fixtures:
        machine = fixture["machine_profile"]
        tools = fixture["environment_tools"]

        assert machine["os"], path.name
        assert machine["cpu"], path.name
        assert machine["ram_gb"] > 0, path.name
        assert machine["disk"]["total_gb"] >= machine["disk"]["free_gb"] >= 0, path.name
        assert REQUIRED_ENV_TOOLS.issubset(tools), path.name
        for tool_name in REQUIRED_ENV_TOOLS:
            assert "installed" in tools[tool_name], f"{path.name}:{tool_name}"
            assert "version" in tools[tool_name], f"{path.name}:{tool_name}"
        assert fixture["gpu_type_hints"], path.name


def test_v05_feedback_fixtures_match_expected_gpu_detection():
    for path, fixture, gpus, selected, reason in parsed_fixture_cases():
        assert reason, path.name
        assert len(gpus) == len(fixture["expected_gpus"]), path.name
        for actual, expected in zip(gpus, fixture["expected_gpus"], strict=True):
            assert actual.name == expected["name"], path.name
            assert actual.vendor == expected["vendor"], path.name
            assert actual.gpu_type == expected["gpu_type"], path.name
            assert actual.vram_confidence == expected["vram_confidence"], path.name
            assert actual.dedicated_vram_gb == expected["dedicated_vram_gb"], path.name
            assert actual.shared_memory_gb == expected["shared_memory_gb"], path.name

        expected_primary = fixture["expected_primary_gpu"]
        if expected_primary is None:
            assert selected is None, path.name
        else:
            assert selected is not None, path.name
            assert selected.name == expected_primary["name"], path.name
            assert selected.gpu_type == expected_primary["gpu_type"], path.name
        assert fixture["expected_gpu_selection_reason_contains"] in reason, path.name


def test_v05_gpu_fixture_scenario_coverage():
    cases = parsed_fixture_cases()
    all_gpus = [gpu for _, _, gpus, _, _ in cases for gpu in gpus]

    assert any(gpu.name == "AMD Radeon 780M Graphics" and gpu.gpu_type == "integrated" for gpu in all_gpus)
    assert any(gpu.name.startswith("NVIDIA GeForce RTX") and gpu.gpu_type == "dedicated" for gpu in all_gpus)
    assert any(gpu.vendor == "Intel" and gpu.gpu_type == "integrated" for gpu in all_gpus)
    assert any(selected is None and "虚拟" in reason for _, _, _, selected, reason in cases)
    assert any(
        selected is not None
        and selected.gpu_type == "dedicated"
        and any(gpu.gpu_type == "integrated" for gpu in gpus)
        for _, _, gpus, selected, _ in cases
    )


def test_v05_vram_confidence_does_not_promote_shared_or_unknown_to_dedicated():
    for path, _, gpus, _, _ in parsed_fixture_cases():
        for gpu in gpus:
            if gpu.vram_confidence in {"shared", "unknown"}:
                assert gpu.dedicated_vram_gb is None, path.name
            if gpu.gpu_type in {"integrated", "virtual"}:
                assert gpu.vram_confidence in {"shared", "unknown"}, path.name
