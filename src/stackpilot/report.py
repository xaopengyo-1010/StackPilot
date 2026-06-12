from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import AppRecommendation, HardwareProfile, RecommendationResult, ReportData, RuleFinding
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
    """Return the default directory used for generated reports."""

    return project_root() / "outputs" / "reports"


def _missing(value: object | None) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, str) and not value.strip():
        return "未检测到"
    return str(value)


def _format_gb(value: float | None) -> str:
    if value is None:
        return "未检测到"
    return f"{value:g} GB"


def _format_score(score: float) -> str:
    return f"{score:g}"


def _score_explanation(score: float) -> str:
    if score >= 90:
        return "非常适合。"
    if score >= 75:
        return "比较适合。"
    if score >= 60:
        return "可以尝试，但需要注意限制。"
    if score >= 40:
        return "不太推荐，可能体验一般。"
    return "不推荐，建议更换目标或升级配置。"


def _format_list(values: list[str], empty_text: str) -> str:
    if not values:
        return empty_text
    return "\n".join(f"- {value}" for value in values)


def _format_profile(profile: HardwareProfile) -> str:
    gpu_list = _format_gpu_list(profile)
    rows = {
        "系统": f"{_missing(profile.os_name)} {_missing(profile.os_version)}".strip(),
        "架构": _missing(profile.architecture),
        "CPU": _missing(profile.cpu_name),
        "CPU 核心数": _missing(profile.cpu_cores),
        "内存": _format_gb(profile.ram_gb),
        "检测到的 GPU": gpu_list,
        "主要性能判断 GPU": profile.primary_gpu.name if profile.primary_gpu else "未能可靠确认",
        "GPU 选择原因": profile.gpu_selection_reason or "未能可靠确认 GPU 选择原因",
        "兼容显存字段": _format_gb(profile.vram_gb),
        "磁盘总容量": _format_gb(profile.disk_total_gb),
        "磁盘剩余空间": _format_gb(profile.disk_free_gb),
        "Python": profile.python_version if profile.python_installed and profile.python_version else "未检测到",
        "Node.js": profile.node_version if profile.node_installed and profile.node_version else "未检测到",
        "Git": profile.git_version if profile.git_installed and profile.git_version else "未检测到",
        "pnpm": profile.pnpm_version if profile.pnpm_installed and profile.pnpm_version else "未检测到",
        "Docker": profile.docker_version if profile.docker_installed and profile.docker_version else "未检测到",
        "WSL": "已检测到" if profile.wsl_installed else "未检测到",
        "NVIDIA 驱动": profile.nvidia_driver_version or "未检测到",
    }
    lines: list[str] = []
    for key, value in rows.items():
        if "\n" in value:
            lines.append(f"- {key}：")
            lines.append(value)
        else:
            lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def _format_gpu_list(profile: HardwareProfile) -> str:
    if profile.gpus:
        return "\n".join(f"  - {gpu.markdown_summary()}" for gpu in profile.gpus)
    if profile.gpu_names:
        return "、".join(profile.gpu_names)
    return "未检测到"


def _format_apps(apps: list[AppRecommendation]) -> str:
    if not apps:
        return "暂无推荐应用。"

    lines = [
        "| 应用 | 必装/可选 | 推荐原因 | 安装方式 | 备注 |",
        "| -- | ----- | ---- | ---- | -- |",
    ]
    for app in apps:
        required = "必装" if app.required else "可选"
        notes = [*app.config_notes, *app.risk_notes]
        note_text = "<br>".join(notes) if notes else "无"
        lines.append(
            f"| {app.name} | {required} | {app.reason} | {app.install_method} | {note_text} |"
        )
    return "\n".join(lines)


def _format_evidence(evidence: dict[str, object | None]) -> str:
    if not evidence:
        return "无"
    parts = []
    for key, value in evidence.items():
        parts.append(f"{key}={_missing(value)}")
    return "；".join(parts)


def _format_findings(findings: list[RuleFinding]) -> str:
    if not findings:
        return "暂无明显风险提示。"

    level_names = {
        "critical": "严重",
        "warning": "提醒",
        "info": "信息",
    }
    lines = [
        "| 等级 | 标题 | 说明 | 依据 |",
        "| -- | -- | -- | -- |",
    ]
    for finding in findings:
        lines.append(
            f"| {level_names[finding.level]} | {finding.title} | {finding.message} | {_format_evidence(finding.evidence)} |"
        )
    return "\n".join(lines)


def _score_reason(recommendation: RecommendationResult) -> str:
    critical_count = sum(1 for finding in recommendation.findings if finding.level == "critical")
    warning_count = sum(1 for finding in recommendation.findings if finding.level == "warning")
    info_count = sum(1 for finding in recommendation.findings if finding.level == "info")
    return (
        "评分基于集中规则判断：严重问题每项扣 25 分，提醒项每项扣 10 分，信息项不扣分。"
        f"当前发现严重 {critical_count} 项、提醒 {warning_count} 项、信息 {info_count} 项。"
    )


def render_markdown(report_data: ReportData) -> str:
    """Render a Chinese Markdown report from structured report data."""

    profile = report_data.hardware_profile
    recommendation = report_data.recommendation
    score = _format_score(recommendation.suitability_score)
    return f"""# StackPilot 应用推荐报告

## 电脑配置摘要

{_format_profile(profile)}

## 使用目标

目标：{recommendation.display_name}
模板 ID：{recommendation.template_id}
适合人群：{template_audience(recommendation.template_id)}

## 适配度评分

适配度评分：{score} / 100

{_score_explanation(recommendation.suitability_score)}

{_score_reason(recommendation)}

## 推荐应用

{_format_apps(recommendation.recommended_apps)}

## 规则判断与风险提示

{_format_findings(recommendation.findings)}

## 配置建议

{_format_list(recommendation.config_recommendations, "暂无额外配置建议。")}

## 当前不推荐事项

{_format_list(recommendation.not_recommended, "暂无明显不推荐事项。")}

## 下一步建议

{_format_list(recommendation.next_steps, "暂无下一步建议。")}

## 说明

{TRANSPARENCY_NOTICE}
请优先从软件官方渠道下载安装应用。
"""


def _apps_to_dict(apps: list[AppRecommendation]) -> list[dict]:
    return [model_to_dict(app) for app in apps]


def render_json_payload(report_data: ReportData) -> dict:
    """Render a structured JSON-compatible report payload."""

    recommendation = report_data.recommendation
    profile = report_data.hardware_profile
    payload = {
        "generated_at": report_data.generated_at,
        "hardware_profile": model_to_dict(profile),
        "goal": {
            "id": recommendation.goal_id,
            "name": recommendation.goal_name,
            "category": recommendation.category,
            "summary": recommendation.summary,
        },
        "suitability_score": recommendation.suitability_score,
        "required_apps": _apps_to_dict(recommendation.required_apps),
        "optional_apps": _apps_to_dict(recommendation.optional_apps),
        "findings": [model_to_dict(finding) for finding in recommendation.findings],
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
    return payload


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
    generated_at = datetime.now(timezone.utc).isoformat()
    report_data = ReportData(
        hardware_profile=profile,
        recommendation=recommendation,
        generated_at=generated_at,
    )

    md_path.write_text(render_markdown(report_data), encoding="utf-8")
    json_path.write_text(
        json.dumps(render_json_payload(report_data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return md_path, json_path, recommendation
