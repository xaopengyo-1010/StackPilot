from __future__ import annotations

from collections.abc import Iterable

from stackpilot import detector
from stackpilot.models import HardwareProfile, RuleFinding, TemplateDefinition


CODING_GOALS = {"coding_starter", "vibe_coding"}
PYTHON_GOALS = {"coding_starter", "comfyui_starter", "ai_beginner"}
LOCAL_AI_GOALS = {"comfyui_starter", "local_llm"}
GPU_SENSITIVE_GOALS = {"comfyui_starter", "local_llm", "gaming_setup", "creator_setup"}


def _effective_vram(profile: HardwareProfile) -> tuple[float | None, bool]:
    if profile.vram_gb is not None:
        return profile.vram_gb, False
    if profile.gpu_vram_gb is not None:
        return profile.gpu_vram_gb, False
    inferred = detector.infer_vram_from_names(profile.gpu_names)
    return inferred, inferred is not None


def _append_unique(findings: list[RuleFinding], finding: RuleFinding) -> None:
    if any(existing.id == finding.id for existing in findings):
        return
    findings.append(finding)


def _finding(
    *,
    id: str,
    level: str,
    title: str,
    message: str,
    goal_id: str,
    component: str,
    evidence: dict[str, object | None],
) -> RuleFinding:
    return RuleFinding(
        id=id,
        level=level,  # type: ignore[arg-type]
        title=title,
        message=message,
        related_goal=goal_id,
        related_component=component,
        evidence=evidence,
    )


def evaluate_rules(profile: HardwareProfile, template: TemplateDefinition) -> list[RuleFinding]:
    """Evaluate centralized hardware and environment rules for a goal template.

    The current implementation uses Python rule functions to keep the engine
    simple. Rule definitions are intentionally isolated here so they can be
    migrated to JSON-backed rules later without touching CLI, scanner, or
    report renderers.
    """

    goal_id = template.template_id
    findings: list[RuleFinding] = []
    ram_gb = profile.ram_gb
    vram_gb, vram_inferred = _effective_vram(profile)
    disk_free_gb = profile.disk_free_gb

    for index, warning in enumerate(profile.warnings):
        _append_unique(
            findings,
            _finding(
                id=f"scanner_warning_{index}",
                level="warning",
                title="检测提示",
                message=warning,
                goal_id=goal_id,
                component="scanner",
                evidence={"warning": warning},
            ),
        )

    for index, warning in enumerate(template.risk_warnings):
        _append_unique(
            findings,
            _finding(
                id=f"template_risk_{goal_id}_{index}",
                level="warning",
                title="模板风险提示",
                message=warning,
                goal_id=goal_id,
                component="template",
                evidence={"template_id": goal_id},
            ),
        )

    if goal_id == "comfyui_starter" and vram_gb is not None and vram_gb < 6:
        _append_unique(
            findings,
            _finding(
                id="comfyui_vram_low",
                level="warning",
                title="显存偏低",
                message="当前显存低于 6GB，可以尝试 ComfyUI，但不适合高分辨率出图或大型模型。",
                goal_id=goal_id,
                component="vram",
                evidence={"vram_gb": vram_gb, "threshold_gb": 6},
            ),
        )

    if goal_id == "local_llm" and ram_gb is not None and ram_gb < 16:
        _append_unique(
            findings,
            _finding(
                id="local_llm_ram_low",
                level="warning",
                title="内存偏低",
                message="当前内存低于 16GB，不建议运行较大的本地大模型。",
                goal_id=goal_id,
                component="ram",
                evidence={"ram_gb": ram_gb, "threshold_gb": 16},
            ),
        )

    if disk_free_gb is not None and disk_free_gb < 30:
        _append_unique(
            findings,
            _finding(
                id="disk_free_low",
                level="critical",
                title="磁盘空间不足",
                message="当前剩余磁盘空间低于 30GB，建议先清理空间后再搭建环境。",
                goal_id=goal_id,
                component="disk",
                evidence={"disk_free_gb": disk_free_gb, "threshold_gb": 30},
            ),
        )

    if goal_id in CODING_GOALS and not profile.docker_installed:
        _append_unique(
            findings,
            _finding(
                id="docker_missing",
                level="info",
                title="Docker 未检测到",
                message="Docker 不是必装项，但对于后端开发、容器化部署和部分开发环境会有帮助。",
                goal_id=goal_id,
                component="docker",
                evidence={"docker_installed": profile.docker_installed},
            ),
        )

    if goal_id in CODING_GOALS and not profile.git_installed:
        _append_unique(
            findings,
            _finding(
                id="git_missing",
                level="warning",
                title="Git 未检测到",
                message="Git 是大多数编程和 AI 辅助编程工作流的基础工具，建议优先安装。",
                goal_id=goal_id,
                component="git",
                evidence={"git_installed": profile.git_installed},
            ),
        )

    if goal_id in PYTHON_GOALS and not profile.python_installed:
        _append_unique(
            findings,
            _finding(
                id="python_missing",
                level="warning",
                title="Python 未检测到",
                message="当前未检测到 Python。对于编程入门、ComfyUI 和部分 AI 工具，Python 通常是基础依赖。",
                goal_id=goal_id,
                component="python",
                evidence={"python_installed": profile.python_installed},
            ),
        )

    if goal_id in GPU_SENSITIVE_GOALS and not profile.gpu_names:
        _append_unique(
            findings,
            _finding(
                id="gpu_missing",
                level="warning",
                title="未检测到独立显卡",
                message="未检测到独立显卡，游戏光影和本地 AI 生成体验可能受限。",
                goal_id=goal_id,
                component="gpu",
                evidence={"gpu_names": profile.gpu_names},
            ),
        )

    if goal_id in LOCAL_AI_GOALS and profile.gpu_names and vram_gb is None:
        _append_unique(
            findings,
            _finding(
                id="vram_unknown",
                level="warning",
                title="显存信息未知",
                message="未检测到显存信息，AI 绘图和本地大模型推荐可能不够准确。",
                goal_id=goal_id,
                component="vram",
                evidence={"gpu_names": profile.gpu_names, "vram_gb": None},
            ),
        )

    if goal_id in LOCAL_AI_GOALS and vram_inferred:
        _append_unique(
            findings,
            _finding(
                id="vram_inferred",
                level="info",
                title="显存为估算值",
                message="未直接检测到显存信息，StackPilot 只能根据显卡名称做粗略估算。",
                goal_id=goal_id,
                component="vram",
                evidence={"gpu_names": profile.gpu_names, "estimated_vram_gb": vram_gb},
            ),
        )

    if any("nvidia" in name.casefold() for name in profile.gpu_names) and not profile.nvidia_driver_version:
        _append_unique(
            findings,
            _finding(
                id="nvidia_driver_unknown",
                level="warning",
                title="NVIDIA 驱动未确认",
                message="检测到 NVIDIA 显卡，建议确认驱动版本是否正常。",
                goal_id=goal_id,
                component="gpu",
                evidence={"gpu_names": profile.gpu_names, "nvidia_driver_version": None},
            ),
        )

    return findings


def findings_to_warnings(findings: Iterable[RuleFinding]) -> list[str]:
    """Return user-facing risk messages from warning and critical findings."""

    return [
        finding.message
        for finding in findings
        if finding.level in {"warning", "critical"}
    ]


def findings_to_not_recommended(findings: Iterable[RuleFinding]) -> list[str]:
    """Translate critical findings into explicit not-recommended actions."""

    actions: list[str] = []
    for finding in findings:
        if finding.id == "disk_free_low":
            actions.append("在释放磁盘空间前开始配置这个工作流。")
        elif finding.id == "comfyui_vram_low":
            actions.append("使用高分辨率 ComfyUI 出图、大批量生成或大型模型。")
        elif finding.id == "local_llm_ram_low":
            actions.append("在低于 16GB 内存的电脑上运行较大的本地大模型或长上下文。")
        elif finding.id == "git_missing":
            actions.append("在没有 Git 的情况下开始需要版本管理的编程工作流。")
        elif finding.id == "python_missing":
            actions.append("在未准备 Python 的情况下直接配置依赖 Python 的开发或 AI 工具。")
    return actions
