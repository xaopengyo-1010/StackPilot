from __future__ import annotations

import re

from stackpilot.models import AppCatalogItem, AppRecommendation, HardwareProfile, RecommendationResult
from stackpilot.plans.models import InstallPlan, InstallSource, InstallStep, utc_now
from stackpilot.plans.policy import apply_step_policy
from stackpilot.security.sources import install_source_from_catalog
from stackpilot.templates import load_app_catalog
from stackpilot.utils import unique_preserve_order


def _safe(value: object | None) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, str) and not value.strip():
        return "未检测到"
    return str(value)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "-", value.strip().lower()).strip("-")
    return slug or "unknown"


def _hardware_summary(profile: HardwareProfile) -> dict[str, object]:
    return {
        "操作系统": f"{_safe(profile.os_name)} {_safe(profile.os_version)}".strip(),
        "系统架构": _safe(profile.architecture),
        "CPU": _safe(profile.cpu_name),
        "CPU 核心数": _safe(profile.cpu_cores),
        "内存 GB": _safe(profile.ram_gb),
        "显卡": "、".join(profile.gpu_names) if profile.gpu_names else "未检测到",
        "显存 GB": _safe(profile.vram_gb),
        "剩余磁盘 GB": _safe(profile.disk_free_gb),
        "Python": profile.python_version if profile.python_installed and profile.python_version else "未检测到",
        "Node.js": profile.node_version if profile.node_installed and profile.node_version else "未检测到",
        "Git": profile.git_version if profile.git_installed and profile.git_version else "未检测到",
        "Docker": profile.docker_version if profile.docker_installed and profile.docker_version else "未检测到",
    }


def _build_command(app: AppRecommendation, source: InstallSource) -> str | None:
    if source.type == "winget" and source.package_id:
        return f"winget install --id {source.package_id} --source winget"
    if source.type in {"official_url", "github_release", "microsoft_store"}:
        location = source.url or source.name
        return f"人工: 请先审查 {location}，确认来源可信后再手动安装 {app.name}。"
    if source.type in {"manual", "pypi", "npm", "docker_official"}:
        return f"人工: 请审查 {app.name} 的官方说明；当前不会生成自动安装命令。"
    return None


def _build_rollback(item: AppCatalogItem | None, source: InstallSource) -> str | None:
    if item and item.rollback_command:
        return item.rollback_command
    if source.type == "winget" and source.package_id:
        return f"winget uninstall {source.package_id}"
    return None


def _default_verify_commands(app_id: str, source: InstallSource) -> list[str]:
    known = {
        "git": ["git --version"],
        "python": ["python --version"],
        "nodejs": ["node --version"],
        "docker_desktop": ["docker --version"],
        "ffmpeg": ["ffmpeg -version"],
        "ollama": ["ollama --version"],
        "vscode": ["where code"],
    }
    if app_id in known:
        return known[app_id]
    if source.type == "winget" and source.package_id:
        return ["where winget"]
    return []


def _warnings_for(app: AppRecommendation, item: AppCatalogItem | None) -> list[str]:
    warnings = [*app.risk_notes]
    if item is not None:
        warnings.extend(item.risk_notes)
        if item.risk_note:
            warnings.append(item.risk_note)
    return unique_preserve_order(warnings)


def _step_from_app(index: int, app: AppRecommendation, item: AppCatalogItem | None) -> InstallStep:
    if item is None:
        source = InstallSource(
            type="unknown",
            name=app.name,
            url=None,
            package_id=None,
            trusted=False,
            notes=["推荐结果引用了 app_catalog.json 中不存在的应用。"],
        )
        return InstallStep(
            id=f"install-{index}-{_slug(app.app_id)}",
            app_id=app.app_id,
            app_name=app.name,
            action="manual",
            source=source,
            command=None,
            requires_admin=False,
            risk_level="blocked",
            reason=app.reason,
            estimated_disk_mb=None,
            rollback_command=None,
            verify_commands=[],
            preconditions=["未来执行前，先把经过审查的元数据补充到 configs/app_catalog.json。"],
            warnings=_warnings_for(app, item),
        )

    source = install_source_from_catalog(item)
    command = _build_command(app, source)
    verify_commands = item.verify_commands or _default_verify_commands(app.app_id, source)
    rollback_command = _build_rollback(item, source)
    action = "install" if source.type == "winget" else "manual"
    preconditions = [
        "未来执行前，先审查生成的安装计划。",
        "先创建或审查 StackPilot 备份 / 快照计划。",
    ]
    if item.requires_admin:
        preconditions.append("确认该应用需要管理员权限，且用户接受这个系统影响。")
    return InstallStep(
        id=f"install-{index}-{_slug(app.app_id)}",
        app_id=app.app_id,
        app_name=item.name,
        action=action,
        source=source,
        command=command,
        requires_admin=item.requires_admin,
        risk_level="low" if source.type in {"winget", "microsoft_store", "official_url"} else "medium",
        reason=app.reason,
        estimated_disk_mb=item.estimated_disk_mb,
        rollback_command=rollback_command,
        verify_commands=verify_commands,
        preconditions=preconditions,
        warnings=_warnings_for(app, item),
    )


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
        step = _step_from_app(index, app, item)
        step, findings = apply_step_policy(step)
        steps.append(step)
        findings_warnings.extend(finding.message for finding in findings if finding.level in {"warning", "blocked"})

    blocked_steps = [
        step
        for step in steps
        if step.risk_level in {"high", "blocked"} or step.source.type == "unknown"
    ]
    warnings = unique_preserve_order([*recommendation.risk_warnings, *findings_warnings])

    return InstallPlan(
        plan_id=f"plan-{recommendation.goal_id}-{utc_now()}",
        goal_id=recommendation.goal_id,
        goal_name=recommendation.goal_name,
        hardware_summary=_hardware_summary(profile),
        steps=steps,
        blocked_steps=blocked_steps,
        warnings=warnings,
        backup_recommendations=[
            "未来执行前，先审查 PATH、用户环境变量和系统环境变量。",
            "未来执行前，记录已安装软件列表。",
            "保留 StackPilot 安装计划、dry-run 输出和日志。",
            "在 StackPilot 以外做系统改动前，备份重要应用配置路径。",
        ],
        rollback_summary=(
            "StackPilot 可以规划卸载和恢复步骤，但软件安装可能写入文件、注册表项、"
            "缓存、驱动或用户数据，因此不能保证 100% 完全恢复。"
        ),
        dry_run_only=True,
    )
