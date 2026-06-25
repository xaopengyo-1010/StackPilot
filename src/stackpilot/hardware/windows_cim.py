from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
import re

from stackpilot.models import (
    BaseboardInfo,
    BiosInfo,
    ComputerModel,
    CpuInfo,
    DiskDevice,
    DiskVolume,
    MemoryInfo,
    MemoryModule,
)
from stackpilot.utils import bytes_to_gb


def _items(value: object) -> list[Mapping[str, object]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _field(data: Mapping[str, object] | None, *names: str) -> object | None:
    if not data or not isinstance(data, Mapping):
        return None
    lower_lookup = {str(key).casefold(): value for key, value in data.items()}
    for name in names:
        if name in data:
            return data[name]
        value = lower_lookup.get(name.casefold())
        if value is not None:
            return value
    return None


def _text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.casefold() in {"none", "null", "to be filled by o.e.m.", "default string"}:
        return None
    return text


def _int(value: object | None) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _gb(value: object | None) -> float | None:
    number = _int(value)
    return bytes_to_gb(number) if number is not None else None


def _date(value: object | None) -> str | None:
    text = _text(value)
    if not text:
        return None
    json_date = re.fullmatch(r"/Date\(([-+]?\d+)\)/", text)
    if json_date:
        try:
            return datetime.fromtimestamp(int(json_date.group(1)) / 1000, tz=timezone.utc).date().isoformat()
        except (OSError, OverflowError, ValueError):
            return text
    if len(text) >= 8 and text[:8].isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    for fmt in ("%Y%m%d%H%M%S.%f%z", "%Y%m%d%H%M%S.%f", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text


def _architecture(value: object | None) -> str | None:
    code = _int(value)
    if code is None:
        return _text(value)
    return {
        0: "x86",
        5: "ARM",
        9: "x86_64",
        12: "ARM64",
    }.get(code, str(code))


def parse_computer_model(raw: Mapping[str, object] | None) -> ComputerModel | None:
    if not raw:
        return None
    model = ComputerModel(
        manufacturer=_text(_field(raw, "Manufacturer")),
        model=_text(_field(raw, "Model")),
        system_family=_text(_field(raw, "SystemFamily")),
        system_sku=_text(_field(raw, "SystemSKUNumber", "SystemSku")),
        total_physical_memory_gb=_gb(_field(raw, "TotalPhysicalMemory")),
        source="cim",
    )
    return model if any([model.manufacturer, model.model, model.system_sku, model.total_physical_memory_gb]) else None


def parse_baseboard(raw: Mapping[str, object] | None) -> BaseboardInfo | None:
    if not raw:
        return None
    board = BaseboardInfo(
        manufacturer=_text(_field(raw, "Manufacturer")),
        product=_text(_field(raw, "Product")),
        version=_text(_field(raw, "Version")),
        serial_number=_text(_field(raw, "SerialNumber")),
        source="cim",
    )
    return board if any([board.manufacturer, board.product, board.version, board.serial_number]) else None


def parse_bios(raw: Mapping[str, object] | None) -> BiosInfo | None:
    if not raw:
        return None
    bios = BiosInfo(
        manufacturer=_text(_field(raw, "Manufacturer")),
        name=_text(_field(raw, "Name")),
        version=_text(_field(raw, "SMBIOSBIOSVersion", "Version")),
        release_date=_date(_field(raw, "ReleaseDate")),
        serial_number=_text(_field(raw, "SerialNumber")),
        source="cim",
    )
    return bios if any([bios.manufacturer, bios.name, bios.version, bios.release_date, bios.serial_number]) else None


def parse_cpu(processors: object, fallback_architecture: str | None = None) -> CpuInfo | None:
    items = _items(processors)
    if not items:
        return None
    first = items[0]
    physical = sum(_int(_field(item, "NumberOfCores")) or 0 for item in items) or None
    logical = sum(_int(_field(item, "NumberOfLogicalProcessors")) or 0 for item in items) or None
    cpu = CpuInfo(
        name=_text(_field(first, "Name")),
        manufacturer=_text(_field(first, "Manufacturer")),
        architecture=_architecture(_field(first, "Architecture")) or fallback_architecture,
        physical_cores=physical,
        logical_cores=logical,
        max_clock_mhz=_int(_field(first, "MaxClockSpeed")),
        source="cim",
    )
    return cpu if any([cpu.name, cpu.physical_cores, cpu.logical_cores, cpu.max_clock_mhz]) else None


def parse_memory(modules: object, total_bytes: object | None = None) -> MemoryInfo | None:
    parsed_modules: list[MemoryModule] = []
    for item in _items(modules):
        parsed_modules.append(
            MemoryModule(
                manufacturer=_text(_field(item, "Manufacturer")),
                part_number=_text(_field(item, "PartNumber")),
                capacity_gb=_gb(_field(item, "Capacity")),
                speed_mhz=_int(_field(item, "Speed", "ConfiguredClockSpeed")),
                bank_label=_text(_field(item, "BankLabel")),
                device_locator=_text(_field(item, "DeviceLocator")),
                source="cim",
            )
        )
    total_gb = _gb(total_bytes) or round(sum(module.capacity_gb or 0 for module in parsed_modules), 2) or None
    memory = MemoryInfo(total_gb=total_gb, modules=parsed_modules, source="cim")
    return memory if memory.total_gb is not None or memory.modules else None


def parse_disk_devices(disks: object) -> list[DiskDevice]:
    devices: list[DiskDevice] = []
    for item in _items(disks):
        devices.append(
            DiskDevice(
                model=_text(_field(item, "Model", "Caption")),
                interface_type=_text(_field(item, "InterfaceType", "BusType")),
                media_type=_text(_field(item, "MediaType")),
                size_gb=_gb(_field(item, "Size")),
                serial_number=_text(_field(item, "SerialNumber")),
                source="cim",
            )
        )
    return devices


def parse_disk_volumes(volumes: object) -> list[DiskVolume]:
    parsed: list[DiskVolume] = []
    for item in _items(volumes):
        parsed.append(
            DiskVolume(
                name=_text(_field(item, "DeviceID", "Name")),
                file_system=_text(_field(item, "FileSystem")),
                drive_type=_text(_field(item, "DriveType")),
                size_gb=_gb(_field(item, "Size")),
                free_gb=_gb(_field(item, "FreeSpace")),
                source="cim",
            )
        )
    return parsed


def parse_windows_hardware_snapshot(raw: Mapping[str, object] | None) -> dict[str, object]:
    if not raw:
        return {}
    computer = parse_computer_model(_field(raw, "ComputerSystem"))  # type: ignore[arg-type]
    total_memory = computer.total_physical_memory_gb if computer is not None else None
    total_memory_bytes = None if total_memory is None else int(total_memory * 1024**3)
    return {
        "computer_model": computer,
        "baseboard": parse_baseboard(_field(raw, "BaseBoard")),  # type: ignore[arg-type]
        "bios": parse_bios(_field(raw, "BIOS")),  # type: ignore[arg-type]
        "cpu": parse_cpu(_field(raw, "Processors")),
        "memory": parse_memory(_field(raw, "PhysicalMemory"), total_memory_bytes),
        "disks": parse_disk_devices(_field(raw, "DiskDrives")),
        "disk_volumes": parse_disk_volumes(_field(raw, "LogicalDisks")),
        "raw_gpu_controllers": _items(_field(raw, "VideoControllers")),
        "operating_system": _field(raw, "OperatingSystem"),
    }
