from __future__ import annotations

import platform
from pathlib import Path

import psutil

from . import detector
from .models import HardwareProfile
from .utils import bytes_to_gb


def _safe_call(label: str, warnings: list[str], func, default=None):
    try:
        return func()
    except Exception as exc:  # pragma: no cover - defensive boundary for OS probes.
        warnings.append(f"{label}检测失败：{exc}")
        return default


def _cpu_name() -> str | None:
    cpu = platform.processor() or None
    if cpu:
        return cpu
    if platform.system() == "Windows":
        output = detector.safe_run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name",
            ]
        )
        if output:
            return output.splitlines()[0].strip()
    return None


def _disk_usage():
    anchor = Path.cwd().anchor or "/"
    return psutil.disk_usage(anchor)


def scan_system() -> HardwareProfile:
    warnings: list[str] = []

    ram = _safe_call("内存", warnings, lambda: psutil.virtual_memory(), None)
    disk = _safe_call("磁盘", warnings, _disk_usage, None)
    gpu_names = _safe_call("显卡", warnings, detector.detect_gpu_names, [])
    gpu_vram_gb = _safe_call("显存", warnings, detector.detect_gpu_vram_gb, None)
    nvidia_driver = _safe_call("NVIDIA 驱动", warnings, detector.detect_nvidia_driver, None)

    if not gpu_names:
        warnings.append("未检测到显卡名称。")
    if gpu_names and gpu_vram_gb is None:
        warnings.append("未检测到显存信息。")
    if any("nvidia" in name.casefold() for name in gpu_names) and nvidia_driver is None:
        warnings.append("未检测到 NVIDIA 驱动版本。")

    node_version = detector.get_command_version("node", ["--version"])
    git_version = detector.get_command_version("git", ["--version"])
    pnpm_version = detector.get_command_version("pnpm", ["--version"])
    docker_version = detector.get_command_version("docker", ["--version"])

    return HardwareProfile(
        os_name=platform.system() or "未知",
        os_version=platform.version() or platform.release() or "未知",
        architecture=platform.machine() or "未知",
        cpu_name=_safe_call("CPU", warnings, _cpu_name, None),
        cpu_cores=_safe_call("CPU 核心数", warnings, lambda: psutil.cpu_count(logical=True), None),
        total_ram_gb=bytes_to_gb(ram.total) if ram else None,
        gpu_names=gpu_names,
        gpu_vram_gb=gpu_vram_gb,
        disk_total_gb=bytes_to_gb(disk.total) if disk else None,
        disk_free_gb=bytes_to_gb(disk.free) if disk else None,
        python_installed=True,
        python_version=platform.python_version(),
        node_installed=node_version is not None,
        node_version=node_version,
        git_installed=git_version is not None,
        git_version=git_version,
        pnpm_installed=pnpm_version is not None,
        pnpm_version=pnpm_version,
        docker_installed=docker_version is not None,
        docker_version=docker_version,
        wsl_available=_safe_call("WSL", warnings, detector.detect_wsl, False),
        nvidia_driver_version=nvidia_driver,
        warnings=warnings,
    )
