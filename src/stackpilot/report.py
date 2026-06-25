from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import HardwareProfile, RecommendationResult, ReportData
from .recommender import recommend
from .scanner import scan_system
from .templates import project_root, template_audience
from .utils import model_to_dict


REPORT_MD = "stackpilot-report.md"
REPORT_JSON = "stackpilot-report.json"
TRANSPARENCY_NOTICE = (
    "StackPilot 当前版本只生成本地推荐报告，不会自动下载、安装软件或修改系统设置。"
)


def default_output_dir() -> Path:
    return project_root() / "outputs" / "reports"


def _missing(value: object | None) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, str) and not value.strip():
        return "未检测到"
    return str(value)


def _gb(value: float | None) -> str:
    return "未检测到" if value is None else f"{value:g} GB"


def _list(values: list[str], empty_text: str) -> str:
    return "\n".join(f"- {value}" for value in values) if values else empty_text


def _join_parts(*parts: object | None) -> str:
    values = [_missing(part) for part in parts if part is not None and _missing(part) != "未检测到"]
    return " / ".join(values) if values else "未检测到"


def _hardware_detail_lines(profile: HardwareProfile) -> list[str]:
    lines: list[str] = []
    if profile.computer_model is not None:
        lines.append(
            f"- 整机型号：{_join_parts(profile.computer_model.manufacturer, profile.computer_model.model, profile.computer_model.system_sku)}"
        )
    if profile.baseboard is not None:
        lines.append(f"- 主板：{_join_parts(profile.baseboard.manufacturer, profile.baseboard.product, profile.baseboard.version)}")
    if profile.bios is not None:
        lines.append(f"- BIOS：{_join_parts(profile.bios.manufacturer, profile.bios.version, profile.bios.release_date)}")
    if profile.cpu is not None:
        cores = (
            f"{profile.cpu.physical_cores or '?'}C/{profile.cpu.logical_cores or '?'}T"
            if profile.cpu.physical_cores or profile.cpu.logical_cores
            else None
        )
        clock = f"{profile.cpu.max_clock_mhz} MHz" if profile.cpu.max_clock_mhz else None
        lines.append(f"- CPU 详情：{_join_parts(profile.cpu.name, cores, clock)}")
    if profile.memory is not None:
        lines.append(f"- 内存详情：总计 {_gb(profile.memory.total_gb)}")
        for module in profile.memory.modules:
            lines.append(
                f"  - {_join_parts(module.device_locator or module.bank_label, _gb(module.capacity_gb), f'{module.speed_mhz} MHz' if module.speed_mhz else None)}"
            )
    if profile.disks:
        lines.append("- 物理磁盘：")
        for disk in profile.disks:
            lines.append(f"  - {_join_parts(disk.model, _gb(disk.size_gb), disk.media_type, disk.interface_type)}")
    if profile.disk_volumes:
        lines.append("- 磁盘卷：")
        for volume in profile.disk_volumes:
            lines.append(f"  - {_join_parts(volume.name, volume.file_system, f'总计 {_gb(volume.size_gb)}', f'剩余 {_gb(volume.free_gb)}')}")
    return lines


def render_markdown(report_data: ReportData) -> str:
    """Render a Chinese Markdown report from structured report data."""

    profile = report_data.hardware_profile
    recommendation = report_data.recommendation

    gpu_text = (
        "\n".join(f"  - {gpu.markdown_summary()}" for gpu in profile.gpus)
        if profile.gpus
        else "、".join(profile.gpu_names)
        if profile.gpu_names
        else "未检测到"
    )
    profile_lines: list[str] = []
    for key, value in {
        "系统": f"{_missing(profile.os_name)} {_missing(profile.os_version)}".strip(),
        "架构": _missing(profile.architecture),
        "CPU": _missing(profile.cpu_name),
        "CPU 核心数": _missing(profile.cpu_cores),
        "内存": _gb(profile.ram_gb),
        "检测到的 GPU": gpu_text,
        "主要性能判断 GPU": profile.primary_gpu.name if profile.primary_gpu else "未能可靠确认",
        "GPU 选择原因": profile.gpu_selection_reason or "未能可靠确认 GPU 选择原因",
        "兼容显存字段": _gb(profile.vram_gb),
        "磁盘总容量": _gb(profile.disk_total_gb),
        "磁盘剩余空间": _gb(profile.disk_free_gb),
        "Python": profile.python_version if profile.python_installed and profile.python_version else "未检测到",
        "Node.js": profile.node_version if profile.node_installed and profile.node_version else "未检测到",
        "Git": profile.git_version if profile.git_installed and profile.git_version else "未检测到",
        "pnpm": profile.pnpm_version if profile.pnpm_installed and profile.pnpm_version else "未检测到",
        "Docker": profile.docker_version if profile.docker_installed and profile.docker_version else "未检测到",
        "WSL": "已检测到" if profile.wsl_installed else "未检测到",
        "NVIDIA 驱动": profile.nvidia_driver_version or "未检测到",
    }.items():
        if "\n" in value:
            profile_lines.extend([f"- {key}：", value])
        else:
            profile_lines.append(f"- {key}：{value}")
    profile_lines.extend(_hardware_detail_lines(profile))
    profile_md = "\n".join(profile_lines)

    if profile.failed_checks:
        failed_md = "\n".join(
            [
                "| 检测项 | 状态 | 原因 | 影响 | 手动确认 |",
                "| -- | -- | -- | -- | -- |",
                *[
                    f"| {check.check_name} | {check.status} | {check.reason} | {check.impact} | {check.manual_check} |"
                    for check in profile.failed_checks
                ],
            ]
        )
    else:
        failed_md = "暂无检测失败项。"

    tier = recommendation.capability_tier
    tier_md = (
        "\n".join(
            [
                f"- 当前等级：{tier.tier}",
                "",
                "适合：",
                _list(tier.suitable, "暂无适合项。"),
                "",
                "不适合：",
                _list(tier.not_suitable, "暂无不适合项。"),
                "",
                "风险：",
                _list(tier.risks, "暂无额外风险。"),
            ]
        )
        if tier is not None
        else "该目标暂无能力分级。"
    )

    disk = recommendation.disk_risk_analysis
    disk_md = (
        "\n".join(
            [
                f"- 风险等级：{disk.risk_level}",
                f"- 扫描盘：{_missing(disk.system_drive)}",
                f"- 剩余空间：{_gb(disk.disk_free_gb)}",
                f"- 模型目录状态：{disk.model_directory_status}",
                f"- 缓存目录状态：{disk.cache_directory_status}",
                "",
                "原因：",
                _list(disk.reasons, "暂无额外原因。"),
                "",
                "建议：",
                _list(disk.recommendations, "暂无额外建议。"),
            ]
        )
        if disk is not None
        else "暂无磁盘风险分析。"
    )

    paths = recommendation.model_path_recommendation
    paths_md = (
        "\n".join(
            [
                "推荐模型目录：",
                _list(paths.recommended_model_paths, "暂无推荐模型目录。"),
                "",
                "推荐缓存目录：",
                _list(paths.recommended_cache_paths, "暂无推荐缓存目录。"),
                "",
                "避免作为默认目录：",
                _list(paths.avoid_paths, "暂无避免目录。"),
                "",
                "说明：",
                _list(paths.notes, "暂无说明。"),
            ]
        )
        if paths is not None
        else "暂无模型路径建议。"
    )

    score = recommendation.suitability_score
    if score >= 90:
        score_text = "非常适合。"
    elif score >= 75:
        score_text = "比较适合。"
    elif score >= 60:
        score_text = "可以尝试，但需要注意限制。"
    elif score >= 40:
        score_text = "不太推荐，可能体验一般。"
    else:
        score_text = "不推荐，建议更换目标或升级配置。"

    critical_count = sum(1 for finding in recommendation.findings if finding.level == "critical")
    warning_count = sum(1 for finding in recommendation.findings if finding.level == "warning")
    info_count = sum(1 for finding in recommendation.findings if finding.level == "info")
    score_reason = (
        "评分基于集中规则判断：严重问题每项扣 25 分，提醒项每项扣 10 分，信息项不扣分。"
        f"当前发现严重 {critical_count} 项、提醒 {warning_count} 项、信息 {info_count} 项。"
    )

    if recommendation.recommended_apps:
        app_rows = [
            "| 应用 | 必装/可选 | 推荐原因 | 安装方式 | 备注 |",
            "| -- | ----- | ---- | ---- | -- |",
        ]
        for item in recommendation.recommended_apps:
            notes = [*item.config_notes, *item.risk_notes]
            app_rows.append(
                f"| {item.name} | {'必装' if item.required else '可选'} | {item.reason} | {item.install_method} | {'<br>'.join(notes) if notes else '无'} |"
            )
        apps_md = "\n".join(app_rows)
    else:
        apps_md = "暂无推荐应用。"

    if recommendation.findings:
        level_names = {"critical": "严重", "warning": "提醒", "info": "信息"}
        finding_rows = [
            "| 等级 | 标题 | 说明 | 依据 |",
            "| -- | -- | -- | -- |",
        ]
        for finding in recommendation.findings:
            evidence = "；".join(f"{key}={_missing(value)}" for key, value in finding.evidence.items()) if finding.evidence else "无"
            finding_rows.append(
                f"| {level_names[finding.level]} | {finding.title} | {finding.message} | {evidence} |"
            )
        findings_md = "\n".join(finding_rows)
    else:
        findings_md = "暂无明显风险提示。"

    return f"""# StackPilot 应用推荐报告

## 电脑配置摘要

{profile_md}

## 检测失败项

{failed_md}

## 能力分级

{tier_md}

## 磁盘风险分析

{disk_md}

## 模型路径建议

{paths_md}

## 使用目标

目标：{recommendation.display_name}
模板 ID：{recommendation.template_id}
适合人群：{template_audience(recommendation.template_id)}

## 适配度评分

适配度评分：{score:g} / 100

{score_text}

{score_reason}

## 推荐应用

{apps_md}

## 规则判断与风险提示

{findings_md}

## 配置建议

{_list(recommendation.config_recommendations, "暂无额外配置建议。")}

## 当前不推荐事项

{_list(recommendation.not_recommended, "暂无明显不推荐事项。")}

## 下一步建议

{_list(recommendation.next_steps, "暂无下一步建议。")}

## 说明

{TRANSPARENCY_NOTICE}
请优先从软件官方渠道下载安装应用。
"""


def render_json_payload(report_data: ReportData) -> dict:
    """Render a structured JSON-compatible report payload."""

    recommendation = report_data.recommendation
    profile = report_data.hardware_profile
    return {
        "generated_at": report_data.generated_at,
        "hardware_profile": model_to_dict(profile),
        "goal": {
            "id": recommendation.goal_id,
            "name": recommendation.goal_name,
            "category": recommendation.category,
            "summary": recommendation.summary,
        },
        "suitability_score": recommendation.suitability_score,
        "required_apps": [model_to_dict(app) for app in recommendation.required_apps],
        "optional_apps": [model_to_dict(app) for app in recommendation.optional_apps],
        "findings": [model_to_dict(finding) for finding in recommendation.findings],
        "failed_checks": [model_to_dict(check) for check in profile.failed_checks],
        "warnings": recommendation.warnings,
        "not_recommended": recommendation.not_recommended,
        "next_steps": recommendation.next_steps,
        "transparency_notice": {
            "en": TRANSPARENCY_NOTICE,
            "zh": TRANSPARENCY_NOTICE,
        },
        "profile": model_to_dict(profile),
        "recommendation": model_to_dict(recommendation),
    }


def generate_report(
    goal: str,
    output_dir: str | Path | None = None,
    profile: HardwareProfile | None = None,
) -> tuple[Path, Path, RecommendationResult]:
    """Generate Markdown and JSON reports for a selected goal."""

    profile = profile or scan_system()
    recommendation = recommend(goal, profile=profile)
    target_dir = Path(output_dir) if output_dir is not None else default_output_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    md_path = target_dir / REPORT_MD
    json_path = target_dir / REPORT_JSON
    report_data = ReportData(
        hardware_profile=profile,
        recommendation=recommendation,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    md_path.write_text(render_markdown(report_data), encoding="utf-8")
    json_path.write_text(
        json.dumps(render_json_payload(report_data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return md_path, json_path, recommendation
