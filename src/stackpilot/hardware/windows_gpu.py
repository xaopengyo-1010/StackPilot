from __future__ import annotations

from collections.abc import Iterable, Mapping

from stackpilot.hardware.gpu_classifier import (
    classify_gpu_type,
    classify_gpu_vendor,
    classify_vram_confidence,
)
from stackpilot.hardware.vram import adapter_ram_to_gb, estimate_dedicated_vram_from_name
from stackpilot.models import GpuDevice


FIELD_ALIASES = {
    "name": ("Name", "name"),
    "video_processor": ("VideoProcessor", "video_processor", "Video Processor"),
    "adapter_ram": ("AdapterRAM", "adapter_ram", "AdapterRam"),
    "driver_version": ("DriverVersion", "driver_version", "Driver Version"),
    "device_id": ("PNPDeviceID", "pnp_device_id", "DeviceID", "device_id"),
}


def _field(controller: Mapping[str, object], key: str) -> object | None:
    aliases = FIELD_ALIASES[key]
    lower_lookup = {str(raw_key).casefold(): raw_value for raw_key, raw_value in controller.items()}
    for alias in aliases:
        if alias in controller:
            return controller[alias]
        value = lower_lookup.get(alias.casefold())
        if value is not None:
            return value
    return None


def _text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_windows_gpu_controllers(raw_controllers: Iterable[Mapping[str, object]] | None) -> list[GpuDevice]:
    """Parse Win32_VideoController-like dictionaries into GPU devices."""

    if not raw_controllers:
        return []

    devices: list[GpuDevice] = []
    for controller in raw_controllers:
        if not isinstance(controller, Mapping):
            continue
        name = _text(_field(controller, "name")) or _text(_field(controller, "video_processor")) or "Unknown GPU"
        vendor = classify_gpu_vendor(name)
        gpu_type = classify_gpu_type(name, vendor, controller)
        adapter_ram_gb = adapter_ram_to_gb(_field(controller, "adapter_ram"))
        estimated_vram_gb = estimate_dedicated_vram_from_name(name) if gpu_type == "dedicated" else None
        if (
            gpu_type == "dedicated"
            and adapter_ram_gb is not None
            and estimated_vram_gb is not None
            and adapter_ram_gb <= 4
            and estimated_vram_gb > adapter_ram_gb
        ):
            adapter_ram_gb = None
        vram_confidence = classify_vram_confidence(
            name=name,
            gpu_type=gpu_type,
            adapter_ram_gb=adapter_ram_gb,
            estimated_vram_gb=estimated_vram_gb,
            raw_fields=controller,
        )

        dedicated_vram_gb = None
        shared_memory_gb = None
        if vram_confidence == "detected":
            dedicated_vram_gb = adapter_ram_gb
        elif vram_confidence == "estimated":
            dedicated_vram_gb = estimated_vram_gb
        elif vram_confidence == "shared":
            shared_memory_gb = adapter_ram_gb

        devices.append(
            GpuDevice(
                name=name,
                vendor=vendor,
                gpu_type=gpu_type,
                dedicated_vram_gb=dedicated_vram_gb,
                shared_memory_gb=shared_memory_gb,
                vram_confidence=vram_confidence,
                driver_version=_text(_field(controller, "driver_version")),
                device_id=_text(_field(controller, "device_id")),
                source="wmi",
            )
        )

    return devices
