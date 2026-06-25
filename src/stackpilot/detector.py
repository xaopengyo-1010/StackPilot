from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
from typing import Any

from .utils import model_to_dict, unique_preserve_order


class StackPilotDetector:
    """Pure-data detector API for future non-CLI frontends."""

    def scan_system(self) -> dict[str, Any]:
        from .scanner import scan_system

        return model_to_dict(scan_system())


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def safe_run(command: list[str]) -> str | None:
    if not command or any(not isinstance(part, str) or not part for part in command):
        return None

    creationflags = 0
    if platform.system() == "Windows" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            check=False,
            creationflags=creationflags,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None

    if completed.returncode != 0:
        return None

    output = (completed.stdout or completed.stderr or "").strip()
    return output or None


def get_command_version(command: str, args: list[str]) -> str | None:
    resolved = shutil.which(command)
    if resolved is None:
        return None
    output = safe_run([resolved, *args])
    if output is None:
        return None
    return output.splitlines()[0].strip() or None


def _powershell_command(script: str) -> str | None:
    shell = "powershell" if command_exists("powershell") else "pwsh"
    if not command_exists(shell):
        return None
    utf8_prefix = (
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        "$OutputEncoding = [Console]::OutputEncoding; "
    )
    return safe_run([shell, "-NoProfile", "-NonInteractive", "-Command", f"{utf8_prefix}{script}"])


def detect_wsl() -> bool:
    if platform.system() == "Windows":
        if not command_exists("wsl"):
            return False
        return safe_run(["wsl", "--status"]) is not None or safe_run(["wsl", "-l", "-q"]) is not None

    try:
        with open("/proc/version", "r", encoding="utf-8", errors="ignore") as handle:
            return "microsoft" in handle.read().casefold()
    except OSError:
        return False


def detect_nvidia_driver() -> str | None:
    if command_exists("nvidia-smi"):
        output = safe_run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"])
        if output:
            return output.splitlines()[0].strip()

    if platform.system() == "Windows":
        output = _powershell_command(
            "Get-CimInstance Win32_VideoController | "
            "Where-Object { $_.Name -match 'NVIDIA' } | "
            "Select-Object -First 1 -ExpandProperty DriverVersion"
        )
        if output:
            return output.splitlines()[0].strip()

    return None


def detect_gpu_names() -> list[str]:
    names: list[str] = []

    if command_exists("nvidia-smi"):
        output = safe_run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        if output:
            names.extend(line.strip() for line in output.splitlines())

    if platform.system() == "Windows":
        output = _powershell_command("Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }")
        if output:
            names.extend(line.strip() for line in output.splitlines())
    elif platform.system() == "Darwin" and command_exists("system_profiler"):
        output = safe_run(["system_profiler", "SPDisplaysDataType"])
        if output:
            for line in output.splitlines():
                if "Chipset Model:" in line:
                    names.append(line.split(":", 1)[1].strip())
    elif command_exists("lspci"):
        output = safe_run(["lspci"])
        if output:
            for line in output.splitlines():
                lowered = line.casefold()
                if "vga compatible controller" in lowered or "3d controller" in lowered or "display controller" in lowered:
                    names.append(line.split(":", 2)[-1].strip())

    return unique_preserve_order(names)


def detect_windows_gpu_controllers() -> list[dict[str, object]]:
    if platform.system() != "Windows":
        return []

    output = _powershell_command(
        "Get-CimInstance Win32_VideoController | "
        "Select-Object Name,VideoProcessor,AdapterRAM,DriverVersion,PNPDeviceID | "
        "ConvertTo-Json -Depth 3"
    )
    if not output:
        return []
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return []
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def detect_windows_hardware_snapshot() -> dict[str, object]:
    if platform.system() != "Windows":
        return {}

    output = _powershell_command(
        "$payload = [ordered]@{"
        "ComputerSystem = Get-CimInstance Win32_ComputerSystem | "
        "Select-Object Manufacturer,Model,SystemFamily,SystemSKUNumber,TotalPhysicalMemory;"
        "BaseBoard = Get-CimInstance Win32_BaseBoard | "
        "Select-Object Manufacturer,Product,Version,SerialNumber;"
        "BIOS = Get-CimInstance Win32_BIOS | "
        "Select-Object Manufacturer,Name,SMBIOSBIOSVersion,Version,ReleaseDate,SerialNumber;"
        "Processors = @(Get-CimInstance Win32_Processor | "
        "Select-Object Name,Manufacturer,Architecture,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed);"
        "PhysicalMemory = @(Get-CimInstance Win32_PhysicalMemory | "
        "Select-Object Manufacturer,PartNumber,Capacity,Speed,ConfiguredClockSpeed,BankLabel,DeviceLocator);"
        "DiskDrives = @(Get-CimInstance Win32_DiskDrive | "
        "Select-Object Model,Caption,InterfaceType,MediaType,Size,SerialNumber);"
        "LogicalDisks = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | "
        "Select-Object DeviceID,Name,FileSystem,DriveType,Size,FreeSpace);"
        "VideoControllers = @(Get-CimInstance Win32_VideoController | "
        "Select-Object Name,VideoProcessor,AdapterRAM,DriverVersion,PNPDeviceID);"
        "OperatingSystem = Get-CimInstance Win32_OperatingSystem | "
        "Select-Object Caption,Version,BuildNumber,OSArchitecture"
        "}; $payload | ConvertTo-Json -Depth 5"
    )
    if not output:
        return {}
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def detect_gpu_vram_gb() -> float | None:
    values_gb: list[float] = []

    if command_exists("nvidia-smi"):
        output = safe_run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"])
        if output:
            for line in output.splitlines():
                match = re.search(r"\d+(?:\.\d+)?", line)
                if match:
                    values_gb.append(float(match.group(0)) / 1024)

    if platform.system() == "Windows":
        output = _powershell_command("Get-CimInstance Win32_VideoController | ForEach-Object { $_.AdapterRAM }")
        if output:
            for line in output.splitlines():
                try:
                    value = int(line.strip())
                except ValueError:
                    continue
                if value > 0:
                    values_gb.append(value / (1024 ** 3))

    if not values_gb:
        return None
    return round(max(values_gb), 2)


def infer_vram_from_names(gpu_names: list[str]) -> float | None:
    joined = " ".join(gpu_names).upper()
    if not joined:
        return None

    known_models = {
        "4090": 24,
        "3090": 24,
        "4080": 16,
        "3080": 10,
        "4070": 12,
        "3070": 8,
        "3060": 12,
        "4060": 8,
        "2080": 8,
        "2070": 8,
        "2060": 6,
        "1660": 6,
        "1650": 4,
        "1060": 6,
        "1050": 4,
    }
    for model, vram in known_models.items():
        if model in joined:
            return float(vram)

    if "RTX" in joined:
        return 8.0
    if "GTX" in joined:
        return 4.0
    if "RADEON" in joined or "RX " in joined:
        return 8.0
    if "ARC" in joined:
        return 8.0
    return None
