from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .templates import project_root


def _bar(score: int | float | None, width: int = 10) -> str:
    value = max(0, min(100, int(score or 0)))
    filled = round(value / 100 * width)
    return "[" + "■" * filled + "□" * (width - filled) + f"] {value}/100"


def _line(value: object | None) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, str) and not value.strip():
        return "unknown"
    return str(value)


def render_markdown(evaluation_data: dict[str, Any]) -> str:
    hardware = evaluation_data.get("hardware_summary", {})
    scores = evaluation_data.get("scores", {})
    risks = evaluation_data.get("risk_alerts", [])
    recommendations = evaluation_data.get("recommendations", {})

    os_info = hardware.get("os") or {}
    cpu = hardware.get("cpu") or {}
    memory = hardware.get("memory") or {}
    disk = hardware.get("disk") or {}
    primary_gpu = hardware.get("primary_gpu") or {}
    tools = hardware.get("tools") or {}

    score_rows = ["| Scenario | Score |", "| --- | --- |"]
    for key in ("coding", "gaming", "ai", "creator"):
        score_rows.append(f"| {key} | {_bar(scores.get(key))} |")

    risk_rows = ["| Level | Message | Component |", "| --- | --- | --- |"]
    if risks:
        for item in risks:
            risk_rows.append(
                f"| {_line(item.get('level'))} | {_line(item.get('msg'))} | {_line(item.get('component'))} |"
            )
    else:
        risk_rows.append("| info | no risk alerts | none |")

    app_rows = ["| App | Required | Reason |", "| --- | --- | --- |"]
    apps = recommendations.get("apps") or []
    if apps:
        for app in apps:
            app_rows.append(
                f"| {_line(app.get('name'))} | {_line(app.get('required'))} | {_line(app.get('reason'))} |"
            )
    else:
        app_rows.append("| none | false | no recommendations |")

    return "\n".join(
        [
            "# StackPilot Report",
            "",
            "## Hardware Summary",
            "",
            f"- OS: {_line(os_info.get('name'))} {_line(os_info.get('version'))}",
            f"- Architecture: {_line(os_info.get('architecture'))}",
            f"- CPU: {_line(cpu.get('name'))}",
            f"- CPU cores: {_line(cpu.get('cores'))}",
            f"- RAM GB: {_line(memory.get('ram_gb') or memory.get('total_ram_gb'))}",
            f"- Disk: {_line(disk.get('anchor'))} total={_line(disk.get('total_gb'))}GB free={_line(disk.get('free_gb'))}GB",
            f"- Primary GPU: {_line(primary_gpu.get('name'))}",
            f"- GPU type: {_line(primary_gpu.get('gpu_type'))}",
            f"- VRAM confidence: {_line(primary_gpu.get('vram_confidence'))}",
            "",
            "## Tool Status",
            "",
            f"- Python: {_line((tools.get('python') or {}).get('version'))}",
            f"- Git: {_line((tools.get('git') or {}).get('version'))}",
            f"- Docker: {_line((tools.get('docker') or {}).get('version'))}",
            f"- WSL: {_line((tools.get('wsl') or {}).get('available'))}",
            "",
            "## Scores",
            "",
            *score_rows,
            "",
            "## Risk Alerts",
            "",
            *risk_rows,
            "",
            "## Recommendations",
            "",
            f"- Selected goal: {_line(recommendations.get('selected_goal'))}",
            f"- Goal ID: {_line(recommendations.get('goal_id'))}",
            f"- Goal name: {_line(recommendations.get('goal_name'))}",
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
