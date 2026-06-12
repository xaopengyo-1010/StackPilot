from .gpu_classifier import classify_gpu_type, classify_gpu_vendor, classify_vram_confidence
from .gpu_selector import select_primary_gpu
from .vram import adapter_ram_to_gb, estimate_dedicated_vram_from_name
from .windows_gpu import parse_windows_gpu_controllers

__all__ = [
    "adapter_ram_to_gb",
    "classify_gpu_type",
    "classify_gpu_vendor",
    "classify_vram_confidence",
    "estimate_dedicated_vram_from_name",
    "parse_windows_gpu_controllers",
    "select_primary_gpu",
]
