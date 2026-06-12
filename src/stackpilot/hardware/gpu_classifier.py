from __future__ import annotations

from collections.abc import Mapping

from stackpilot.models import GpuType, GpuVendor, VramConfidence


VIRTUAL_GPU_MARKERS = (
    "microsoft basic display",
    "remote display",
    "rdp",
    "virtual display",
    "indirect display",
    "idddriver",
    "vmware",
    "virtualbox",
    "parallels",
    "hyper-v",
    "qxl",
    "virtio",
    "asklink",
    "oray",
)

NVIDIA_MARKERS = ("nvidia", "geforce", "rtx", "gtx", "quadro", "tesla")
AMD_MARKERS = ("amd", "radeon", "firepro")
INTEL_MARKERS = ("intel", "iris", "uhd graphics", "hd graphics", "arc")
APPLE_MARKERS = ("apple", "m1", "m2", "m3", "m4", "m5")

AMD_INTEGRATED_MARKERS = (
    "780m",
    "760m",
    "740m",
    "680m",
    "660m",
    "610m",
    "vega",
    "radeon graphics",
    "radeon(tm) graphics",
)

AMD_DEDICATED_MARKERS = ("radeon rx", "rx ", "radeon pro", "firepro", "radeon vii")
INTEL_INTEGRATED_MARKERS = ("uhd", "iris", "hd graphics", "arc graphics")
INTEL_DEDICATED_MARKERS = ("arc a", "arc b", "arc pro")


def _clean_name(name: str | None) -> str:
    return (name or "").casefold().strip()


def _raw_text(raw_fields: Mapping[str, object] | None) -> str:
    if not raw_fields:
        return ""
    return " ".join(str(value) for value in raw_fields.values() if value is not None).casefold()


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def classify_gpu_vendor(name: str | None) -> GpuVendor:
    """Classify the GPU vendor conservatively from a device name."""

    text = _clean_name(name)
    if not text:
        return "Unknown"
    if _contains_any(text, ("microsoft basic display", "microsoft remote display")):
        return "Microsoft"
    if _contains_any(text, NVIDIA_MARKERS):
        return "NVIDIA"
    if _contains_any(text, AMD_MARKERS):
        return "AMD"
    if _contains_any(text, INTEL_MARKERS):
        return "Intel"
    if _contains_any(text, APPLE_MARKERS):
        return "Apple"
    if "microsoft" in text:
        return "Microsoft"
    return "Unknown"


def classify_gpu_type(
    name: str | None,
    vendor: GpuVendor | str | None = None,
    raw_fields: Mapping[str, object] | None = None,
) -> GpuType:
    """Classify GPU device type without treating GPU as a synonym for dGPU."""

    text = _clean_name(name)
    combined = f"{text} {_raw_text(raw_fields)}"
    vendor_text = (vendor or classify_gpu_vendor(name)).casefold()

    if not text and not raw_fields:
        return "unknown"
    if _contains_any(combined, VIRTUAL_GPU_MARKERS):
        return "virtual"
    if vendor_text == "microsoft":
        return "virtual"
    if vendor_text == "nvidia":
        return "dedicated"
    if vendor_text == "apple":
        return "integrated"
    if vendor_text == "amd":
        if _contains_any(text, AMD_DEDICATED_MARKERS):
            return "dedicated"
        if _contains_any(text, AMD_INTEGRATED_MARKERS):
            return "integrated"
        return "unknown"
    if vendor_text == "intel":
        if _contains_any(text, INTEL_DEDICATED_MARKERS):
            return "dedicated"
        if _contains_any(text, INTEL_INTEGRATED_MARKERS):
            return "integrated"
        return "unknown"
    return "unknown"


def classify_vram_confidence(
    *,
    name: str | None = None,
    gpu_type: GpuType | str = "unknown",
    adapter_ram_gb: float | None = None,
    estimated_vram_gb: float | None = None,
    raw_fields: Mapping[str, object] | None = None,
) -> VramConfidence:
    """Return how much trust StackPilot should place in the VRAM value."""

    normalized_type = gpu_type if gpu_type in {"integrated", "dedicated", "virtual", "unknown"} else "unknown"
    text = f"{_clean_name(name)} {_raw_text(raw_fields)}"
    if normalized_type == "virtual" or _contains_any(text, VIRTUAL_GPU_MARKERS):
        return "unknown"
    if normalized_type == "integrated":
        return "shared"
    if normalized_type == "dedicated":
        if adapter_ram_gb is not None and 0 < adapter_ram_gb <= 128:
            return "detected"
        if estimated_vram_gb is not None and estimated_vram_gb > 0:
            return "estimated"
        return "unknown"
    return "unknown"
