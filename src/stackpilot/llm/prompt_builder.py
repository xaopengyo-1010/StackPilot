from __future__ import annotations

from stackpilot.models import HardwareProfile, RecommendationResult, TemplateDefinition


def _value(value: object | None) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, str) and not value.strip():
        return "未检测到"
    return str(value)


def _gb(value: float | None) -> str:
    if value is None:
        return "未检测到"
    return f"{value:g} GB"


def build_report_prompt(
    hardware_profile: HardwareProfile,
    goal: str,
    template: TemplateDefinition,
    recommendation_result: RecommendationResult,
) -> str:
    """Build a Chinese prompt for a future LLM report writer.

    This function does not call any LLM API. It only turns structured facts,
    rule findings, and recommendations into a constrained prompt that can be
    reviewed and tested locally.
    """

    facts = [
        f"- 系统：{_value(hardware_profile.os_name)} {_value(hardware_profile.os_version)}",
        f"- CPU：{_value(hardware_profile.cpu_name)}",
        f"- CPU 核心数：{_value(hardware_profile.cpu_cores)}",
        f"- 内存：{_gb(hardware_profile.ram_gb)}",
        f"- 显卡：{_value('、'.join(hardware_profile.gpu_names) if hardware_profile.gpu_names else None)}",
        f"- 显存：{_gb(hardware_profile.vram_gb)}",
        f"- 磁盘剩余空间：{_gb(hardware_profile.disk_free_gb)}",
        f"- Python：{_value(hardware_profile.python_version if hardware_profile.python_installed else None)}",
        f"- Git：{_value(hardware_profile.git_version if hardware_profile.git_installed else None)}",
        f"- Docker：{_value(hardware_profile.docker_version if hardware_profile.docker_installed else None)}",
        f"- WSL：{'已检测到' if hardware_profile.wsl_installed else '未检测到'}",
    ]
    findings = [
        f"- {finding.level} / {finding.title}：{finding.message}"
        for finding in recommendation_result.findings
    ] or ["- 暂无明显规则风险。"]
    apps = [
        f"- {app.name}（{'必装' if app.required else '可选'}）：{app.reason}"
        for app in recommendation_result.recommended_apps
    ]

    return "\n".join(
        [
            "你是 StackPilot 的中文报告撰写助手。",
            "",
            "请基于已提供事实、规则判断和推荐结果，写出面向电脑小白的简洁中文建议。",
            "",
            "硬性约束：",
            "1. 只基于已提供事实，不编造未检测到的信息。",
            "2. 不覆盖 critical / warning 规则，不淡化风险。",
            "3. 不建议自动安装软件，不生成自动安装脚本。",
            "4. 不建议修改系统危险设置，不承诺性能提升。",
            "5. 如果信息缺失，请写“未检测到”或“需要用户确认”。",
            "6. 输出必须区分“事实”“判断”“建议”。",
            "",
            f"目标 ID：{goal}",
            f"目标名称：{template.display_name}",
            f"模板说明：{template.description}",
            f"适配度评分：{recommendation_result.suitability_score:g} / 100",
            "",
            "硬件事实：",
            *facts,
            "",
            "规则判断：",
            *findings,
            "",
            "推荐应用：",
            *apps,
            "",
            "下一步建议：",
            *[f"- {step}" for step in recommendation_result.next_steps],
        ]
    )
