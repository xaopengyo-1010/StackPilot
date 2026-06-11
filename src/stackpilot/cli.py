from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .models import HardwareProfile, RecommendationResult
from .recommender import recommend
from .report import generate_report
from .scanner import scan_system
from .templates import UnknownTemplateError, load_template, load_templates, template_audience


app = typer.Typer(help="StackPilot：给小白用的电脑应用推荐助手。")
console = Console()


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


def _print_profile(profile: HardwareProfile) -> None:
    table = Table(title="电脑配置摘要")
    table.add_column("项目")
    table.add_column("检测结果")
    values = {
        "系统": f"{_missing(profile.os_name)} {_missing(profile.os_version)}".strip(),
        "架构": _missing(profile.architecture),
        "CPU": _missing(profile.cpu_name),
        "CPU 核心数": _missing(profile.cpu_cores),
        "内存": _format_gb(profile.ram_gb),
        "显卡": "、".join(profile.gpu_names) if profile.gpu_names else "未检测到",
        "显存": _format_gb(profile.vram_gb),
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
    for key, value in values.items():
        table.add_row(key, value)
    console.print(table)
    if profile.warnings:
        console.print("[yellow]检测提示[/yellow]")
        for warning in profile.warnings:
            console.print(f"- {warning}")


def _print_section(title: str, values: list[str], empty_text: str) -> None:
    console.print(f"[bold]{title}[/bold]")
    if values:
        for value in values:
            console.print(f"- {value}")
    else:
        console.print(empty_text)


def _print_findings(recommendation: RecommendationResult) -> None:
    console.print("[bold]规则判断与风险提示：[/bold]")
    if not recommendation.findings:
        console.print("暂无明显风险提示。")
        return
    level_names = {"critical": "严重", "warning": "提醒", "info": "信息"}
    for finding in recommendation.findings:
        console.print(f"- [{level_names[finding.level]}] {finding.title}：{finding.message}")


def _print_recommendation(recommendation: RecommendationResult) -> None:
    console.print(f"[bold]推荐结果：{recommendation.display_name}[/bold]")
    console.print("")
    console.print(f"适配度评分：{_format_score(recommendation.suitability_score)} / 100")
    console.print("")

    console.print("[bold]推荐应用：[/bold]")
    for item in recommendation.recommended_apps:
        required = "必装" if item.required else "可选"
        console.print(f"- {item.name}（{required}）：{item.reason}")
    console.print("")

    _print_findings(recommendation)
    console.print("")
    _print_section("配置建议：", recommendation.config_recommendations, "暂无额外配置建议。")
    console.print("")
    _print_section("当前不推荐事项：", recommendation.not_recommended, "暂无明显不推荐事项。")
    console.print("")
    _print_section("下一步：", recommendation.next_steps, "暂无下一步建议。")


def _missing_goal() -> None:
    console.print("[red]缺少 --goal。[/red]请先运行 `python -m stackpilot list-templates` 查看可用模板。")


@app.command("scan")
def scan_command() -> None:
    """检测本机公开系统信息。"""

    _print_profile(scan_system())


@app.command("list-templates")
def list_templates_command() -> None:
    """列出可用推荐模板。"""

    table = Table(title="可用模板")
    table.add_column("模板 ID")
    table.add_column("模板名称")
    table.add_column("适合谁")
    for template in load_templates():
        table.add_row(template.template_id, template.display_name, template_audience(template.template_id))
    console.print(table)


@app.command("recommend")
def recommend_command(goal: Optional[str] = typer.Option(None, "--goal", "-g", help="模板 ID。")) -> None:
    """根据使用目标生成应用推荐。"""

    if not goal:
        _missing_goal()
        raise typer.Exit(code=1)
    try:
        _print_recommendation(recommend(goal))
    except UnknownTemplateError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.command("report")
def report_command(goal: Optional[str] = typer.Option(None, "--goal", "-g", help="模板 ID。")) -> None:
    """生成 Markdown 和 JSON 推荐报告。"""

    if not goal:
        _missing_goal()
        raise typer.Exit(code=1)
    try:
        md_path, json_path, recommendation = generate_report(goal)
    except UnknownTemplateError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"报告已生成：{recommendation.display_name}")
    console.print(str(md_path))
    console.print(str(json_path))


@app.command("doctor")
def doctor_command(goal: Optional[str] = typer.Option(None, "--goal", "-g", help="模板 ID。")) -> None:
    """检测电脑配置，生成推荐和报告。"""

    if not goal:
        _missing_goal()
        raise typer.Exit(code=1)
    try:
        template = load_template(goal)
    except UnknownTemplateError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print("正在检测电脑配置...")
    profile = scan_system()
    console.print(f"正在生成推荐：{template.display_name}...")
    try:
        md_path, json_path, _ = generate_report(goal, profile=profile)
    except UnknownTemplateError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print("报告已生成：")
    console.print(str(md_path))
    console.print(str(json_path))


def main() -> None:
    app()
