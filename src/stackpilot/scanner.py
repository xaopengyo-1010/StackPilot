from __future__ import annotations

import platform
from pathlib import Path
from subprocess import TimeoutExpired

import psutil

from . import detector
from .hardware.gpu_classifier import classify_gpu_type, classify_gpu_vendor, classify_vram_confidence
from .hardware.gpu_selector import select_primary_gpu
from .hardware.vram import estimate_dedicated_vram_from_name
from .hardware.windows_gpu import parse_windows_gpu_controllers
from .models import FailedCheck, GpuDevice, HardwareProfile
from .platform.detector import detect_platform_profile
from .utils import bytes_to_gb


CHECK_METADATA = {
    "memory": (
        "无法读取内存信息，内存容量相关建议可信度下降。",
        "任务管理器 -> 性能 -> 内存",
    ),
    "disk": (
        "无法读取磁盘空间，安装计划无法确认模型、缓存和软件占用是否安全。",
        "资源管理器 -> 此电脑；确认系统盘和目标安装盘剩余空间",
    ),
    "platform": (
        "无法读取系统平台信息，包管理器和安装后端判断会更保守。",
        "运行 systeminfo，或在系统设置中查看 Windows/macOS/Linux 版本",
    ),
    "gpu_controllers": (
        "无法读取显卡控制器，GPU 推荐只能使用备用探测或保守判断。",
        "任务管理器 -> 性能 -> GPU；或运行 nvidia-smi / lspci",
    ),
    "gpu_names": (
        "无法读取显卡名称，游戏、本地 AI 和创作类推荐可信度下降。",
        "设备管理器 -> 显示适配器",
    ),
    "gpu_vram": (
        "无法读取显存容量，ComfyUI、本地 LLM 和游戏建议会按保守规则处理。",
        "任务管理器 -> 性能 -> GPU；NVIDIA 用户也可以运行 nvidia-smi",
    ),
    "nvidia_driver": (
        "无法读取 NVIDIA 驱动版本，CUDA/PyTorch 兼容性需要人工确认。",
        "运行 nvidia-smi，或打开 NVIDIA App 查看驱动版本",
    ),
    "cpu": (
        "无法读取 CPU 名称，CPU 相关建议只能按核心数或未知硬件处理。",
        "任务管理器 -> 性能 -> CPU",
    ),
    "cpu_cores": (
        "无法读取 CPU 核心数，多任务、编译和本地模型建议会更保守。",
        "任务管理器 -> 性能 -> CPU",
    ),
    "python": (
        "无法确认 Python 版本，依赖 Python 的工具建议需要人工复核。",
        "运行 python --version 或 py --version",
    ),
    "node": (
        "无法确认 Node.js 版本，前端和 CLI 工具链建议需要人工复核。",
        "运行 node --version",
    ),
    "git": (
        "无法确认 Git 版本，版本控制和开源项目获取建议需要人工复核。",
        "运行 git --version",
    ),
    "pnpm": (
        "无法确认 pnpm 版本，JavaScript 包管理建议需要人工复核。",
        "运行 pnpm --version",
    ),
    "docker": (
        "无法确认 Docker 版本，容器相关建议需要人工复核。",
        "运行 docker --version，并确认 Docker Desktop 是否启动",
    ),
    "wsl": (
        "无法确认 WSL 状态，Windows 上的 Linux/容器工作流建议需要人工复核。",
        "运行 wsl --status 或 wsl -l -v",
    ),
}

PROBE_ERRORS = (
    PermissionError,
    FileNotFoundError,
    TimeoutError,
    TimeoutExpired,
    ValueError,
    TypeError,
    OSError,
    RuntimeError,
    psutil.Error,
)


def scan_system() -> HardwareProfile:
    failed_checks: list[FailedCheck] = []
    warnings: list[str] = []
    disk_anchor = Path.cwd().anchor or "/"

    def record_failure(check_name: str, status: str, reason: str) -> None:
        impact, manual_check = CHECK_METADATA.get(
            check_name,
            (
                "该检测项失败，相关建议会按保守规则处理。",
                "手动查看系统设置或运行对应命令确认",
            ),
        )
        failed_checks.append(
            FailedCheck(
                check_name=check_name,
                status=status,  # type: ignore[arg-type]
                reason=reason,
                impact=impact,
                manual_check=manual_check,
            )
        )

    def status_for(exc: Exception) -> str:
        if isinstance(exc, (PermissionError, psutil.AccessDenied)):
            return "permission_denied"
        if isinstance(exc, FileNotFoundError):
            return "command_not_found"
        if isinstance(exc, (TimeoutError, TimeoutExpired, psutil.TimeoutExpired)):
            return "timeout"
        if isinstance(exc, (ValueError, TypeError)):
            return "parse_failed"
        if isinstance(exc, OSError):
            return "unavailable"
        return "unknown_error"

    def probe(check_name: str, func, default=None):
        try:
            return func()
        except PROBE_ERRORS as exc:
            detail = str(exc).strip() or exc.__class__.__name__
            record_failure(check_name, status_for(exc), f"{check_name} 检测失败：{detail}")
            return default

    def command_version(check_name: str, command: str, args: list[str]) -> str | None:
        if not detector.command_exists(command):
            record_failure(
                check_name,
                "command_not_found",
                f"{command} 命令不存在，无法读取 {check_name} 版本。",
            )
            return None

        failure_count = len(failed_checks)
        version = probe(check_name, lambda: detector.get_command_version(command, args), None)
        if version is None and len(failed_checks) == failure_count:
            record_failure(
                check_name,
                "unavailable",
                f"{command} 命令存在，但未能读取可用版本输出。",
            )
        return version

    def cpu_name() -> str | None:
        cpu = platform.processor() or None
        if cpu or platform.system() != "Windows":
            return cpu
        output = detector.safe_run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name",
            ]
        )
        return output.splitlines()[0].strip() if output else None

    ram = probe("memory", psutil.virtual_memory)
    disk = probe("disk", lambda: psutil.disk_usage(disk_anchor))
    platform_profile = probe("platform", detect_platform_profile)
    raw_windows_gpus = probe("gpu_controllers", detector.detect_windows_gpu_controllers, [])
    gpus = parse_windows_gpu_controllers(raw_windows_gpus)
    legacy_gpu_vram_gb = None

    if gpus:
        gpu_names = [gpu.name for gpu in gpus]
    else:
        gpu_names = probe("gpu_names", detector.detect_gpu_names, [])
        legacy_gpu_vram_gb = probe("gpu_vram", detector.detect_gpu_vram_gb)
        gpus = []
        for name in gpu_names:
            vendor = classify_gpu_vendor(name)
            gpu_type = classify_gpu_type(name, vendor)
            estimated_vram = estimate_dedicated_vram_from_name(name) if gpu_type == "dedicated" else None
            confidence = classify_vram_confidence(
                name=name,
                gpu_type=gpu_type,
                adapter_ram_gb=legacy_gpu_vram_gb if gpu_type == "dedicated" else None,
                estimated_vram_gb=estimated_vram,
            )
            gpus.append(
                GpuDevice(
                    name=name,
                    vendor=vendor,
                    gpu_type=gpu_type,
                    dedicated_vram_gb=(
                        legacy_gpu_vram_gb if confidence == "detected" else estimated_vram if confidence == "estimated" else None
                    ),
                    vram_confidence=confidence,
                    source="unknown",
                )
            )

    primary_gpu, gpu_selection_reason = select_primary_gpu(gpus)
    gpu_vram_gb = (
        primary_gpu.dedicated_vram_gb
        if primary_gpu and primary_gpu.dedicated_vram_gb is not None
        else legacy_gpu_vram_gb
    )
    nvidia_driver = probe("nvidia_driver", detector.detect_nvidia_driver)

    if not gpus:
        warnings.append("未检测到显卡名称。")
    if gpus and primary_gpu is None:
        warnings.append(gpu_selection_reason)
    if primary_gpu and primary_gpu.vram_confidence == "unknown":
        warnings.append("未能确认主要 GPU 的显存信息。")
    if any(gpu.vendor == "NVIDIA" for gpu in gpus) and nvidia_driver is None:
        warnings.append("未检测到 NVIDIA 驱动版本。")

    python_version = probe("python", platform.python_version)
    node_version = command_version("node", "node", ["--version"])
    git_version = command_version("git", "git", ["--version"])
    pnpm_version = command_version("pnpm", "pnpm", ["--version"])
    docker_version = command_version("docker", "docker", ["--version"])

    return HardwareProfile(
        os_name=platform.system() or "未知",
        os_version=platform.version() or platform.release() or "未知",
        architecture=platform.machine() or "未知",
        platform_profile=platform_profile,
        failed_checks=failed_checks,
        cpu_name=probe("cpu", cpu_name),
        cpu_cores=probe("cpu_cores", lambda: psutil.cpu_count(logical=True)),
        total_ram_gb=bytes_to_gb(ram.total) if ram else None,
        gpu_names=gpu_names,
        gpus=gpus,
        primary_gpu=primary_gpu,
        gpu_selection_reason=gpu_selection_reason,
        gpu_vram_gb=gpu_vram_gb,
        disk_total_gb=bytes_to_gb(disk.total) if disk else None,
        disk_free_gb=bytes_to_gb(disk.free) if disk else None,
        disk_anchor=disk_anchor,
        python_installed=python_version is not None,
        python_version=python_version,
        node_installed=node_version is not None,
        node_version=node_version,
        git_installed=git_version is not None,
        git_version=git_version,
        pnpm_installed=pnpm_version is not None,
        pnpm_version=pnpm_version,
        docker_installed=docker_version is not None,
        docker_version=docker_version,
        wsl_available=probe("wsl", detector.detect_wsl, False),
        nvidia_driver_version=nvidia_driver,
        warnings=warnings,
    )
