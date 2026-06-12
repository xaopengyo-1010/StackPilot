from __future__ import annotations

import platform
from pathlib import Path

import psutil

from . import detector
from .hardware.gpu_classifier import classify_gpu_type, classify_gpu_vendor, classify_vram_confidence
from .hardware.gpu_selector import select_primary_gpu
from .hardware.vram import estimate_dedicated_vram_from_name
from .hardware.windows_gpu import parse_windows_gpu_controllers
from .models import GpuDevice, HardwareProfile
from .platform.detector import detect_platform_profile
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


def _legacy_gpu_devices(gpu_names: list[str], gpu_vram_gb: float | None) -> list[GpuDevice]:
    devices: list[GpuDevice] = []
    for name in gpu_names:
        vendor = classify_gpu_vendor(name)
        gpu_type = classify_gpu_type(name, vendor)
        estimated_vram = estimate_dedicated_vram_from_name(name) if gpu_type == "dedicated" else None
        dedicated_vram = gpu_vram_gb if gpu_type == "dedicated" and gpu_vram_gb is not None else estimated_vram
        confidence = classify_vram_confidence(
            name=name,
            gpu_type=gpu_type,
            adapter_ram_gb=gpu_vram_gb if gpu_type == "dedicated" else None,
            estimated_vram_gb=estimated_vram,
        )
        devices.append(
            GpuDevice(
                name=name,
                vendor=vendor,
                gpu_type=gpu_type,
                dedicated_vram_gb=dedicated_vram if confidence in {"detected", "estimated"} else None,
                vram_confidence=confidence,
                source="unknown",
            )
        )
    return devices


def _legacy_vram_from_primary(primary_gpu: GpuDevice | None, fallback: float | None) -> float | None:
    if primary_gpu and primary_gpu.dedicated_vram_gb is not None:
        return primary_gpu.dedicated_vram_gb
    return fallback


def scan_system() -> HardwareProfile:
    warnings: list[str] = []

    ram = _safe_call("内存", warnings, lambda: psutil.virtual_memory(), None)
    disk = _safe_call("磁盘", warnings, _disk_usage, None)
    platform_profile = _safe_call("平台", warnings, detect_platform_profile, None)
    raw_windows_gpus = _safe_call("Windows 显卡控制器", warnings, detector.detect_windows_gpu_controllers, [])
    gpus = parse_windows_gpu_controllers(raw_windows_gpus)
    legacy_gpu_vram_gb = None
    if gpus:
        gpu_names = [gpu.name for gpu in gpus]
    else:
        gpu_names = _safe_call("显卡", warnings, detector.detect_gpu_names, [])
        legacy_gpu_vram_gb = _safe_call("显存", warnings, detector.detect_gpu_vram_gb, None)
        gpus = _legacy_gpu_devices(gpu_names, legacy_gpu_vram_gb)

    primary_gpu, gpu_selection_reason = select_primary_gpu(gpus)
    gpu_vram_gb = _legacy_vram_from_primary(primary_gpu, legacy_gpu_vram_gb)
    nvidia_driver = _safe_call("NVIDIA 驱动", warnings, detector.detect_nvidia_driver, None)

    if not gpus:
        warnings.append("未检测到显卡名称。")
    if gpus and primary_gpu is None:
        warnings.append(gpu_selection_reason)
    if primary_gpu and primary_gpu.vram_confidence == "unknown":
        warnings.append("未能确认主要 GPU 的显存信息。")
    if any(gpu.vendor == "NVIDIA" for gpu in gpus) and nvidia_driver is None:
        warnings.append("未检测到 NVIDIA 驱动版本。")

    node_version = detector.get_command_version("node", ["--version"])
    git_version = detector.get_command_version("git", ["--version"])
    pnpm_version = detector.get_command_version("pnpm", ["--version"])
    docker_version = detector.get_command_version("docker", ["--version"])

    return HardwareProfile(
        os_name=platform.system() or "未知",
        os_version=platform.version() or platform.release() or "未知",
        architecture=platform.machine() or "未知",
        platform_profile=platform_profile,
        cpu_name=_safe_call("CPU", warnings, _cpu_name, None),
        cpu_cores=_safe_call("CPU 核心数", warnings, lambda: psutil.cpu_count(logical=True), None),
        total_ram_gb=bytes_to_gb(ram.total) if ram else None,
        gpu_names=gpu_names,
        gpus=gpus,
        primary_gpu=primary_gpu,
        gpu_selection_reason=gpu_selection_reason,
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
