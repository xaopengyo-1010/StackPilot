from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable

from stackpilot.detector import StackPilotDetector
from stackpilot.recommender import StackPilotRecommender
from stackpilot.reporter import export_report
from stackpilot.templates import UnknownTemplateError


VERSION = "v0.7.1-beta"

ANSI = {
    "cyan": "\033[1;36m",
    "green": "\033[1;32m",
    "yellow": "\033[1;33m",
    "red": "\033[1;31m",
    "gray": "\033[90m",
    "reset": "\033[0m",
}


class TuiInputClosed(Exception):
    """Raised when stdin closes while the TUI is waiting for input."""


def format_tui_error(exc: Exception) -> str:
    if isinstance(exc, UnknownTemplateError):
        if not exc.available:
            return (
                "未找到内置配置模板。请确认正在运行的是最新的 StackPilot_TUI.exe；"
                "如果是从源码运行，请在项目根目录执行。"
            )
        return str(exc)
    if isinstance(exc, FileNotFoundError):
        return f"配置文件缺失：{exc}"
    if isinstance(exc, OSError):
        return f"检测或文件访问失败：{exc}"
    if isinstance(exc, ValueError):
        return f"配置数据解析失败：{exc}"
    return f"检测流程失败：{exc.__class__.__name__}: {exc}"


def render_tui_error(message: str, write: Callable[[str], None] = print) -> None:
    write(f"{ANSI['red']}[错误] {message}{ANSI['reset']}")
    write(f"{ANSI['yellow']}程序没有修改系统。请保留这段提示，方便反馈问题。{ANSI['reset']}")
    write("")


def wait_after_error(
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> bool:
    try:
        read(f"{ANSI['gray']}按 Enter 返回主菜单，或关闭窗口退出...{ANSI['reset']}")
    except (EOFError, KeyboardInterrupt):
        write(f"{ANSI['gray']}输入已结束，程序退出。{ANSI['reset']}")
        return False
    return True

SCENARIOS = {
    "1": ("coding", "Coding 环境", "通用软件开发后端"),
    "2": ("gaming", "Gaming 配置", "游戏开发与高性能运行"),
    "3": ("ai", "AI 场景评估", "本地大模型训练与推理"),
    "4": ("creator", "Creator 方案", "音视频多媒体内容创作"),
}

SCENARIO_NAMES = {
    "coding": "Coding 环境",
    "gaming": "Gaming 配置",
    "ai": "AI 场景评估",
    "creator": "Creator 方案",
}


def app_base_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def enable_utf8_console() -> None:
    if os.name == "nt":
        os.system("chcp 65001 >nul")
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def prompt(read: Callable[[str], str] = input, accent: str = "cyan") -> str:
    prefix = f"{ANSI['gray']}stackpilot@local {ANSI[accent]}❯ {ANSI['reset']}"
    try:
        return read(prefix).strip()
    except (EOFError, KeyboardInterrupt) as exc:
        raise TuiInputClosed from exc


def run_pipeline(goal: str = "ai") -> dict[str, Any]:
    raw_specs = StackPilotDetector().scan_system()
    return StackPilotRecommender().evaluate(raw_specs, goal=goal)


def draw_logo(write: Callable[[str], None] = print) -> None:
    cyan = ANSI["cyan"]
    gray = ANSI["gray"]
    reset = ANSI["reset"]

    write(f"{gray}┌────────────────────────────────────────────────────────┐{reset}")
    write(
        f"{gray}│{reset}{cyan}"
        "   ____  _             _    ____  _ _       _   "
        f"{reset}{gray}│{reset}"
    )
    write(
        f"{gray}│{reset}{cyan}"
        "  / ___|| |_ __ _  ___| | _|  _ \\(_) | ___ | |_ "
        f"{reset}{gray}│{reset}"
    )
    write(
        f"{gray}│{reset}{cyan}"
        "  \\___ \\| __/ _` |/ __| |/ / |_) | | |/ _ \\| __|"
        f"{reset}{gray}│{reset}"
    )
    write(
        f"{gray}│{reset}{cyan}"
        "   ___) | || (_| | (__|   <|  __/| | | (_) | |_ "
        f"{reset}{gray}│{reset}"
    )
    write(
        f"{gray}│{reset}{cyan}"
        "  |____/ \\__\\__,_|\\___|_|\\_\\_|   |_|_|\\___/ \\__|"
        f"{reset}{gray}│{reset}"
    )
    write(
        f"{gray}├─────────────────────── {cyan}{VERSION}{gray} ───────────────────────┤"
        f"{reset}"
    )
    write("")


def draw_goal_menu(write: Callable[[str], None] = print) -> None:
    cyan = ANSI["cyan"]
    reset = ANSI["reset"]

    lines = [
        "┌────────────────────────────────────────────────────────┐",
        "│         请选择您的主要目标场景 (Target Scenario)        │",
        "├────────────────────────────────────────────────────────┤",
        "│  [1]  Coding 环境 (通用软件开发后端)                  │",
        "│  [2]  Gaming 配置 (游戏开发与高性能运行)              │",
        "│  [3]  AI 场景评估 (本地大模型训练与推理)              │",
        "│  [4]  Creator 方案 (音视频多媒体内容创作)             │",
        "└────────────────────────────────────────────────────────┘",
    ]
    for line in lines:
        write(f"{cyan}{line}{reset}")


def choose_goal(
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> str:
    while True:
        draw_goal_menu(write)
        choice = prompt(read, "cyan")
        if choice in SCENARIOS:
            return SCENARIOS[choice][0]
        write(f"{ANSI['yellow']}请输入 1、2、3 或 4。{ANSI['reset']}")
        write("")


def score_bar(score: int | float | None, width: int = 10) -> str:
    value = max(0, min(100, int(score or 0)))
    filled = round(value / 100 * width)
    empty = width - filled
    return f"[{'■' * filled}{'□' * empty}] {value:3d}/100"


def render_scores(
    evaluation_data: dict[str, Any],
    selected_goal: str,
    write: Callable[[str], None],
) -> None:
    scores = evaluation_data.get("scores", {})
    write(f"{ANSI['cyan']}┌─ 场景评分 ──────────────────────────────────────────────┐{ANSI['reset']}")

    for key in ("coding", "gaming", "ai", "creator"):
        score = scores.get(key)
        label = SCENARIO_NAMES.get(key, key)
        suffix = " [当前目标]" if key == selected_goal else ""
        color = ANSI["green"] if key == selected_goal else ANSI["gray"]
        line = f"│  {label:<14} {score_bar(score)}{suffix}"
        write(f"{color}{line}{ANSI['reset']}")

    write(f"{ANSI['cyan']}└────────────────────────────────────────────────────────┘{ANSI['reset']}")
    write("")


def render_risks(evaluation_data: dict[str, Any], write: Callable[[str], None]) -> None:
    risks = evaluation_data.get("risk_alerts", [])
    write(f"{ANSI['cyan']}┌─ 风险警报 ──────────────────────────────────────────────┐{ANSI['reset']}")

    if not risks:
        write(f"{ANSI['green']}│  未发现需要阻断当前目标的风险项。{ANSI['reset']}")
        write(f"{ANSI['cyan']}└────────────────────────────────────────────────────────┘{ANSI['reset']}")
        write("")
        return

    for item in risks:
        level = item.get("level")
        component = item.get("component") or "system"
        message = item.get("msg") or "未提供风险说明"
        if level == "error":
            color = ANSI["red"]
            label = "[✘] 致命"
        else:
            color = ANSI["yellow"]
            label = "[⚠] 警告"
        write(f"{color}│  {label}  {component}: {message}{ANSI['reset']}")

    write(f"{ANSI['cyan']}└────────────────────────────────────────────────────────┘{ANSI['reset']}")
    write("")


def render_recommendations(
    evaluation_data: dict[str, Any],
    write: Callable[[str], None],
) -> None:
    recommendations = evaluation_data.get("recommendations", {})
    apps = recommendations.get("apps") or []
    goal_name = recommendations.get("goal_name") or recommendations.get("goal_id") or "未知目标"

    write(f"{ANSI['cyan']}┌─ 推荐配置 ──────────────────────────────────────────────┐{ANSI['reset']}")
    write(f"{ANSI['gray']}│  当前模板: {goal_name}{ANSI['reset']}")

    if not apps:
        write(f"{ANSI['yellow']}│  当前模板未返回可安装组件建议。{ANSI['reset']}")
    else:
        for app in apps[:8]:
            name = app.get("name") or "未命名组件"
            marker = "必选" if app.get("required") else "可选"
            reason = app.get("reason") or "未提供说明"
            write(f"{ANSI['gray']}│  [{marker}] {name} - {reason}{ANSI['reset']}")
        remaining = len(apps) - 8
        if remaining > 0:
            write(f"{ANSI['gray']}│  另有 {remaining} 项建议已写入导出报告。{ANSI['reset']}")

    write(f"{ANSI['cyan']}└────────────────────────────────────────────────────────┘{ANSI['reset']}")
    write("")


def render_evaluation(
    evaluation_data: dict[str, Any],
    selected_goal: str,
    write: Callable[[str], None] = print,
) -> None:
    render_scores(evaluation_data, selected_goal, write)
    render_risks(evaluation_data, write)
    render_recommendations(evaluation_data, write)


def draw_control_menu(write: Callable[[str], None] = print) -> None:
    cyan = ANSI["cyan"]
    reset = ANSI["reset"]
    write(f"{cyan}┌─ 控制菜单 ──────────────────────────────────────────────┐{reset}")
    write(f"{cyan}│  [1] 重新检测    [2] 导出报告    [3] 退出程序           │{reset}")
    write(f"{cyan}└────────────────────────────────────────────────────────┘{reset}")


def control_loop(
    evaluation_data: dict[str, Any],
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> str:
    while True:
        draw_control_menu(write)
        choice = prompt(read, "green")
        if choice == "1":
            return "rescan"
        if choice == "2":
            try:
                path = export_report(evaluation_data)
            except OSError as exc:
                write(f"{ANSI['red']}[✘] 致命  报告导出失败: {exc}{ANSI['reset']}")
            else:
                write(f"{ANSI['green']}[✓] 报告已导出: {path}{ANSI['reset']}")
            write("")
            continue
        if choice == "3":
            return "exit"
        write(f"{ANSI['yellow']}请输入 1、2 或 3。{ANSI['reset']}")
        write("")


def tui_loop(
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> None:
    while True:
        clear_screen()
        draw_logo(write)
        try:
            goal = choose_goal(read, write)
        except TuiInputClosed:
            write(f"{ANSI['gray']}输入已结束，程序退出。{ANSI['reset']}")
            return

        clear_screen()
        draw_logo(write)
        write(f"{ANSI['green']}正在检测当前主机，目标场景: {SCENARIO_NAMES[goal]}{ANSI['reset']}")
        write("")

        try:
            evaluation_data = run_pipeline(goal)
        except Exception as exc:
            render_tui_error(format_tui_error(exc), write)
            if wait_after_error(read, write):
                continue
            return
        render_evaluation(evaluation_data, goal, write)

        try:
            action = control_loop(evaluation_data, read, write)
        except TuiInputClosed:
            write(f"{ANSI['gray']}输入已结束，程序退出。{ANSI['reset']}")
            return
        if action == "rescan":
            continue
        return


def run_tui(
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> None:
    enable_utf8_console()
    tui_loop(read, write)


def main() -> None:
    run_tui()


if __name__ == "__main__":
    main()
