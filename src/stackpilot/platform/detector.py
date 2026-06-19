from __future__ import annotations

import platform as py_platform
import shutil

from stackpilot.models import OsFamily, PlatformProfile


def detect_platform_profile() -> PlatformProfile:
    """Detect platform facts without making installer decisions final."""

    system = py_platform.system()
    notes: list[str] = []
    if system == "Windows":
        os_family: OsFamily = "windows"
        candidates = ["winget", "choco", "scoop"]
        notes.append("Windows-first support.")
    elif system == "Darwin":
        os_family = "macos"
        candidates = ["brew"]
        notes.append("macOS support is experimental.")
    elif system == "Linux":
        os_family = "linux"
        candidates = ["apt", "dnf", "pacman"]
        notes.append("Linux support is experimental.")
    else:
        os_family = "unknown"
        candidates = []
        notes.append("Unknown platform; installer backend must remain manual or unknown.")

    machine = (py_platform.machine() or "").casefold()
    architecture = "x86_64" if machine in {"amd64", "x86_64", "x64"} else "arm64" if machine in {"arm64", "aarch64"} else "unknown"
    package_managers = [command for command in candidates if shutil.which(command)]
    if os_family == "windows" and "winget" in package_managers:
        backend = "winget"
    elif os_family == "macos" and "brew" in package_managers:
        backend = "brew"
    elif os_family == "linux" and "apt" in package_managers:
        backend = "apt"
    elif os_family in {"windows", "macos", "linux"}:
        backend = "manual"
    else:
        backend = "unknown"

    return PlatformProfile(
        os_family=os_family,
        os_name=system or "未知",
        os_version=py_platform.version() or py_platform.release() or "未知",
        architecture=architecture,  # type: ignore[arg-type]
        package_managers=package_managers,
        default_installer_backend=backend,  # type: ignore[arg-type]
        notes=notes,
    )
