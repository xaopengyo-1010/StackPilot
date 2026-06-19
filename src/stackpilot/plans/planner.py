from __future__ import annotations

import re

from stackpilot.models import AppCatalogItem, HardwareProfile, RecommendationResult
from stackpilot.plans.models import InstallPlan, InstallSource, InstallStep, utc_now
from stackpilot.plans.policy import apply_step_policy
from stackpilot.security.sources import install_source_from_catalog
from stackpilot.templates import load_app_catalog
from stackpilot.utils import unique_preserve_order


VERIFY_COMMANDS = {
    "git": ["git --version"],
    "python": ["python --version"],
    "nodejs": ["node --version"],
    "docker_desktop": ["docker --version"],
    "ffmpeg": ["ffmpeg -version"],
    "ollama": ["ollama --version"],
    "vscode": ["where code"],
}


def _safe(value: object | None) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, str) and not value.strip():
        return "未检测到"
    return str(value)


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "-", value.strip().lower()).strip("-") or "unknown"


def build_install_plan(
    profile: HardwareProfile,
    recommendation: RecommendationResult,
    app_catalog: dict[str, AppCatalogItem] | None = None,
) -> InstallPlan:
    """Build an auditable dry-run install plan from a recommendation result."""

    catalog = app_catalog or load_app_catalog()
    steps: list[InstallStep] = []
    findings_warnings: list[str] = []

    for index, app in enumerate(recommendation.recommended_apps, start=1):
        item = catalog.get(app.app_id)
        step_id = f"install-{index}-{_slug(app.app_id)}"

        if item is None:
            step = InstallStep(
                id=step_id,
                app_id=app.app_id,
                app_name=app.name,
                action="manual",
                source=InstallSource(
                    type="unknown",
                    name=app.name,
                    url=None,
                    package_id=None,
                    trusted=False,
                    notes=["推荐结果引用了 app_catalog.json 中不存在的应用。"],
                ),
                command=None,
                requires_admin=False,
                risk_level="blocked",
                reason=app.reason,
                estimated_disk_mb=None,
                rollback_command=None,
                verify_commands=[],
                preconditions=["执行前，先把经过审查的元数据补充到 configs/app_catalog.json。"],
                warnings=unique_preserve_order(app.risk_notes),
            )
        else:
            source = install_source_from_catalog(item)
            if source.type == "winget" and source.package_id:
                command = f"winget install --id {source.package_id} --source winget"
            elif source.type in {"official_url", "github_release", "microsoft_store"}:
                command = f"人工: 请先审查 {source.url or source.name}，确认来源可信后再手动安装 {app.name}。"
            elif source.type in {"manual", "pypi", "npm", "docker_official"}:
                command = f"人工: 请审查 {app.name} 的官方说明；当前不会生成自动安装命令。"
            else:
                command = None

            verify_commands = item.verify_commands or VERIFY_COMMANDS.get(app.app_id, [])
            if not verify_commands and source.type == "winget" and source.package_id:
                verify_commands = ["where winget"]

            preconditions = [
                "执行前，先审查生成的安装计划。",
                "先创建或审查 StackPilot 备份 / 快照计划。",
            ]
            if item.requires_admin:
                preconditions.append("确认该应用需要管理员权限，且用户接受这个系统影响。")

            step = InstallStep(
                id=step_id,
                app_id=app.app_id,
                app_name=item.name,
                action="install" if source.type == "winget" else "manual",
                source=source,
                command=command,
                requires_admin=item.requires_admin,
                risk_level="low" if source.type in {"winget", "microsoft_store", "official_url"} else "medium",
                reason=app.reason,
                estimated_disk_mb=item.estimated_disk_mb,
                rollback_command=item.rollback_command
                or (f"winget uninstall {source.package_id}" if source.type == "winget" and source.package_id else None),
                verify_commands=verify_commands,
                preconditions=preconditions,
                warnings=unique_preserve_order(
                    [
                        *app.risk_notes,
                        *item.risk_notes,
                        *([item.risk_note] if item.risk_note else []),
                    ]
                ),
            )

        step, findings = apply_step_policy(step)
        steps.append(step)
        findings_warnings.extend(finding.message for finding in findings if finding.level in {"warning", "blocked"})

    gpu_summary = (
        "; ".join(gpu.markdown_summary() for gpu in profile.gpus)
        if profile.gpus
        else "、".join(profile.gpu_names)
        if profile.gpu_names
        else "未检测到"
    )
    platform_summary = {
        "平台类型": "unknown",
        "包管理器": "未检测到",
        "默认安装后端": "unknown",
    }
    if profile.platform_profile is not None:
        platform_summary = {
            "平台类型": profile.platform_profile.os_family,
            "包管理器": "、".join(profile.platform_profile.package_managers)
            if profile.platform_profile.package_managers
            else "未检测到",
            "默认安装后端": profile.platform_profile.default_installer_backend,
        }

    hardware_summary: dict[str, object] = {
        "操作系统": f"{_safe(profile.os_name)} {_safe(profile.os_version)}".strip(),
        "系统架构": _safe(profile.architecture),
        **platform_summary,
        "CPU": _safe(profile.cpu_name),
        "CPU 核心数": _safe(profile.cpu_cores),
        "内存 GB": _safe(profile.ram_gb),
        "检测到的 GPU": gpu_summary,
        "主要性能判断 GPU": profile.primary_gpu.name if profile.primary_gpu else "未能可靠确认",
        "GPU 选择原因": profile.gpu_selection_reason or "未能可靠确认 GPU 选择原因",
        "兼容显存 GB": _safe(profile.vram_gb),
        "剩余磁盘 GB": _safe(profile.disk_free_gb),
        "Python": profile.python_version if profile.python_installed and profile.python_version else "未检测到",
        "Node.js": profile.node_version if profile.node_installed and profile.node_version else "未检测到",
        "Git": profile.git_version if profile.git_installed and profile.git_version else "未检测到",
        "Docker": profile.docker_version if profile.docker_installed and profile.docker_version else "未检测到",
        "检测失败项": [
            f"{check.check_name} ({check.status}): {check.impact} 手动确认：{check.manual_check}"
            for check in profile.failed_checks
        ]
        or "暂无",
    }
    if recommendation.capability_tier is not None:
        hardware_summary.update(
            {
                "能力分级": recommendation.capability_tier.tier,
                "能力分级适合": recommendation.capability_tier.suitable,
                "能力分级不适合": recommendation.capability_tier.not_suitable,
            }
        )
    if recommendation.disk_risk_analysis is not None:
        hardware_summary.update(
            {
                "磁盘风险等级": recommendation.disk_risk_analysis.risk_level,
                "磁盘风险原因": recommendation.disk_risk_analysis.reasons,
                "磁盘风险建议": recommendation.disk_risk_analysis.recommendations,
            }
        )
    if recommendation.model_path_recommendation is not None:
        hardware_summary.update(
            {
                "推荐模型目录": recommendation.model_path_recommendation.recommended_model_paths,
                "推荐缓存目录": recommendation.model_path_recommendation.recommended_cache_paths,
                "避免模型目录": recommendation.model_path_recommendation.avoid_paths,
            }
        )

    failed_check_warnings = [
        f"{check.check_name} 检测失败：{check.impact} 手动确认：{check.manual_check}"
        for check in recommendation.failed_checks
    ]
    disk_warnings = (
        recommendation.disk_risk_analysis.reasons + recommendation.disk_risk_analysis.recommendations
        if recommendation.disk_risk_analysis is not None
        else []
    )
    path_warnings = (
        recommendation.model_path_recommendation.notes
        if recommendation.model_path_recommendation is not None
        else []
    )

    return InstallPlan(
        plan_id=f"plan-{recommendation.goal_id}-{utc_now()}",
        goal_id=recommendation.goal_id,
        goal_name=recommendation.goal_name,
        hardware_summary=hardware_summary,
        steps=steps,
        blocked_steps=[
            step for step in steps if step.risk_level in {"high", "blocked"} or step.source.type == "unknown"
        ],
        warnings=unique_preserve_order(
            [
                *recommendation.risk_warnings,
                *failed_check_warnings,
                *disk_warnings,
                *path_warnings,
                *findings_warnings,
            ]
        ),
        backup_recommendations=[
            "执行前，先审查 PATH、用户环境变量和系统环境变量。",
            "执行前，记录已安装软件列表。",
            "保留 StackPilot 安装计划、dry-run 输出和日志。",
            "在 StackPilot 以外做系统改动前，备份重要应用配置路径。",
        ],
        rollback_summary=(
            "StackPilot 可以规划卸载和恢复步骤，但软件安装可能写入文件、注册表项、"
            "缓存、驱动或用户数据，因此不能保证 100% 完全恢复。"
        ),
        dry_run_only=True,
    )
