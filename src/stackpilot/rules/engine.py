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
GIT_GOALS = CODING_GOALS | LOCAL_AI_GOALS
DOCKER_GOALS = CODING_GOALS | {"local_llm"}
WSL_GOALS = CODING_GOALS | LOCAL_AI_GOALS
FAILED_CHECK_CRITICAL = {"disk"}


def _profile_gpus(profile: HardwareProfile) -> list[GpuDevice]:
    if profile.gpus:
        return profile.gpus

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


def _primary_gpu(profile: HardwareProfile) -> tuple[GpuDevice | None, str | None]:
    if profile.primary_gpu is not None:
        return profile.primary_gpu, profile.gpu_selection_reason
    gpus = _profile_gpus(profile)
    if not gpus:
        return None, None
    return select_primary_gpu(gpus)


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
    disk_free_gb = profile.disk_free_gb
    gpus = _profile_gpus(profile)
    primary_gpu, gpu_selection_reason = _primary_gpu(profile)
    if primary_gpu is not None and primary_gpu.gpu_type == "dedicated" and primary_gpu.dedicated_vram_gb is not None:
        vram_gb = primary_gpu.dedicated_vram_gb
        vram_inferred = primary_gpu.vram_confidence == "estimated"
    elif profile.gpus or profile.primary_gpu is not None:
        vram_gb = None
        vram_inferred = False
    elif profile.vram_gb is not None:
        vram_gb = profile.vram_gb
        vram_inferred = False
    elif profile.gpu_vram_gb is not None:
        vram_gb = profile.gpu_vram_gb
        vram_inferred = False
    else:
        vram_gb = detector.infer_vram_from_names(profile.gpu_names)
        vram_inferred = vram_gb is not None
    is_windows = (
        profile.platform_profile.os_family == "windows"
        if profile.platform_profile is not None
        else "windows" in (profile.os_name or "").casefold()
    )

    for failed_check in profile.failed_checks:
        level = "critical" if failed_check.check_name in FAILED_CHECK_CRITICAL else "warning"
        _append_unique(
            findings,
            _finding(
                id=f"failed_check_{failed_check.check_name}",
                level=level,
                title=f"{failed_check.check_name} 检测失败",
                message=(
                    f"{failed_check.reason} 影响：{failed_check.impact} "
                    f"手动确认：{failed_check.manual_check}"
                ),
                goal_id=goal_id,
                component=failed_check.check_name,
                evidence={
                    "check_name": failed_check.check_name,
                    "status": failed_check.status,
                    "manual_check": failed_check.manual_check,
                },
            ),
        )

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

    if goal_id in LOCAL_AI_GOALS and profile.disk_anchor and profile.disk_anchor.casefold().startswith("c:"):
        level = "warning" if disk_free_gb is None or disk_free_gb < 100 else "info"
        _append_unique(
            findings,
            _finding(
                id="system_drive_ai_storage_risk",
                level=level,
                title="C 盘空间风险",
                message=(
                    "当前扫描目录位于 C 盘。本地 AI 的模型、缓存、虚拟环境和输出文件很容易占用数十 GB，"
                    "建议把模型目录和缓存目录放到非系统盘，并保留足够可回收空间。"
                ),
                goal_id=goal_id,
                component="disk",
                evidence={"disk_anchor": profile.disk_anchor, "disk_free_gb": disk_free_gb},
            ),
        )

    if goal_id in LOCAL_AI_GOALS:
        _append_unique(
            findings,
            _finding(
                id="model_directory_risk",
                level="warning",
                title="模型目录风险",
                message=(
                    "ComfyUI、Ollama 或 LM Studio 的模型目录可能快速增长；不要把大型模型默认堆在 C 盘或项目目录里，"
                    "先指定一个空间充足、路径清楚、便于备份的目录。"
                ),
                goal_id=goal_id,
                component="storage",
                evidence={"goal_id": goal_id},
            ),
        )
        _append_unique(
            findings,
            _finding(
                id="cache_directory_risk",
                level="warning",
                title="缓存目录风险",
                message=(
                    "pip、Hugging Face、ComfyUI custom nodes 和图像输出会写入缓存；安装前先确认缓存位置，"
                    "避免用户目录或 C 盘被临时文件占满。"
                ),
                goal_id=goal_id,
                component="storage",
                evidence={"goal_id": goal_id},
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

    if goal_id in GPU_SENSITIVE_GOALS and primary_gpu is not None and primary_gpu.vram_confidence == "shared":
        _append_unique(
            findings,
            _finding(
                id="shared_vram_risk",
                level="warning",
                title="共享显存风险",
                message=(
                    f"{primary_gpu.name} 使用共享内存，不等于独立显存；本地 AI、游戏和 4K 创作建议按低配处理，"
                    "不要把共享内存当作可稳定使用的 GPU 显存。"
                ),
                goal_id=goal_id,
                component="vram",
                evidence={
                    "primary_gpu": primary_gpu.name,
                    "gpu_type": primary_gpu.gpu_type,
                    "vram_confidence": primary_gpu.vram_confidence,
                },
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
                    message=(
                        f"当前主要 GPU 是 {primary_gpu.name}。适合：轻量 ComfyUI、低分辨率测试和少量节点学习；"
                        "不适合：Flux、SDXL 高分辨率、批量生成或复杂工作流；风险：共享显存和系统内存互相争用；"
                        "建议：模型、输出和缓存放到非 C 盘，并从轻量模型开始。"
                    ),
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

    if goal_id in DOCKER_GOALS and not profile.docker_installed:
        _append_unique(
            findings,
            _finding(
                id="docker_missing",
                level="info",
                title="Docker 未检测到",
                message=(
                    "未检测到 Docker。后端开发、数据库沙盒、Open WebUI 或部分本地服务会受影响；"
                    "如果暂时不用容器，可以跳过，但不要把依赖 Docker 的步骤当作已可执行。手动确认：docker --version。"
                ),
                goal_id=goal_id,
                component="docker",
                evidence={"docker_installed": profile.docker_installed},
            ),
        )

    if goal_id in GIT_GOALS and not profile.git_installed:
        _append_unique(
            findings,
            _finding(
                id="git_missing",
                level="warning",
                title="Git 未检测到",
                message=(
                    "未检测到 Git。开源项目获取、版本回滚、ComfyUI custom nodes 和代码工作流都会受影响；"
                    "先运行 git --version 确认，再决定是否安装。"
                ),
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
                message=(
                    "当前未检测到 Python。编程入门、ComfyUI 和部分 AI 工具通常需要 Python；"
                    "先运行 python --version 或 py --version 确认，避免直接配置依赖后才发现命令不可用。"
                ),
                goal_id=goal_id,
                component="python",
                evidence={"python_installed": profile.python_installed},
            ),
        )

    if goal_id in WSL_GOALS and is_windows and not profile.wsl_installed:
        _append_unique(
            findings,
            _finding(
                id="wsl_missing",
                level="info",
                title="WSL 未检测到",
                message=(
                    "Windows 上未检测到 WSL。纯 Windows 工具链可以继续，但 Linux 教程、部分容器工作流和命令行工具"
                    "不能默认照搬；如需要 Linux 环境，先运行 wsl --status 或 wsl -l -v 确认。"
                ),
                goal_id=goal_id,
                component="wsl",
                evidence={"wsl_installed": profile.wsl_installed},
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
                    message="检测到 NVIDIA 独立显卡，可以考虑 GPU 加速，但仍取决于独立显存容量、量化方式和模型大小。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={
                        "primary_gpu": primary_gpu.name,
                        "dedicated_vram_gb": primary_gpu.dedicated_vram_gb,
                        "vram_confidence": primary_gpu.vram_confidence,
                    },
                ),
            )
            if primary_gpu.dedicated_vram_gb is not None and primary_gpu.dedicated_vram_gb < 8:
                _append_unique(
                    findings,
                    _finding(
                        id="local_llm_vram_low",
                        level="warning",
                        title="本地大模型显存偏低",
                        message=(
                            f"{primary_gpu.name} 独立显存约 {primary_gpu.dedicated_vram_gb:g}GB。"
                            "建议从 7B Q4/Q5 或 CPU/内存路径开始，不要直接尝试大上下文或大参数模型。"
                        ),
                        goal_id=goal_id,
                        component="vram",
                        evidence={
                            "primary_gpu": primary_gpu.name,
                            "dedicated_vram_gb": primary_gpu.dedicated_vram_gb,
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

    if goal_id == "creator_setup" and primary_gpu is not None:
        if primary_gpu.gpu_type == "integrated":
            _append_unique(
                findings,
                _finding(
                    id="creator_integrated_gpu",
                    level="warning",
                    title="创作工作流主要依赖核显",
                    message=(
                        f"当前主要 GPU 是 {primary_gpu.name}。适合：录屏、轻量剪辑、音频处理和基础转码；"
                        "不适合：4K 多轨剪辑、复杂调色、Blender 重渲染或 GPU 特效；建议先降低分辨率、码率和缓存压力。"
                    ),
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"primary_gpu": primary_gpu.name, "gpu_type": primary_gpu.gpu_type},
                ),
            )
        elif primary_gpu.gpu_type == "dedicated":
            _append_unique(
                findings,
                _finding(
                    id="creator_dedicated_gpu",
                    level="info",
                    title="检测到独立显卡",
                    message=(
                        "检测到独立显卡，适合把 OBS 硬件编码、剪辑软件缓存和 Blender 渲染作为可选能力；"
                        "仍需要按显存、驱动和项目分辨率判断具体强度。"
                    ),
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
                    id="creator_gpu_unknown",
                    level="warning",
                    title="创作性能无法确认",
                    message="当前 GPU 类型未知，视频剪辑、录屏编码和 3D 渲染建议需要用户补充显卡型号与显存后再判断。",
                    goal_id=goal_id,
                    component="gpu",
                    evidence={"primary_gpu": primary_gpu.name, "gpu_type": primary_gpu.gpu_type},
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
                message=(
                    "未检测到独立显存容量，AI 绘图和本地大模型建议会保守处理。"
                    "请在任务管理器 GPU 页面、nvidia-smi 或显卡驱动面板中确认显存后再选择大型模型。"
                ),
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
        elif finding.id == "failed_check_disk":
            actions.append("在手动确认磁盘剩余空间前下载大型模型、素材库或安装体积较大的软件。")
        elif finding.id == "comfyui_vram_low":
            actions.append("使用高分辨率 ComfyUI 出图、大批量生成或大型模型。")
        elif finding.id in {"comfyui_integrated_gpu", "shared_vram_risk"}:
            actions.append("把共享显存或核显当作重型 AI 绘图、4K 剪辑或大型游戏的主要算力。")
        elif finding.id == "local_llm_ram_low":
            actions.append("在低于 16GB 内存的电脑上运行较大的本地大模型或长上下文。")
        elif finding.id == "local_llm_vram_low":
            actions.append("在低显存显卡上直接运行大参数、大上下文或未量化模型。")
        elif finding.id == "model_directory_risk":
            actions.append("在没有规划模型目录的情况下连续下载多个大型模型。")
        elif finding.id == "cache_directory_risk":
            actions.append("在没有确认缓存目录的情况下批量安装 custom nodes、Python 包或模型依赖。")
        elif finding.id == "git_missing":
            actions.append("在没有 Git 的情况下开始需要版本管理的编程工作流。")
        elif finding.id == "python_missing":
            actions.append("在未准备 Python 的情况下直接配置依赖 Python 的开发或 AI 工具。")
    return actions
