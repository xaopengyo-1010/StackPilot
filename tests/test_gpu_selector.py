from stackpilot.hardware.gpu_selector import select_primary_gpu
from stackpilot.models import GpuDevice


def gpu(name: str, gpu_type: str, **overrides) -> GpuDevice:
    data = {
        "name": name,
        "vendor": overrides.pop("vendor", "Unknown"),
        "gpu_type": gpu_type,
        "vram_confidence": overrides.pop("vram_confidence", "unknown"),
    }
    data.update(overrides)
    return GpuDevice(**data)


def test_select_primary_gpu_prefers_dedicated_over_integrated():
    integrated = gpu("AMD Radeon 780M", "integrated", vendor="AMD", vram_confidence="shared")
    dedicated = gpu(
        "NVIDIA GeForce RTX 4060 Laptop GPU",
        "dedicated",
        vendor="NVIDIA",
        dedicated_vram_gb=8,
        vram_confidence="detected",
    )

    selected, reason = select_primary_gpu([integrated, dedicated])

    assert selected == dedicated
    assert "独立显卡" in reason
    assert "RTX 4060" in reason


def test_select_primary_gpu_prefers_higher_confidence_then_vram_among_dedicated():
    estimated_large = gpu(
        "NVIDIA GeForce RTX 4070",
        "dedicated",
        vendor="NVIDIA",
        dedicated_vram_gb=12,
        vram_confidence="estimated",
    )
    detected_smaller = gpu(
        "NVIDIA GeForce RTX 4060",
        "dedicated",
        vendor="NVIDIA",
        dedicated_vram_gb=8,
        vram_confidence="detected",
    )

    selected, _ = select_primary_gpu([estimated_large, detected_smaller])

    assert selected == detected_smaller


def test_select_primary_gpu_uses_higher_vram_when_confidence_matches():
    smaller = gpu("NVIDIA GeForce RTX 4060", "dedicated", vendor="NVIDIA", dedicated_vram_gb=8, vram_confidence="detected")
    larger = gpu("NVIDIA GeForce RTX 4090", "dedicated", vendor="NVIDIA", dedicated_vram_gb=24, vram_confidence="detected")

    selected, _ = select_primary_gpu([smaller, larger])

    assert selected == larger


def test_select_primary_gpu_integrated_if_no_dedicated():
    integrated = gpu("Intel Iris Xe Graphics", "integrated", vendor="Intel", vram_confidence="shared")

    selected, reason = select_primary_gpu([integrated])

    assert selected == integrated
    assert "集成显卡" in reason


def test_select_primary_gpu_virtual_only_returns_none():
    virtual = gpu("Microsoft Basic Display Adapter", "virtual", vendor="Microsoft")

    selected, reason = select_primary_gpu([virtual])

    assert selected is None
    assert "虚拟" in reason


def test_select_primary_gpu_no_gpu_returns_none():
    selected, reason = select_primary_gpu([])

    assert selected is None
    assert "未检测到 GPU" in reason
