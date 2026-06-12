from __future__ import annotations

from collections.abc import Iterable

from stackpilot import detector
from stackpilot.hardware.gpu_classifier import classify_gpu_type, classify_gpu_vendor, classify_vram_confidence
from stackpilot.hardware.gpu_selector import select_primary_gpu
from stackpilot.hardware.vram import estimate_dedicated_vram_from_name
from stackpilot.models import GpuDevice, HardwareProfile, RuleFinding, TemplateDefinition


CODING_GOALS = {"coding_starter", "vibe_coding"}
PYTHON_GOALS = {"coding_starter", "comfyui_starter", "ai_beginner"}
LOCAL_AI_GOALS = {"comfyui_starter", "local_llm"}
GPU_SENSITIVE_GOALS = {"comfyui_starter", "local_llm", "gaming_setup", "creator_setup"}


def _legacy_gpus(profile: HardwareProfile) -> list[GpuDevice]:
    devices: list[GpuDevice] = []
    for name in profile.gpu_names:
        vendor = classify_gpu_vendor(name)
        gpu_type = classify_gpu_type(name, vendor)
        estimated_vram = estimate_dedicated_vram_from_name(name) if gpu_type == "dedicated" else None
        adapter_vram = profile.vram_gb if gpu_type == "dedicated" else None
        confidence = classify_vram_confidence(
            name=name,
            gpu_type=gpu_type,
            adapter_ram_gb=adapter_vram,
            estimated_vram_gb=estimated_vram,
        )
        devices.append(
            GpuDevice(
                name=name,
                vendor=vendor,
                gpu_type=gpu_type,
                dedicated_vram_gb=(adapter_vram or estimated_vram) if confidence in {"detected", "estimated"} else None,
                vram_confidence=confidence,
                source="unknown",
            )
        )
    return devices


def _profile_gpus(profile: HardwareProfile) -> list[GpuDevice]:
    return profile.gpus or _legacy_gpus(profile)


def _primary_gpu(profile: HardwareProfile) -> tuple[GpuDevice | None, str | None]:
    if profile.primary_gpu is not None:
        return profile.primary_gpu, profile.gpu_selection_reason
    gpus = _profile_gpus(profile)
    if not gpus:
        return None, None
    return select_primary_gpu(gpus)


def _effective_vram(profile: HardwareProfile) -> tuple[float | None, bool]:
    primary_gpu, _ = _primary_gpu(profile)
    if primary_gpu is not None and primary_gpu.gpu_type == "dedicated":
        if primary_gpu.dedicated_vram_gb is not None:
            return primary_gpu.dedicated_vram_gb, primary_gpu.vram_confidence == "estimated"
    if profile.gpus or profile.primary_gpu is not None:
        return None, False
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
    gpus = _profile_gpus(profile)
    primary_gpu, gpu_selection_reason = _primary_gpu(profile)

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

    if goal_id == "comfyui_starter":
        if primary_gpu is None:
            level = "warning"
            title = "GPU 性能无法确认"
            message = "未能可靠确认真实 GPU 信息，AI 绘图性能需要用户补充确认。"
            if gpus:
                title = "仅检测到虚拟/基础显示设备"
                message = "仅检测到虚拟或基础显示设备，无法可靠评估本地 AI 绘图性能。"
            _append_unique(
                findings,
                _finding(
                    id="comfyui_gpu_unreliable",
                    level=level,
                    title=title,
                    message=message,
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"gpu_selection_reason": gpu_selection_reason},
                ),
            )
        elif primary_gpu.gpu_type == "integrated":
            _append_unique(
                findings,
                _finding(
                    id="comfyui_integrated_gpu",
                    level="warning",
                    title="当前主要 GPU 是核显",
                    message="当前主要性能判断基于集成显卡和共享内存，不推荐用于较重的本地 AI 绘图工作流。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={
                        "primary_gpu": primary_gpu.name,
                        "gpu_type": primary_gpu.gpu_type,
                        "vram_confidence": primary_gpu.vram_confidence,
                    },
                ),
            )
        elif primary_gpu.gpu_type == "unknown":
            _append_unique(
                findings,
                _finding(
                    id="comfyui_gpu_unknown",
                    level="warning",
                    title="GPU 类型未知",
                    message="当前 GPU 类型无法确认，ComfyUI 适配性需要用户补充设备信息后再判断。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"primary_gpu": primary_gpu.name, "gpu_type": primary_gpu.gpu_type},
                ),
            )
        elif (
            primary_gpu.vendor == "NVIDIA"
            and primary_gpu.gpu_type == "dedicated"
            and primary_gpu.dedicated_vram_gb is not None
            and primary_gpu.vram_confidence == "detected"
        ):
            if primary_gpu.dedicated_vram_gb >= 12:
                title = "NVIDIA 独显适合 AI 绘图"
                message = "检测到 NVIDIA 独立显卡且独立显存不少于 12GB，适合从 ComfyUI 入门并尝试较复杂工作流。"
            elif primary_gpu.dedicated_vram_gb >= 8:
                title = "NVIDIA 独显可用于 AI 绘图"
                message = "检测到 NVIDIA 独立显卡且独立显存不少于 8GB，适合从 ComfyUI 入门。"
            elif primary_gpu.dedicated_vram_gb >= 6:
                title = "NVIDIA 独显显存偏紧"
                message = "检测到 NVIDIA 独立显卡，但显存约 6GB，建议只尝试轻量 ComfyUI 工作流。"
            else:
                title = "NVIDIA 独显显存不足"
                message = "检测到 NVIDIA 独立显卡，但独立显存低于 6GB，不适合较重 ComfyUI 工作流。"
            _append_unique(
                findings,
                _finding(
                    id="comfyui_nvidia_dedicated_vram",
                    level="info" if primary_gpu.dedicated_vram_gb >= 8 else "warning",
                    title=title,
                    message=message,
                    goal_id=goal_id,
                    component="gpu",
                    evidence={
                        "primary_gpu": primary_gpu.name,
                        "dedicated_vram_gb": primary_gpu.dedicated_vram_gb,
                        "vram_confidence": primary_gpu.vram_confidence,
                    },
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

    if goal_id == "local_llm" and primary_gpu is not None:
        if primary_gpu.gpu_type == "integrated":
            _append_unique(
                findings,
                _finding(
                    id="local_llm_integrated_gpu",
                    level="info",
                    title="本地大模型不应主要依赖核显",
                    message="当前主要 GPU 是集成显卡，本地大模型建议优先按内存和 CPU 路径规划，不要把 GPU 加速作为主要路径。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"primary_gpu": primary_gpu.name, "gpu_type": primary_gpu.gpu_type},
                ),
            )
        elif primary_gpu.vendor == "NVIDIA" and primary_gpu.gpu_type == "dedicated":
            _append_unique(
                findings,
                _finding(
                    id="local_llm_nvidia_gpu_available",
                    level="info",
                    title="检测到 NVIDIA 独显",
                    message="检测到 NVIDIA 独立显卡，未来可考虑 GPU 加速，但仍取决于独立显存容量和模型大小。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={
                        "primary_gpu": primary_gpu.name,
                        "dedicated_vram_gb": primary_gpu.dedicated_vram_gb,
                        "vram_confidence": primary_gpu.vram_confidence,
                    },
                ),
            )
        elif primary_gpu.gpu_type == "unknown":
            _append_unique(
                findings,
                _finding(
                    id="local_llm_gpu_unknown",
                    level="warning",
                    title="GPU 类型未知",
                    message="当前 GPU 类型无法确认，本地大模型推荐不会假设可用 GPU 加速。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"primary_gpu": primary_gpu.name},
                ),
            )

    if goal_id == "gaming_setup":
        if primary_gpu is None:
            _append_unique(
                findings,
                _finding(
                    id="gaming_gpu_unreliable",
                    level="warning",
                    title="图形性能无法确认",
                    message="未能可靠确认真实 GPU，游戏性能和画质建议需要保守判断。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"gpu_selection_reason": gpu_selection_reason},
                ),
            )
        elif primary_gpu.gpu_type == "integrated":
            _append_unique(
                findings,
                _finding(
                    id="gaming_integrated_gpu",
                    level="info",
                    title="当前主要 GPU 是核显",
                    message="当前主要 GPU 是集成显卡，更适合轻量游戏、云游戏或低画质设置。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"primary_gpu": primary_gpu.name, "gpu_type": primary_gpu.gpu_type},
                ),
            )
        elif primary_gpu.gpu_type == "dedicated":
            _append_unique(
                findings,
                _finding(
                    id="gaming_dedicated_gpu",
                    level="info",
                    title="检测到独立显卡",
                    message="检测到独立显卡，可以安装游戏平台和性能监控工具，但具体画质仍取决于显卡型号和显存。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={
                        "primary_gpu": primary_gpu.name,
                        "dedicated_vram_gb": primary_gpu.dedicated_vram_gb,
                        "vram_confidence": primary_gpu.vram_confidence,
                    },
                ),
            )
        elif primary_gpu.gpu_type == "unknown":
            _append_unique(
                findings,
                _finding(
                    id="gaming_gpu_unknown",
                    level="warning",
                    title="GPU 类型未知",
                    message="当前 GPU 类型无法确认，游戏性能建议需要用户补充设备信息。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"primary_gpu": primary_gpu.name},
                ),
            )

    if goal_id in GPU_SENSITIVE_GOALS and not gpus:
        _append_unique(
            findings,
            _finding(
                id="gpu_missing",
                level="warning",
                title="未检测到 GPU 信息",
                message="未检测到 GPU 信息，游戏光影和本地 AI 生成体验需要保守判断。",
                goal_id=goal_id,
                component="gpu",
                evidence={"gpu_names": profile.gpu_names},
            ),
        )

    if goal_id in LOCAL_AI_GOALS and gpus and vram_gb is None and (
        primary_gpu is None or primary_gpu.gpu_type in {"dedicated", "unknown"}
    ):
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
