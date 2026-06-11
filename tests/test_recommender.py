from stackpilot.models import HardwareProfile, RecommendationResult
from stackpilot.recommender import recommend


def sample_profile() -> HardwareProfile:
    return HardwareProfile(
        os_name="Windows",
        os_version="Windows 11",
        architecture="AMD64",
        cpu_name="Test CPU",
        cpu_cores=12,
        ram_gb=32,
        gpu_names=["NVIDIA GeForce RTX 4070"],
        vram_gb=12,
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
