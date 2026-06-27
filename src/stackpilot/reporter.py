from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .templates import project_root


SCENARIO_NAMES = {
    "coding": "Coding 环境",
    "gaming": "Gaming 配置",
    "ai": "AI 场景评估",
    "creator": "Creator 方案",
}

LEVEL_NAMES = {
    "error": "严重",
    "critical": "严重",
    "warning": "警告",
    "info": "信息",
}

GPU_TYPE_NAMES = {
    "dedicated": "独立显卡",
    "integrated": "核显",
    "virtual": "虚拟显卡",
    "unknown": "未确认",
}

VRAM_CONFIDENCE_NAMES = {
    "detected": "已检测",
    "estimated": "估算",
    "shared": "共享内存",
    "unknown": "未确认",
}


def _bar(score: int | float | None, width: int = 10) -> str:
    value = max(0, min(100, int(score or 0)))
    filled = round(value / 100 * width)
    return "[" + "■" * filled + "□" * (width - filled) + f"] {value}/100"


def _line(value: object | None) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, str) and not value.strip():
        return "未检测到"
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def _scenario_name(key: object | None) -> str:
    text = _line(key)
    return SCENARIO_NAMES.get(text, text)


def _level_name(key: object | None) -> str:
    text = _line(key)
    return LEVEL_NAMES.get(text, text)


def _gpu_type_name(key: object | None) -> str:
    text = _line(key)
    return GPU_TYPE_NAMES.get(text, text)


def _vram_confidence_name(key: object | None) -> str:
    text = _line(key)
    return VRAM_CONFIDENCE_NAMES.get(text, text)


def _yes_no(value: object | None) -> str:
    return "必选" if bool(value) else "可选"


def _join_available(*values: object | None) -> str:
    available = [_line(value) for value in values if _line(value) != "未检测到"]
    return " ".join(available) if available else "未检测到"


def _cpu_cores(cpu_details: dict[str, Any], cpu: dict[str, Any]) -> str:
    physical = _line(cpu_details.get("physical_cores"))
    logical = _line(cpu_details.get("logical_cores") or cpu.get("cores"))
    if physical == "未检测到" and logical == "未检测到":
        return "未检测到"
    if physical == "未检测到":
        return f"{logical} 线程"
    if logical == "未检测到":
        return f"{physical} 核"
    return f"{physical}C/{logical}T"


def render_markdown(evaluation_data: dict[str, Any]) -> str:
    hardware = evaluation_data.get("hardware_summary", {})
    scores = evaluation_data.get("scores", {})
    risks = evaluation_data.get("risk_alerts", [])
    recommendations = evaluation_data.get("recommendations", {})

    os_info = hardware.get("os") or {}
    computer = hardware.get("computer_model") or {}
    baseboard = hardware.get("baseboard") or {}
    bios = hardware.get("bios") or {}
    cpu = hardware.get("cpu") or {}
    cpu_details = cpu.get("details") or {}
    memory = hardware.get("memory") or {}
    memory_details = memory.get("details") or {}
    disk = hardware.get("disk") or {}
    disk_devices = disk.get("devices") or []
    disk_volumes = disk.get("volumes") or []
    primary_gpu = hardware.get("primary_gpu") or {}
    tools = hardware.get("tools") or {}

    score_rows = ["| 场景 | 评分 |", "| --- | --- |"]
    for key in ("coding", "gaming", "ai", "creator"):
        score_rows.append(f"| {_scenario_name(key)} | {_bar(scores.get(key))} |")

    risk_rows = ["| 等级 | 说明 | 组件 |", "| --- | --- | --- |"]
    if risks:
        for item in risks:
            risk_rows.append(
                f"| {_level_name(item.get('level'))} | {_line(item.get('msg'))} | {_line(item.get('component'))} |"
            )
    else:
        risk_rows.append("| 信息 | 暂无风险提示 | 无 |")

    app_rows = ["| 应用 | 必选/可选 | 推荐原因 |", "| --- | --- | --- |"]
    apps = recommendations.get("apps") or []
    if apps:
        for app in apps:
            app_rows.append(
                f"| {_line(app.get('name'))} | {_yes_no(app.get('required'))} | {_line(app.get('reason'))} |"
            )
    else:
        app_rows.append("| 暂无 | 可选 | 暂无推荐 |")

    return "\n".join(
        [
            "# StackPilot 报告",
            "",
            "## 硬件摘要",
            "",
            f"- 系统：{_line(os_info.get('name'))} {_line(os_info.get('version'))}",
            f"- 架构：{_line(os_info.get('architecture'))}",
            f"- 整机型号：{_join_available(computer.get('manufacturer'), computer.get('model'))}",
            f"- 主板：{_join_available(baseboard.get('manufacturer'), baseboard.get('product'))}",
            f"- BIOS：{_join_available(bios.get('manufacturer'), bios.get('version'), bios.get('release_date'))}",
            f"- CPU：{_line(cpu_details.get('name') or cpu.get('name'))}",
            f"- CPU 核心：{_cpu_cores(cpu_details, cpu)}",
            f"- 内存：{_line(memory_details.get('total_gb') or memory.get('ram_gb') or memory.get('total_ram_gb'))} GB",
            f"- 磁盘：{_line(disk.get('anchor'))} 总计 {_line(disk.get('total_gb'))} GB，剩余 {_line(disk.get('free_gb'))} GB",
            f"- 物理磁盘数量：{_line(len(disk_devices))}",
            f"- 磁盘卷数量：{_line(len(disk_volumes))}",
            f"- 主要 GPU：{_line(primary_gpu.get('name'))}",
            f"- GPU 类型：{_gpu_type_name(primary_gpu.get('gpu_type'))}",
            f"- 显存置信度：{_vram_confidence_name(primary_gpu.get('vram_confidence'))}",
            "",
            "## 工具状态",
            "",
            f"- Python：{_line((tools.get('python') or {}).get('version'))}",
            f"- Git：{_line((tools.get('git') or {}).get('version'))}",
            f"- Docker：{_line((tools.get('docker') or {}).get('version'))}",
            f"- WSL：{_line((tools.get('wsl') or {}).get('available'))}",
            "",
            "## 场景评分",
            "",
            *score_rows,
            "",
            "## 风险提示",
            "",
            *risk_rows,
            "",
            "## 推荐配置",
            "",
            f"- 当前场景：{_scenario_name(recommendations.get('selected_goal'))}",
            f"- 模板 ID：{_line(recommendations.get('goal_id'))}",
            f"- 模板名称：{_line(recommendations.get('goal_name'))}",
            "",
            *app_rows,
            "",
        ]
    )


def default_report_dir() -> Path:
    return project_root() / "outputs" / "reports"


def _should_open_notepad() -> bool:
    return os.name == "nt"


def _unique_report_path(target_dir: Path, timestamp: str) -> Path:
    report_path = target_dir / f"report_{timestamp}.md"
    if not report_path.exists():
        return report_path
    counter = 2
    while True:
        candidate = target_dir / f"report_{timestamp}_{counter}.md"
        if not candidate.exists():
            return candidate
        counter += 1


def export_report(
    evaluation_data: dict[str, Any],
    output_dir: str | Path | None = None,
    *,
    open_notepad: bool = True,
) -> Path:
    target_dir = Path(output_dir) if output_dir is not None else default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = _unique_report_path(target_dir, timestamp)
    report_path.write_text(render_markdown(evaluation_data), encoding="utf-8")

    if open_notepad and _should_open_notepad():
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            ["cmd", "/c", "start", "", "notepad.exe", str(report_path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

    return report_path
