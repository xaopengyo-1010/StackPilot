from __future__ import annotations

import platform as py_platform
import shutil

from stackpilot.models import Architecture, InstallerBackend, OsFamily, PlatformProfile


def _architecture() -> Architecture:
    machine = (py_platform.machine() or "").casefold()
    if machine in {"amd64", "x86_64", "x64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return "unknown"


def _command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _package_managers(candidates: list[str]) -> list[str]:
    return [command for command in candidates if _command_exists(command)]


def _default_backend(os_family: OsFamily, package_managers: list[str]) -> InstallerBackend:
    if os_family == "windows" and "winget" in package_managers:
        return "winget"
    if os_family == "macos" and "brew" in package_managers:
        return "brew"
    if os_family == "linux" and "apt" in package_managers:
        return "apt"
    if os_family in {"windows", "macos", "linux"}:
        return "manual"
    return "unknown"


def detect_platform_profile() -> PlatformProfile:
    """Detect platform facts without making installer decisions final."""

    system = py_platform.system()
    os_family: OsFamily
    candidates: list[str]
    notes: list[str] = []
    if system == "Windows":
        os_family = "windows"
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

    package_managers = _package_managers(candidates)
    return PlatformProfile(
        os_family=os_family,
        os_name=system or "未知",
        os_version=py_platform.version() or py_platform.release() or "未知",
        architecture=_architecture(),
        package_managers=package_managers,
        default_installer_backend=_default_backend(os_family, package_managers),
        notes=notes,
    )
