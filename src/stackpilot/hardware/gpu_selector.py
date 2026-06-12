from __future__ import annotations

from collections.abc import Sequence

from stackpilot.models import GpuDevice


VRAM_CONFIDENCE_RANK = {
    "unknown": 0,
    "shared": 1,
    "estimated": 2,
    "detected": 3,
}

VENDOR_RANK = {
    "NVIDIA": 3,
    "AMD": 3,
    "Intel": 2,
    "Apple": 2,
    "Microsoft": 0,
    "Unknown": 1,
}


def _vram_value(gpu: GpuDevice) -> float:
    return gpu.dedicated_vram_gb or 0.0


def _selection_score(gpu: GpuDevice) -> tuple[int, float, int, str]:
    return (
        VRAM_CONFIDENCE_RANK.get(gpu.vram_confidence, 0),
        _vram_value(gpu),
        VENDOR_RANK.get(gpu.vendor, 1),
        gpu.name.casefold(),
    )


def _best_gpu(gpus: list[GpuDevice]) -> GpuDevice:
    return sorted(gpus, key=_selection_score, reverse=True)[0]


def select_primary_gpu(gpus: Sequence[GpuDevice]) -> tuple[GpuDevice | None, str]:
    """Select the GPU used for performance decisions with a user-readable reason."""

    devices = [gpu for gpu in gpus if isinstance(gpu, GpuDevice)]
    if not devices:
        return None, "未检测到 GPU 设备，无法可靠判断图形性能。"

    dedicated = [gpu for gpu in devices if gpu.gpu_type == "dedicated"]
    if dedicated:
        selected = _best_gpu(dedicated)
        return (
            selected,
            f"检测到独立显卡，因此优先使用 {selected.name} 作为主要性能判断 GPU。",
        )

    integrated = [gpu for gpu in devices if gpu.gpu_type == "integrated"]
    if integrated:
        selected = _best_gpu(integrated)
        return (
            selected,
            f"未检测到独立显卡，当前主要性能判断基于集成显卡 {selected.name}。",
        )

    unknown = [gpu for gpu in devices if gpu.gpu_type == "unknown"]
    if unknown:
        selected = _best_gpu(unknown)
        return (
            selected,
            f"无法确认 {selected.name} 的 GPU 类型，图形性能判断需要用户补充确认。",
        )

    return None, "仅检测到虚拟/基础显示设备，无法可靠判断图形性能。"
