import json
from pathlib import Path

from stackpilot.hardware.windows_cim import parse_windows_hardware_snapshot
from stackpilot.hardware.windows_gpu import parse_windows_gpu_controllers


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "windows_cim"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_parse_windows_cim_brand_laptop_snapshot():
    parsed = parse_windows_hardware_snapshot(load_fixture("windows_cim_brand_laptop.json"))

    assert parsed["computer_model"].manufacturer == "Lenovo"
    assert parsed["baseboard"].product == "LNVNB161216"
    assert parsed["bios"].release_date == "2024-05-21"
    assert parsed["cpu"].logical_cores == 16
    assert parsed["memory"].total_gb == 32
    assert len(parsed["memory"].modules) == 2
    assert len(parsed["disks"]) == 1
    assert len(parsed["disk_volumes"]) == 2
    assert parsed["disk_volumes"][0].name == "C:"

    gpus = parse_windows_gpu_controllers(parsed["raw_gpu_controllers"])
    assert gpus[0].name == "AMD Radeon 780M Graphics"
    assert gpus[0].gpu_type == "integrated"


def test_parse_windows_cim_custom_desktop_single_object_sections():
    parsed = parse_windows_hardware_snapshot(load_fixture("windows_cim_custom_desktop.json"))

    assert parsed["computer_model"].total_physical_memory_gb == 64
    assert parsed["baseboard"].manufacturer == "ASUSTeK COMPUTER INC."
    assert parsed["cpu"].name.startswith("AMD Ryzen 7 7800X3D")
    assert parsed["memory"].modules[0].speed_mhz == 6000
    assert len(parsed["disks"]) == 2
    assert len(parsed["disk_volumes"]) == 1

    gpus = parse_windows_gpu_controllers(parsed["raw_gpu_controllers"])
    assert [gpu.vendor for gpu in gpus] == ["NVIDIA", "AMD"]
    assert gpus[0].gpu_type == "dedicated"


def test_parse_windows_cim_missing_fields_does_not_crash():
    parsed = parse_windows_hardware_snapshot(load_fixture("windows_cim_missing_fields.json"))

    assert parsed["computer_model"] is None
    assert parsed["baseboard"] is None
    assert parsed["bios"].release_date == "bad-date"
    assert parsed["cpu"] is None
    assert parsed["memory"].total_gb is None
    assert parsed["disks"][0].model == "Unknown Disk"

    gpus = parse_windows_gpu_controllers(parsed["raw_gpu_controllers"])
    assert gpus[0].gpu_type == "virtual"


def test_parse_windows_cim_powershell_json_date():
    parsed = parse_windows_hardware_snapshot({"BIOS": {"ReleaseDate": "/Date(0)/"}})

    assert parsed["bios"].release_date == "1970-01-01"
