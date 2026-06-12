from stackpilot.models import GpuDevice, HardwareProfile, PlatformProfile, RecommendationResult, RuleFinding
from stackpilot.utils import model_to_dict


def test_hardware_profile_can_be_created_and_serialized():
    profile = HardwareProfile(
        os_name="Windows",
        os_version="Windows 11",
        architecture="AMD64",
        cpu_name=None,
        cpu_cores=8,
        ram_gb=16,
        gpu_name="Test GPU",
        vram_gb=8,
        disk_total_gb=512,
        disk_free_gb=128,
        python_installed=True,
        python_version="3.11.9",
        node_installed=False,
        git_installed=True,
        git_version="git version 2.45.0",
        pnpm_installed=False,
        docker_installed=False,
        wsl_installed=False,
    )

    payload = model_to_dict(profile)

    assert payload["ram_gb"] == 16
    assert payload["total_ram_gb"] == 16
    assert payload["vram_gb"] == 8
    assert payload["gpu_vram_gb"] == 8
    assert payload["gpu_names"] == ["Test GPU"]


def test_gpu_device_serialization_and_type_flags_are_consistent():
    gpu = GpuDevice(
        name="NVIDIA GeForce RTX 4060 Laptop GPU",
        vendor="NVIDIA",
        gpu_type="dedicated",
        dedicated_vram_gb=8,
        vram_confidence="detected",
        driver_version="555.85",
        source="wmi",
    )

    payload = model_to_dict(gpu)

    assert payload["name"] == "NVIDIA GeForce RTX 4060 Laptop GPU"
    assert payload["vendor"] == "NVIDIA"
    assert payload["gpu_type"] == "dedicated"
    assert payload["is_dedicated"] is True
    assert payload["is_integrated"] is False
    assert payload["is_virtual"] is False
    assert payload["vram_confidence"] == "detected"


def test_gpu_device_markdown_summary_does_not_leak_none():
    gpu = GpuDevice(name="AMD Radeon 780M", vendor="AMD", gpu_type="integrated", vram_confidence="shared")

    summary = gpu.markdown_summary()

    assert "None" not in summary
    assert "AMD Radeon 780M" in summary
    assert "共享内存" in summary


def test_hardware_profile_supports_multiple_gpus_and_primary_gpu():
    integrated = GpuDevice(name="AMD Radeon 780M", vendor="AMD", gpu_type="integrated", vram_confidence="shared")
    dedicated = GpuDevice(
        name="NVIDIA GeForce RTX 4060 Laptop GPU",
        vendor="NVIDIA",
        gpu_type="dedicated",
        dedicated_vram_gb=8,
        vram_confidence="detected",
    )

    profile = HardwareProfile(
        os_name="Windows",
        os_version="Windows 11",
        architecture="AMD64",
        gpus=[integrated, dedicated],
        primary_gpu=dedicated,
        gpu_selection_reason="检测到独立显卡，因此优先用于图形性能判断。",
    )
    payload = model_to_dict(profile)

    assert profile.gpu_names == ["AMD Radeon 780M", "NVIDIA GeForce RTX 4060 Laptop GPU"]
    assert profile.gpu_name == "AMD Radeon 780M"
    assert profile.primary_gpu is not None
    assert profile.primary_gpu.name == "NVIDIA GeForce RTX 4060 Laptop GPU"
    assert payload["gpus"][0]["gpu_type"] == "integrated"
    assert payload["primary_gpu"]["gpu_type"] == "dedicated"
    assert "独立显卡" in payload["gpu_selection_reason"]


def test_platform_profile_serialization():
    profile = PlatformProfile(
        os_family="windows",
        os_name="Windows",
        os_version="11",
        architecture="x86_64",
        package_managers=["winget"],
        default_installer_backend="winget",
    )

    payload = model_to_dict(profile)

    assert payload["os_family"] == "windows"
    assert payload["architecture"] == "x86_64"
    assert payload["package_managers"] == ["winget"]
    assert payload["default_installer_backend"] == "winget"


def test_recommendation_result_can_include_findings():
    finding = RuleFinding(
        id="disk_free_low",
        level="critical",
        title="磁盘空间不足",
        message="当前剩余磁盘空间低于 30GB。",
        related_goal="comfyui_starter",
        related_component="disk",
        evidence={"disk_free_gb": 12},
    )
    recommendation = RecommendationResult(
        template_id="comfyui_starter",
        display_name="AI 绘图入门",
        name="AI 绘图入门",
        category="AI",
        suitability_score=75,
        summary="测试",
        findings=[finding],
    )

    assert recommendation.goal_id == "comfyui_starter"
    assert recommendation.warnings == ["当前剩余磁盘空间低于 30GB。"]
