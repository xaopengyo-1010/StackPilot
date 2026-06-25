from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import (
    AppRecommendation,
    CapabilityTier,
    DiskRiskAnalysis,
    HardwareProfile,
    ModelPathRecommendation,
    RecommendationResult,
)
from .rules.engine import evaluate_rules, findings_to_not_recommended, findings_to_warnings
from .scanner import scan_system
from .scorer import score_template
from .templates import load_app_catalog, load_template
from .utils import model_to_dict, parse_model


TUI_SCENARIO_GOALS = {
    "coding": "coding_starter",
    "gaming": "gaming_setup",
    "ai": "comfyui_starter",
    "creator": "creator_setup",
}


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = value.strip()
        if text and text.casefold() not in seen:
            seen.add(text.casefold())
            result.append(text)
    return result


def _primary_gpu(profile: HardwareProfile):
    return profile.primary_gpu or (profile.gpus[0] if profile.gpus else None)


def _profile_from_data(raw_specs: HardwareProfile | Mapping[str, Any]) -> HardwareProfile:
    if isinstance(raw_specs, HardwareProfile):
        return raw_specs
    return parse_model(HardwareProfile, dict(raw_specs))


class StackPilotRecommender:
    """Pure-data recommendation API for TUI and other non-CLI frontends."""

    def evaluate(
        self,
        raw_specs: HardwareProfile | Mapping[str, Any],
        goal: str = "comfyui_starter",
    ) -> dict[str, Any]:
        profile = _profile_from_data(raw_specs)
        template_goal = TUI_SCENARIO_GOALS.get(goal, goal)
        recommendation = recommend(template_goal, profile=profile)
        primary_gpu = _primary_gpu(profile)

        scores: dict[str, float] = {}
        for scenario, template_id in TUI_SCENARIO_GOALS.items():
            template = load_template(template_id)
            findings = evaluate_rules(profile, template)
            scores[scenario] = score_template(profile, template, findings)

        risk_alerts = [
            {
                "level": "error" if finding.level == "critical" else "warning",
                "msg": finding.message,
                "id": finding.id,
                "component": finding.related_component,
            }
            for finding in recommendation.findings
            if finding.level in {"critical", "warning"}
        ]

        return {
            "hardware_summary": {
                "os": {
                    "name": profile.os_name,
                    "version": profile.os_version,
                    "architecture": profile.architecture,
                },
                "computer_model": model_to_dict(profile.computer_model)
                if profile.computer_model is not None
                else None,
                "baseboard": model_to_dict(profile.baseboard) if profile.baseboard is not None else None,
                "bios": model_to_dict(profile.bios) if profile.bios is not None else None,
                "cpu": {
                    "name": profile.cpu_name,
                    "cores": profile.cpu_cores,
                    "details": model_to_dict(profile.cpu) if profile.cpu is not None else None,
                },
                "memory": {
                    "ram_gb": profile.ram_gb,
                    "total_ram_gb": profile.total_ram_gb,
                    "details": model_to_dict(profile.memory) if profile.memory is not None else None,
                },
                "disk": {
                    "anchor": profile.disk_anchor,
                    "total_gb": profile.disk_total_gb,
                    "free_gb": profile.disk_free_gb,
                    "devices": [model_to_dict(disk) for disk in profile.disks],
                    "volumes": [model_to_dict(volume) for volume in profile.disk_volumes],
                },
                "gpus": [model_to_dict(gpu) for gpu in profile.gpus],
                "primary_gpu": model_to_dict(primary_gpu) if primary_gpu is not None else None,
                "gpu_selection_reason": profile.gpu_selection_reason,
                "tools": {
                    "python": {
                        "installed": profile.python_installed,
                        "version": profile.python_version,
                    },
                    "node": {
                        "installed": profile.node_installed,
                        "version": profile.node_version,
                    },
                    "git": {
                        "installed": profile.git_installed,
                        "version": profile.git_version,
                    },
                    "pnpm": {
                        "installed": profile.pnpm_installed,
                        "version": profile.pnpm_version,
                    },
                    "docker": {
                        "installed": profile.docker_installed,
                        "version": profile.docker_version,
                    },
                    "wsl": {
                        "installed": profile.wsl_installed,
                        "available": profile.wsl_available,
                        "version": profile.wsl_version,
                    },
                },
                "platform": model_to_dict(profile.platform_profile)
                if profile.platform_profile is not None
                else None,
                "failed_checks": [model_to_dict(check) for check in profile.failed_checks],
                "warnings": list(profile.warnings),
            },
            "scores": scores,
            "risk_alerts": risk_alerts,
            "recommendations": {
                "selected_goal": goal,
                "goal_id": recommendation.template_id,
                "goal_name": recommendation.display_name,
                "apps": [model_to_dict(app) for app in recommendation.recommended_apps],
                "config": list(recommendation.config_recommendations),
                "not_recommended": list(recommendation.not_recommended),
                "next_steps": list(recommendation.next_steps),
                "capability_tier": model_to_dict(recommendation.capability_tier)
                if recommendation.capability_tier is not None
                else None,
                "disk_risk_analysis": model_to_dict(recommendation.disk_risk_analysis)
                if recommendation.disk_risk_analysis is not None
                else None,
                "model_path_recommendation": model_to_dict(recommendation.model_path_recommendation)
                if recommendation.model_path_recommendation is not None
                else None,
            },
        }


def recommend(goal: str, profile: HardwareProfile | None = None) -> RecommendationResult:
    """Build a structured recommendation for a goal."""

    profile = profile or scan_system()
    template = load_template(goal)
    catalog = load_app_catalog()
    findings = evaluate_rules(profile, template)

    primary_gpu = _primary_gpu(profile)
    primary_vram_gb = (
        primary_gpu.dedicated_vram_gb
        if primary_gpu and primary_gpu.dedicated_vram_gb is not None
        else profile.vram_gb or profile.gpu_vram_gb
    )
    ram_gb = profile.ram_gb or profile.total_ram_gb
    is_windows = (
        profile.platform_profile.os_family == "windows"
        if profile.platform_profile is not None
        else "windows" in (profile.os_name or "").casefold()
    )
    system_drive = bool(profile.disk_anchor and profile.disk_anchor.casefold().startswith("c:"))
    local_ai_goal = goal in {"comfyui_starter", "local_llm"}
    has_nvidia = any(gpu.vendor == "NVIDIA" for gpu in profile.gpus) or any(
        "nvidia" in name.casefold() for name in profile.gpu_names
    )

    if is_windows:
        model_path_recommendation = ModelPathRecommendation(
            recommended_model_paths=[r"D:\AI\Models", r"D:\LLM\Models"],
            recommended_cache_paths=[r"D:\AI\Cache", r"D:\LLM\Cache"],
            avoid_paths=[r"C:\Users\...\Downloads", r"C:\Users\...\AppData", r"C:\Windows\Temp"],
            notes=[
                "模型目录和缓存目录要先规划，再下载大型模型。",
                "优先选择空间充足、路径清楚、便于备份的非系统盘目录。",
                "不要把 C:\\Users\\... 作为默认模型目录。",
            ],
        )
    else:
        model_path_recommendation = ModelPathRecommendation(
            recommended_model_paths=["/data/ai/models", "/data/llm/models"],
            recommended_cache_paths=["/data/ai/cache", "/data/llm/cache"],
            avoid_paths=["~/Downloads", "~/.cache on a small system disk", "/tmp"],
            notes=[
                "模型目录和缓存目录要先规划，再下载大型模型。",
                "优先选择空间充足、路径清楚、便于备份的非系统盘目录。",
            ],
        )
    if profile.disk_free_gb is not None:
        model_path_recommendation.notes.append(f"当前扫描盘剩余空间约 {profile.disk_free_gb:g}GB。")

    disk_reasons: list[str] = []
    disk_recommendations: list[str] = []
    disk_risk_level = "low"
    if profile.disk_free_gb is None:
        disk_risk_level = "medium"
        disk_reasons.append("未能确认磁盘剩余空间。")
        disk_recommendations.append("先手动确认系统盘和模型目标盘剩余空间。")
    elif profile.disk_free_gb < 30:
        disk_risk_level = "high"
        disk_reasons.append("当前扫描盘剩余空间低于 30GB。")
        disk_recommendations.append("先清理磁盘或迁移模型/缓存目录，再继续安装。")
    elif local_ai_goal and profile.disk_free_gb < 100:
        disk_risk_level = "medium"
        disk_reasons.append("本地 AI 模型、缓存和输出文件可能快速占用数十 GB。")
        disk_recommendations.append("模型目录和缓存目录建议放到非系统盘。")

    if local_ai_goal and system_drive:
        disk_risk_level = "medium" if disk_risk_level == "low" else disk_risk_level
        disk_reasons.append("当前扫描目录位于 C 盘，本地 AI 工作流容易挤占系统盘。")
        disk_recommendations.extend(
            [
                r"模型目录建议迁移到 D:\AI\Models 或其他非系统盘。",
                r"缓存目录建议迁移到 D:\AI\Cache 或其他非系统盘。",
            ]
        )
    if not disk_reasons:
        disk_reasons.append("当前磁盘空间没有触发明显风险规则。")
    if not disk_recommendations:
        disk_recommendations.append("继续保持模型、缓存和输出目录分离。")

    disk_risk_analysis = DiskRiskAnalysis(
        risk_level=disk_risk_level,  # type: ignore[arg-type]
        system_drive=profile.disk_anchor,
        disk_free_gb=profile.disk_free_gb,
        model_directory_status="not_configured",
        cache_directory_status="not_configured",
        reasons=disk_reasons,
        recommendations=disk_recommendations,
    )

    capability_tier = None
    if local_ai_goal:
        tier_risks: list[str] = []
        if primary_gpu is None:
            tier_name = "Unknown"
            suitable = ["只能按保守路径继续，先补充 GPU 型号和显存。"]
            not_suitable = ["不能据此判断重型 AI 工作流或 GPU 加速。"]
            tier_risks.append("GPU 信息缺失。")
        elif primary_gpu.gpu_type == "integrated":
            tier_name = "Entry"
            suitable = ["轻量测试", "低分辨率工作流", "学习基础流程"]
            not_suitable = ["Flux 重型工作流", "SDXL 高分辨率批量生成", "大上下文本地模型"]
            tier_risks.append("核显使用共享内存，不能当作独立显存。")
        elif primary_gpu.gpu_type == "dedicated" and primary_vram_gb is not None and primary_vram_gb >= 16:
            tier_name = "Advanced"
            suitable = ["较复杂 ComfyUI 工作流", "更大的本地模型", "更高分辨率测试"]
            not_suitable = ["无人工审查来源的模型和节点", "无限制批量生成"]
        elif primary_gpu.gpu_type == "dedicated" and primary_vram_gb is not None and primary_vram_gb >= 8:
            tier_name = "Standard"
            suitable = ["ComfyUI 入门到中等工作流", "7B 量化本地模型", "有限批量任务"]
            not_suitable = ["大型 Flux/SDXL 批量工作流", "大参数未量化模型"]
        elif primary_gpu.gpu_type == "dedicated":
            tier_name = "Entry"
            suitable = ["轻量 ComfyUI", "小模型或 CPU/内存路径"]
            not_suitable = ["重型图像生成", "大模型 GPU 加速"]
            tier_risks.append("独立显存偏低或未知。")
        else:
            tier_name = "Unknown"
            suitable = ["先确认 GPU 类型和显存。"]
            not_suitable = ["不能直接判断 AI 能力等级。"]
            tier_risks.append("GPU 类型未知。")

        if goal == "local_llm":
            if ram_gb is not None and ram_gb < 16:
                tier_risks.append("内存低于 16GB，本地 LLM 体验会明显受限。")
            if tier_name == "Advanced" and ram_gb is not None and ram_gb < 32:
                tier_name = "Standard"
                tier_risks.append("显存较强，但内存低于 32GB，降为 Standard。")
            if tier_name == "Entry":
                suitable = ["7B Q4/Q5 小模型", "短上下文", "CPU/内存优先路径"]
                not_suitable = ["32B/70B 模型", "长上下文", "多模型并行"]

        capability_tier = CapabilityTier(
            goal_id=goal,
            tier=tier_name,  # type: ignore[arg-type]
            suitable=suitable,
            not_suitable=not_suitable,
            risks=tier_risks or ["仍需按模型大小、驱动和实际工作流复核。"],
        )

    recommended_apps: list[AppRecommendation] = []
    for template_app in template.apps:
        app_id = template_app.app_id
        required = template_app.required
        reason = template_app.reason

        if app_id == "nvidia_app" and not has_nvidia:
            required = False
            reason = f"{reason} 未检测到 NVIDIA 显卡，因此这个项目可以跳过。"
        elif app_id == "cuda_pytorch_note" and not has_nvidia:
            required = False
            reason = f"{reason} 未检测到 NVIDIA 显卡，因此不要按 CUDA 必装路径处理。"

        notes: list[str] = []
        if app_id == "python" and not profile.python_installed:
            notes.append("当前未检测到 Python，先运行 python --version 或 py --version 复核。")
        if app_id == "git" and not profile.git_installed:
            notes.append("当前未检测到 Git，涉及克隆仓库、版本回滚或 custom nodes 前需要先复核。")
        if app_id == "docker_desktop" and not profile.docker_installed:
            notes.append("当前未检测到 Docker；只有需要容器、数据库沙箱或 Open WebUI 时才建议继续。")
        if (
            app_id == "wsl2_ubuntu"
            and profile.platform_profile
            and profile.platform_profile.os_family == "windows"
            and not profile.wsl_installed
        ):
            notes.append("当前未检测到 WSL，Linux 教程和容器工作流不能默认照抄。")
        if local_ai_goal and system_drive and app_id in {"comfyui", "ollama", "lm_studio"}:
            notes.append("当前目录位于 C 盘，模型和缓存建议放到非系统盘。")

        if primary_gpu is None:
            if goal in {"comfyui_starter", "local_llm", "gaming_setup", "creator_setup"}:
                notes.append("未能可靠确认 GPU，相关建议按保守配置处理。")
        elif goal == "comfyui_starter" and app_id == "comfyui":
            if primary_gpu.gpu_type == "integrated":
                notes.append(
                    f"当前主 GPU 为 {primary_gpu.name}（核显/共享内存），适合轻量 ComfyUI 学习，不适合 Flux、SDXL 高分辨率或批量生成。"
                )
            elif primary_gpu.gpu_type == "dedicated" and primary_gpu.dedicated_vram_gb is not None:
                notes.append(f"当前主 GPU 为 {primary_gpu.name}，独立显存约 {primary_gpu.dedicated_vram_gb:g}GB。")
            elif primary_gpu.gpu_type == "dedicated":
                notes.append(f"当前主 GPU 为 {primary_gpu.name}，但显存容量未知，需要先人工确认。")
            else:
                notes.append(f"当前 GPU 类型为 {primary_gpu.gpu_type}，ComfyUI 适配需要人工确认显卡型号和显存。")
        elif goal == "local_llm" and app_id in {"ollama", "lm_studio", "llama_cpp"}:
            if primary_gpu.gpu_type == "integrated":
                notes.append("当前主要依赖核显，建议优先按 CPU/内存路径选择小模型和低上下文。")
            elif primary_gpu.gpu_type == "dedicated" and primary_gpu.dedicated_vram_gb is not None:
                notes.append(
                    f"检测到独显 {primary_gpu.name}（约 {primary_gpu.dedicated_vram_gb:g}GB 显存），模型大小仍需按显存和内存选择。"
                )
            else:
                notes.append("GPU 加速能力不明确，建议先从小模型开始测试。")
        elif goal == "gaming_setup" and app_id in {"steam", "msi_afterburner", "rtss", "capframex"}:
            if primary_gpu.gpu_type == "integrated":
                notes.append(f"当前主 GPU 为 {primary_gpu.name}，更适合轻量游戏、云游戏或低画质设置。")
            elif primary_gpu.gpu_type == "dedicated":
                notes.append(f"检测到独显 {primary_gpu.name}，可以安装平台和监控工具，但画质建议仍取决于具体显存和驱动。")
            else:
                notes.append("图形性能无法确认，游戏画质建议需要人工补充显卡信息。")
        elif goal == "creator_setup" and app_id in {"obs_studio", "davinci_resolve", "blender", "ffmpeg"}:
            if primary_gpu.gpu_type == "integrated":
                notes.append(f"当前主 GPU 为 {primary_gpu.name}，适合轻量录屏/剪辑，不适合重型 4K、多轨或 3D 渲染。")
            elif primary_gpu.gpu_type == "dedicated":
                notes.append(f"检测到独显 {primary_gpu.name}，可考虑硬件编码、剪辑缓存和渲染加速。")
            else:
                notes.append("创作性能无法确认，需要先人工确认 GPU 类型和显存。")

        if notes:
            reason = f"{reason} 当前检测：{' '.join(notes)}"

        catalog_item = catalog.get(app_id)
        if catalog_item is None:
            recommended_apps.append(
                AppRecommendation(
                    app_id=app_id,
                    name=app_id,
                    required=required,
                    category="未知",
                    reason=reason,
                    install_method="从官方来源手动安装",
                    official_source="未知",
                    config_notes=[],
                    risk_notes=["模板引用了这个应用，但 app_catalog.json 中缺少对应条目。"],
                )
            )
            continue

        recommended_apps.append(
            AppRecommendation(
                app_id=catalog_item.app_id,
                name=catalog_item.name,
                required=required,
                category=catalog_item.category,
                reason=reason,
                install_method=catalog_item.install_methods[0] if catalog_item.install_methods else "手动安装",
                official_source=catalog_item.official_source,
                config_notes=catalog_item.config_notes,
                risk_notes=catalog_item.risk_notes,
            )
        )

    return RecommendationResult(
        template_id=template.template_id,
        display_name=template.display_name,
        name=template.display_name,
        category=template.category,
        suitability_score=score_template(profile, template, findings),
        summary=template.description,
        recommended_apps=recommended_apps,
        findings=findings,
        config_recommendations=_unique(template.config_recommendations),
        risk_warnings=_unique(findings_to_warnings(findings)),
        not_recommended=_unique([*template.not_recommended, *findings_to_not_recommended(findings)]),
        next_steps=_unique(
            [
                *template.next_steps,
                *[f"手动确认 {check.check_name}：{check.manual_check}" for check in profile.failed_checks],
            ]
        ),
        failed_checks=profile.failed_checks,
        disk_risk_analysis=disk_risk_analysis,
        model_path_recommendation=model_path_recommendation,
        capability_tier=capability_tier,
    )
