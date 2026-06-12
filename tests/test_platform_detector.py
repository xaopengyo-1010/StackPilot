from stackpilot.platform import detector


def test_detect_platform_profile_windows_with_winget(monkeypatch):
    monkeypatch.setattr(detector.py_platform, "system", lambda: "Windows")
    monkeypatch.setattr(detector.py_platform, "version", lambda: "10.0.22631")
    monkeypatch.setattr(detector.py_platform, "release", lambda: "11")
    monkeypatch.setattr(detector.py_platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(detector.shutil, "which", lambda command: f"C:\\Windows\\{command}.exe" if command == "winget" else None)

    profile = detector.detect_platform_profile()

    assert profile.os_family == "windows"
    assert profile.architecture == "x86_64"
    assert profile.package_managers == ["winget"]
    assert profile.default_installer_backend == "winget"


def test_detect_platform_profile_macos_is_experimental(monkeypatch):
    monkeypatch.setattr(detector.py_platform, "system", lambda: "Darwin")
    monkeypatch.setattr(detector.py_platform, "version", lambda: "24.0.0")
    monkeypatch.setattr(detector.py_platform, "release", lambda: "15")
    monkeypatch.setattr(detector.py_platform, "machine", lambda: "arm64")
    monkeypatch.setattr(detector.shutil, "which", lambda command: "/opt/homebrew/bin/brew" if command == "brew" else None)

    profile = detector.detect_platform_profile()

    assert profile.os_family == "macos"
    assert profile.architecture == "arm64"
    assert profile.default_installer_backend == "brew"
    assert any("experimental" in note for note in profile.notes)


def test_detect_platform_profile_linux_manual_fallback(monkeypatch):
    monkeypatch.setattr(detector.py_platform, "system", lambda: "Linux")
    monkeypatch.setattr(detector.py_platform, "version", lambda: "#1 SMP")
    monkeypatch.setattr(detector.py_platform, "release", lambda: "6.8")
    monkeypatch.setattr(detector.py_platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(detector.shutil, "which", lambda command: None)

    profile = detector.detect_platform_profile()

    assert profile.os_family == "linux"
    assert profile.package_managers == []
    assert profile.default_installer_backend == "manual"
    assert any("experimental" in note for note in profile.notes)
