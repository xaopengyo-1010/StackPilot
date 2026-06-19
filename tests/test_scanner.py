from stackpilot.models import SystemProfile
from stackpilot.detector import StackPilotDetector
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


def test_detector_failure_records_failed_check_without_crashing(monkeypatch):
    from stackpilot import detector

    def raise_permission_error():
        raise PermissionError("GPU access denied")

    monkeypatch.setattr(detector, "detect_windows_gpu_controllers", lambda: [])
    monkeypatch.setattr(detector, "detect_gpu_names", raise_permission_error)
    monkeypatch.setattr(detector, "detect_gpu_vram_gb", lambda: None)
    monkeypatch.setattr(detector, "detect_nvidia_driver", lambda: None)
    monkeypatch.setattr(detector, "detect_wsl", lambda: False)
    monkeypatch.setattr(detector, "get_command_version", lambda command, args: None)

    profile = scan_system()
    payload = StackPilotDetector().scan_system()

    assert isinstance(profile, SystemProfile)
    assert any(
        check.check_name == "gpu_names"
        and check.status == "permission_denied"
        and "GPU access denied" in check.reason
        for check in profile.failed_checks
    )
    assert isinstance(payload, dict)
    assert any(
        check["check_name"] == "gpu_names"
        and check["status"] == "permission_denied"
        and "GPU access denied" in check["reason"]
        for check in payload["failed_checks"]
    )


def test_core_probe_failures_are_non_fatal_and_structured(monkeypatch):
    from stackpilot import detector
    from stackpilot import scanner as scanner_module

    def raise_runtime_error(name):
        raise RuntimeError(f"{name} blocked")

    monkeypatch.setattr(scanner_module.psutil, "disk_usage", lambda anchor: raise_runtime_error("disk"))
    monkeypatch.setattr(scanner_module.platform, "python_version", lambda: raise_runtime_error("python"))
    monkeypatch.setattr(detector, "detect_windows_gpu_controllers", lambda: [])
    monkeypatch.setattr(detector, "detect_gpu_names", lambda: raise_runtime_error("gpu"))
    monkeypatch.setattr(detector, "detect_gpu_vram_gb", lambda: None)
    monkeypatch.setattr(detector, "detect_nvidia_driver", lambda: None)
    monkeypatch.setattr(detector, "detect_wsl", lambda: raise_runtime_error("wsl"))

    def get_command_version(command, args):
        if command in {"git", "docker"}:
            raise_runtime_error(command)
        return None

    monkeypatch.setattr(detector, "get_command_version", get_command_version)

    profile = scan_system()
    failed_names = {check.check_name for check in profile.failed_checks}

    assert isinstance(profile, SystemProfile)
    assert {"disk", "python", "git", "docker", "wsl", "gpu_names"}.issubset(failed_names)
    assert profile.python_installed is False
    assert profile.git_installed is False
    assert profile.docker_installed is False
    assert profile.wsl_installed is False


def test_missing_command_records_command_not_found(monkeypatch):
    from stackpilot import detector

    monkeypatch.setattr(detector, "detect_windows_gpu_controllers", lambda: [])
    monkeypatch.setattr(detector, "detect_gpu_names", lambda: [])
    monkeypatch.setattr(detector, "detect_gpu_vram_gb", lambda: None)
    monkeypatch.setattr(detector, "detect_nvidia_driver", lambda: None)
    monkeypatch.setattr(detector, "detect_wsl", lambda: False)
    monkeypatch.setattr(detector, "command_exists", lambda command: False if command == "git" else True)
    monkeypatch.setattr(detector, "get_command_version", lambda command, args: None)

    profile = scan_system()

    git_check = next(check for check in profile.failed_checks if check.check_name == "git")
    assert git_check.status == "command_not_found"
    assert "git" in git_check.reason


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
