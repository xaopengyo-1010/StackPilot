from stackpilot.models import SystemProfile
from stackpilot.scanner import scan_system


def test_scanner_returns_system_profile():
    profile = scan_system()
    assert isinstance(profile, SystemProfile)
    assert profile.os_name
    assert profile.architecture
    assert profile.platform_profile is not None
    assert profile.python_installed is True


def test_missing_optional_tools_do_not_crash(monkeypatch):
    from stackpilot import detector

    monkeypatch.setattr(detector, "detect_windows_gpu_controllers", lambda: [])
    monkeypatch.setattr(detector, "detect_gpu_names", lambda: [])
    monkeypatch.setattr(detector, "detect_gpu_vram_gb", lambda: None)
    monkeypatch.setattr(detector, "detect_nvidia_driver", lambda: None)
    monkeypatch.setattr(detector, "detect_wsl", lambda: False)
    monkeypatch.setattr(detector, "get_command_version", lambda command, args: None)

    profile = scan_system()

    assert isinstance(profile, SystemProfile)
    assert profile.node_installed is False
    assert profile.git_installed is False
    assert profile.pnpm_installed is False
    assert profile.docker_installed is False


def test_scanner_uses_windows_gpu_parser_and_primary_selector(monkeypatch):
    from stackpilot import detector

    monkeypatch.setattr(
        detector,
        "detect_windows_gpu_controllers",
        lambda: [
            {
                "Name": "AMD Radeon 780M Graphics",
                "AdapterRAM": 4294967296,
            },
            {
                "Name": "NVIDIA GeForce RTX 4060 Laptop GPU",
                "AdapterRAM": 8589934592,
                "DriverVersion": "555.85",
            },
        ],
    )
    monkeypatch.setattr(detector, "detect_nvidia_driver", lambda: "555.85")
    monkeypatch.setattr(detector, "detect_wsl", lambda: False)
    monkeypatch.setattr(detector, "get_command_version", lambda command, args: None)

    profile = scan_system()

    assert len(profile.gpus) == 2
    assert profile.gpu_names == ["AMD Radeon 780M Graphics", "NVIDIA GeForce RTX 4060 Laptop GPU"]
    assert profile.primary_gpu is not None
    assert profile.primary_gpu.name == "NVIDIA GeForce RTX 4060 Laptop GPU"
    assert profile.primary_gpu.gpu_type == "dedicated"
    assert profile.vram_gb == 8
    assert "独立显卡" in profile.gpu_selection_reason
