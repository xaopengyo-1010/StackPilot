from stackpilot.hardware.vram import adapter_ram_to_gb
from stackpilot.hardware.windows_gpu import parse_windows_gpu_controllers


def bytes_for_gb(value: int) -> int:
    return value * 1024**3


def test_parse_windows_multi_gpu_controllers_preserves_all_devices():
    gpus = parse_windows_gpu_controllers(
        [
            {
                "Name": "AMD Radeon 780M Graphics",
                "AdapterRAM": bytes_for_gb(4),
                "DriverVersion": "31.0.1",
                "PNPDeviceID": "PCI\\VEN_1002&DEV_15BF",
            },
            {
                "Name": "NVIDIA GeForce RTX 4060 Laptop GPU",
                "AdapterRAM": bytes_for_gb(8),
                "DriverVersion": "555.85",
                "PNPDeviceID": "PCI\\VEN_10DE&DEV_28A0",
            },
        ]
    )

    assert [gpu.name for gpu in gpus] == [
        "AMD Radeon 780M Graphics",
        "NVIDIA GeForce RTX 4060 Laptop GPU",
    ]
    assert gpus[0].gpu_type == "integrated"
    assert gpus[0].vram_confidence == "shared"
    assert gpus[0].dedicated_vram_gb is None
    assert gpus[0].shared_memory_gb == 4
    assert gpus[1].gpu_type == "dedicated"
    assert gpus[1].dedicated_vram_gb == 8
    assert gpus[1].vram_confidence == "detected"
    assert gpus[1].driver_version == "555.85"


def test_parse_windows_adapter_ram_null_zero_and_invalid_do_not_crash():
    gpus = parse_windows_gpu_controllers(
        [
            {"Name": "NVIDIA GeForce RTX 4050 Laptop GPU", "AdapterRAM": None},
            {"Name": "NVIDIA GeForce GTX 1650", "AdapterRAM": 0},
            {"Name": "Example Future Graphics Device", "AdapterRAM": "not-a-number"},
        ]
    )

    assert len(gpus) == 3
    assert gpus[0].vram_confidence == "estimated"
    assert gpus[0].dedicated_vram_gb == 6
    assert gpus[1].vram_confidence == "estimated"
    assert gpus[2].gpu_type == "unknown"
    assert gpus[2].vram_confidence == "unknown"


def test_parse_windows_microsoft_basic_display_is_virtual():
    gpus = parse_windows_gpu_controllers(
        [
            {
                "Name": "Microsoft Basic Display Adapter",
                "AdapterRAM": bytes_for_gb(8),
            }
        ]
    )

    assert len(gpus) == 1
    assert gpus[0].vendor == "Microsoft"
    assert gpus[0].gpu_type == "virtual"
    assert gpus[0].is_virtual is True
    assert gpus[0].vram_confidence == "unknown"
    assert gpus[0].dedicated_vram_gb is None


def test_adapter_ram_to_gb_rejects_unreasonable_values():
    assert adapter_ram_to_gb(None) is None
    assert adapter_ram_to_gb(0) is None
    assert adapter_ram_to_gb("not-a-number") is None
    assert adapter_ram_to_gb(1024**3) == 1
    assert adapter_ram_to_gb(1024**3 * 256) is None
