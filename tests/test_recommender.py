from stackpilot.models import FailedCheck, GpuDevice, HardwareProfile, PlatformProfile, RecommendationResult
from stackpilot.recommender import recommend


def sample_profile() -> HardwareProfile:
    dedicated_gpu = GpuDevice(
        name="NVIDIA GeForce RTX 4070",
        vendor="NVIDIA",
        gpu_type="dedicated",
        dedicated_vram_gb=12,
        vram_confidence="detected",
        driver_version="555.85",
        source="fixture",
    )
    platform_profile = PlatformProfile(
        os_family="windows",
        os_name="Windows",
        os_version="11",
        architecture="x86_64",
        package_managers=["winget"],
        default_installer_backend="winget",
    )
    return HardwareProfile(
        os_name="Windows",
        os_version="Windows 11",
        architecture="AMD64",
        cpu_name="Test CPU",
        cpu_cores=12,
        ram_gb=32,
        gpu_names=["NVIDIA GeForce RTX 4070"],
        gpus=[dedicated_gpu],
        primary_gpu=dedicated_gpu,
        gpu_selection_reason="检测到独立显卡，因此优先使用 NVIDIA GeForce RTX 4070 作为主要性能判断 GPU。",
        vram_gb=12,
        platform_profile=platform_profile,
        disk_total_gb=1000,
        disk_free_gb=300,
        python_installed=True,
        python_version="3.11.9",
        node_installed=True,
        node_version="v22.0.0",
        git_installed=True,
        git_version="git version 2.45.0",
        pnpm_installed=True,
        pnpm_version="9.0.0",
        docker_installed=False,
        docker_version=None,
        wsl_installed=True,
        wsl_version="2",
        nvidia_driver_version="555.85",
        warnings=[],
    )


def test_comfyui_starter_recommendation_contains_chinese_display_name():
    recommendation = recommend("comfyui_starter", profile=sample_profile())

    assert isinstance(recommendation, RecommendationResult)
    assert recommendation.template_id == "comfyui_starter"
    assert recommendation.display_name == "AI 绘图入门"
    assert recommendation.suitability_score > 0
    assert any(app.app_id == "comfyui" for app in recommendation.recommended_apps)
    assert recommendation.findings


def test_office_productivity_recommendation_succeeds():
    recommendation = recommend("office_productivity", profile=sample_profile())

    assert recommendation.template_id == "office_productivity"
    assert recommendation.display_name == "办公生产力"
    assert recommendation.suitability_score > 0
    assert any(app.app_id == "everything" for app in recommendation.recommended_apps)


def test_recommendation_result_splits_required_and_optional_apps():
    recommendation = recommend("office_productivity", profile=sample_profile())

    assert recommendation.required_apps
    assert recommendation.optional_apps
    assert all(app.required for app in recommendation.required_apps)
    assert all(not app.required for app in recommendation.optional_apps)


def test_recommendation_uses_structured_gpus_for_nvidia_detection():
    profile = sample_profile()
    profile.gpu_names = []

    recommendation = recommend("comfyui_starter", profile=profile)

    nvidia_app = next(app for app in recommendation.recommended_apps if app.app_id == "nvidia_app")
    assert "可以跳过" not in nvidia_app.reason


def test_recommendation_keeps_cuda_optional_without_nvidia_gpu():
    integrated_gpu = GpuDevice(
        name="AMD Radeon 780M Graphics",
        vendor="AMD",
        gpu_type="integrated",
        shared_memory_gb=4,
        vram_confidence="shared",
        source="fixture",
    )
    profile = sample_profile()
    profile.gpu_names = [integrated_gpu.name]
    profile.gpus = [integrated_gpu]
    profile.primary_gpu = integrated_gpu
    profile.gpu_selection_reason = "未检测到独立显卡，当前主要性能判断基于集成显卡 AMD Radeon 780M Graphics。"
    profile.vram_gb = None
    profile.nvidia_driver_version = None

    recommendation = recommend("comfyui_starter", profile=profile)

    cuda_note = next(app for app in recommendation.recommended_apps if app.app_id == "cuda_pytorch_note")
    nvidia_app = next(app for app in recommendation.recommended_apps if app.app_id == "nvidia_app")
    assert cuda_note.required is False
    assert "不要按 CUDA 必装路径处理" in cuda_note.reason
    assert nvidia_app.required is False
    assert "可以跳过" in nvidia_app.reason
    comfyui_app = next(app for app in recommendation.recommended_apps if app.app_id == "comfyui")
    assert "AMD Radeon 780M Graphics" in comfyui_app.reason
    assert "Flux" in comfyui_app.reason


def test_recommendation_consumes_failed_checks():
    profile = sample_profile()
    profile.failed_checks = [
        FailedCheck(
            check_name="gpu_vram",
            status="permission_denied",
            reason="gpu_vram 检测失败：access denied",
            impact="GPU 推荐可信度下降。",
            manual_check="任务管理器 -> 性能 -> GPU",
        )
    ]

    recommendation = recommend("comfyui_starter", profile=profile)

    assert recommendation.failed_checks
    assert any(finding.id == "failed_check_gpu_vram" for finding in recommendation.findings)
    assert any("任务管理器" in warning for warning in recommendation.risk_warnings)
    assert any("gpu_vram" in step for step in recommendation.next_steps)


def test_comfyui_integrated_gpu_gets_entry_capability_tier_and_path_guidance():
    integrated_gpu = GpuDevice(
        name="AMD Radeon 780M Graphics",
        vendor="AMD",
        gpu_type="integrated",
        shared_memory_gb=4,
        vram_confidence="shared",
        source="fixture",
    )
    profile = sample_profile()
    profile.gpu_names = [integrated_gpu.name]
    profile.gpus = [integrated_gpu]
    profile.primary_gpu = integrated_gpu
    profile.vram_gb = None
    profile.disk_anchor = "C:\\"
    profile.disk_free_gb = 80

    recommendation = recommend("comfyui_starter", profile=profile)

    assert recommendation.capability_tier is not None
    assert recommendation.capability_tier.tier == "Entry"
    assert any("Flux" in item for item in recommendation.capability_tier.not_suitable)
    assert recommendation.disk_risk_analysis is not None
    assert recommendation.disk_risk_analysis.risk_level == "medium"
    assert recommendation.model_path_recommendation is not None
    assert r"D:\AI\Models" in recommendation.model_path_recommendation.recommended_model_paths
    assert any(path.startswith("C:\\Users") for path in recommendation.model_path_recommendation.avoid_paths)


def test_comfyui_4060_gets_standard_tier_and_5090_gets_advanced_tier():
    standard_gpu = GpuDevice(
        name="NVIDIA GeForce RTX 4060",
        vendor="NVIDIA",
        gpu_type="dedicated",
        dedicated_vram_gb=8,
        vram_confidence="detected",
        source="fixture",
    )
    advanced_gpu = GpuDevice(
        name="NVIDIA GeForce RTX 5090",
        vendor="NVIDIA",
        gpu_type="dedicated",
        dedicated_vram_gb=32,
        vram_confidence="detected",
        source="fixture",
    )
    standard_profile = sample_profile()
    standard_profile.gpus = [standard_gpu]
    standard_profile.primary_gpu = standard_gpu
    standard_profile.vram_gb = 8
    advanced_profile = sample_profile()
    advanced_profile.gpus = [advanced_gpu]
    advanced_profile.primary_gpu = advanced_gpu
    advanced_profile.vram_gb = 32
    advanced_profile.ram_gb = 64

    standard = recommend("comfyui_starter", profile=standard_profile)
    advanced = recommend("local_llm", profile=advanced_profile)

    assert standard.capability_tier is not None
    assert standard.capability_tier.tier == "Standard"
    assert advanced.capability_tier is not None
    assert advanced.capability_tier.tier == "Advanced"
