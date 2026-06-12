import json
from pathlib import Path

from stackpilot.hardware.gpu_selector import select_primary_gpu
from stackpilot.hardware.windows_gpu import parse_windows_gpu_controllers


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "hardware"
REQUIRED_FIXTURES = {
    "only_intel_uhd.json",
    "only_iris_xe.json",
    "only_radeon_780m.json",
    "intel_uhd_plus_rtx4050.json",
    "radeon_780m_plus_rtx4060.json",
    "rtx3060_12gb.json",
    "rtx4090_24gb.json",
    "rtx5090_32gb.json",
    "microsoft_basic_display_only.json",
    "unknown_gpu_name.json",
    "no_gpu_detected.json",
    "low_disk_space.json",
}


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_required_hardware_fixtures_exist():
    existing = {path.name for path in FIXTURE_DIR.glob("*.json")}

    assert REQUIRED_FIXTURES.issubset(existing)
    assert len(existing) >= 12


def test_hardware_fixtures_validate_parser_and_primary_selection():
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture = load_fixture(path)
        gpus = parse_windows_gpu_controllers(fixture["raw_windows_video_controllers"])
        selected, reason = select_primary_gpu(gpus)

        assert len(gpus) == len(fixture["expected_gpus"]), path.name
        for gpu, expected in zip(gpus, fixture["expected_gpus"], strict=True):
            assert gpu.name == expected["name"], path.name
            assert gpu.vendor == expected["vendor"], path.name
            assert gpu.gpu_type == expected["gpu_type"], path.name
            assert gpu.vram_confidence == expected["vram_confidence"], path.name
            assert gpu.dedicated_vram_gb == expected["dedicated_vram_gb"], path.name
            assert gpu.shared_memory_gb == expected["shared_memory_gb"], path.name

        expected_primary = fixture["expected_primary_gpu"]
        if expected_primary is None:
            assert selected is None, path.name
        else:
            assert selected is not None, path.name
            assert selected.name == expected_primary["name"], path.name
            assert selected.gpu_type == expected_primary["gpu_type"], path.name
        assert fixture["expected_gpu_selection_reason_contains"] in reason, path.name
        assert "expected_findings" in fixture, path.name


def test_fixture_coverage_for_required_gpu_cases():
    fixtures = {path.name: load_fixture(path) for path in FIXTURE_DIR.glob("*.json")}

    assert fixtures["only_intel_uhd.json"]["expected_gpus"][0]["gpu_type"] == "integrated"
    assert fixtures["only_iris_xe.json"]["expected_gpus"][0]["gpu_type"] == "integrated"
    assert fixtures["only_radeon_780m.json"]["expected_gpus"][0]["gpu_type"] == "integrated"
    assert fixtures["intel_uhd_plus_rtx4050.json"]["expected_primary_gpu"]["name"].endswith("RTX 4050 Laptop GPU")
    assert fixtures["radeon_780m_plus_rtx4060.json"]["expected_primary_gpu"]["name"].endswith("RTX 4060 Laptop GPU")
    assert fixtures["rtx3060_12gb.json"]["expected_gpus"][0]["vram_confidence"] == "detected"
    assert fixtures["rtx4090_24gb.json"]["expected_gpus"][0]["dedicated_vram_gb"] == 24.0
    assert fixtures["rtx5090_32gb.json"]["expected_gpus"][0]["vram_confidence"] in {"detected", "estimated"}
    assert fixtures["microsoft_basic_display_only.json"]["expected_gpus"][0]["gpu_type"] == "virtual"
    assert fixtures["unknown_gpu_name.json"]["expected_gpus"][0]["gpu_type"] == "unknown"
    assert fixtures["no_gpu_detected.json"]["expected_primary_gpu"] is None
    assert any(
        expected["vram_confidence"] == "shared"
        for fixture in fixtures.values()
        for expected in fixture["expected_gpus"]
    )
    assert any(
        expected["vram_confidence"] == "unknown"
        for fixture in fixtures.values()
        for expected in fixture["expected_gpus"]
    )
