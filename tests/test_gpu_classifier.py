from stackpilot.hardware.gpu_classifier import (
    classify_gpu_type,
    classify_gpu_vendor,
    classify_vram_confidence,
)


def test_classify_nvidia_rtx_as_dedicated():
    name = "NVIDIA GeForce RTX 4060 Laptop GPU"

    assert classify_gpu_vendor(name) == "NVIDIA"
    assert classify_gpu_type(name, "NVIDIA") == "dedicated"


def test_classify_amd_radeon_rx_as_dedicated():
    name = "AMD Radeon RX 7900 XTX"

    assert classify_gpu_vendor(name) == "AMD"
    assert classify_gpu_type(name, "AMD") == "dedicated"


def test_classify_amd_radeon_780m_as_integrated():
    name = "AMD Radeon 780M Graphics"

    assert classify_gpu_vendor(name) == "AMD"
    assert classify_gpu_type(name, "AMD") == "integrated"


def test_classify_intel_uhd_as_integrated():
    name = "Intel(R) UHD Graphics 770"

    assert classify_gpu_vendor(name) == "Intel"
    assert classify_gpu_type(name, "Intel") == "integrated"


def test_classify_intel_iris_xe_as_integrated():
    name = "Intel(R) Iris(R) Xe Graphics"

    assert classify_gpu_vendor(name) == "Intel"
    assert classify_gpu_type(name, "Intel") == "integrated"


def test_classify_microsoft_basic_display_as_virtual():
    name = "Microsoft Basic Display Adapter"

    assert classify_gpu_vendor(name) == "Microsoft"
    assert classify_gpu_type(name, "Microsoft") == "virtual"


def test_classify_remote_and_vmware_display_as_virtual():
    assert classify_gpu_type("Remote Display Adapter", "Unknown") == "virtual"
    assert classify_gpu_type("VMware SVGA 3D", "Unknown") == "virtual"
    assert classify_gpu_type("AskLinkIddDriver Device", "Unknown") == "virtual"
    assert classify_gpu_type("OrayIddDriver Device", "Unknown") == "virtual"


def test_classify_unknown_gpu_name_conservatively():
    name = "Example Future Graphics Device"

    assert classify_gpu_vendor(name) == "Unknown"
    assert classify_gpu_type(name, "Unknown") == "unknown"


def test_vram_confidence_detected_for_dedicated_adapter_ram():
    assert (
        classify_vram_confidence(gpu_type="dedicated", adapter_ram_gb=8)
        == "detected"
    )


def test_vram_confidence_shared_for_integrated_gpu():
    assert classify_vram_confidence(gpu_type="integrated", adapter_ram_gb=8) == "shared"


def test_vram_confidence_estimated_for_dedicated_name_estimate():
    assert (
        classify_vram_confidence(gpu_type="dedicated", estimated_vram_gb=8)
        == "estimated"
    )


def test_vram_confidence_unknown_for_invalid_or_virtual_values():
    assert classify_vram_confidence(gpu_type="dedicated", adapter_ram_gb=0) == "unknown"
    assert classify_vram_confidence(gpu_type="virtual", adapter_ram_gb=8) == "unknown"
