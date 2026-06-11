from stackpilot.models import SystemProfile
from stackpilot.scanner import scan_system


def test_scanner_returns_system_profile():
    profile = scan_system()
    assert isinstance(profile, SystemProfile)
    assert profile.os_name
    assert profile.architecture
    assert profile.python_installed is True


def test_missing_optional_tools_do_not_crash(monkeypatch):
    from stackpilot import detector

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
