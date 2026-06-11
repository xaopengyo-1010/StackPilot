from stackpilot.models import HardwareProfile, RecommendationResult, RuleFinding
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
