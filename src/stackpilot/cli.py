from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .executors.dry_run import DryRunExecutor
from .models import HardwareProfile, RecommendationResult
from .plans.audit import audit_install_plan
from .plans.models import InstallPlan
from .plans.planner import build_install_plan
from .plans.renderer import render_dry_run_json, render_dry_run_markdown, write_plan_artifacts
from .recommender import recommend
from .report import generate_report
from .rollbacks.planner import build_rollback_plan
from .scanner import scan_system
from .snapshots.planner import build_snapshot_plan
from .templates import UnknownTemplateError, load_template, load_templates, template_audience
from .utils import parse_model


app = typer.Typer(help="StackPilot：本地电脑环境检测与推荐工具。")
console = Console()


def _missing(value: object | None) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, str) and not value.strip():
        return "未检测到"
    return str(value)


def _gb(value: float | None) -> str:
    return "未检测到" if value is None else f"{value:g} GB"


def _platform_value(profile: HardwareProfile, field: str) -> str:
    return "未检测到" if profile.platform_profile is None else _missing(getattr(profile.platform_profile, field))


def _join_parts(*parts: object | None) -> str:
    values = [_missing(part) for part in parts if part is not None and _missing(part) != "鏈娴嬪埌"]
    return " / ".join(values) if values else "鏈娴嬪埌"


def _computer_model(profile: HardwareProfile) -> str:
    model = profile.computer_model
    return "鏈娴嬪埌" if model is None else _join_parts(model.manufacturer, model.model, model.system_sku)


def _baseboard(profile: HardwareProfile) -> str:
    board = profile.baseboard
    return "鏈娴嬪埌" if board is None else _join_parts(board.manufacturer, board.product, board.version)


def _bios(profile: HardwareProfile) -> str:
    bios = profile.bios
    return "鏈娴嬪埌" if bios is None else _join_parts(bios.manufacturer, bios.version, bios.release_date)


def _cpu(profile: HardwareProfile) -> str:
    cpu = profile.cpu
    if cpu is None:
        return _missing(profile.cpu_name)
    cores = f"{cpu.physical_cores or '?'}C/{cpu.logical_cores or '?'}T" if cpu.physical_cores or cpu.logical_cores else None
    clock = f"{cpu.max_clock_mhz} MHz" if cpu.max_clock_mhz else None
    return _join_parts(cpu.name, cores, clock)


def _memory(profile: HardwareProfile) -> str:
    memory = profile.memory
    if memory is None:
        return _gb(profile.ram_gb)
    modules = [
        _join_parts(module.device_locator or module.bank_label, _gb(module.capacity_gb), f"{module.speed_mhz} MHz" if module.speed_mhz else None)
        for module in memory.modules
    ]
    suffix = "\n".join(f"- {module}" for module in modules if module != "鏈娴嬪埌")
    total = f"总计 {_gb(memory.total_gb)}"
    return f"{total}\n{suffix}" if suffix else total


def _disk_devices(profile: HardwareProfile) -> str:
    if not profile.disks:
        return "鏈娴嬪埌"
    return "\n".join(f"- {_join_parts(disk.model, _gb(disk.size_gb), disk.media_type, disk.interface_type)}" for disk in profile.disks)


def _disk_volumes(profile: HardwareProfile) -> str:
    if not profile.disk_volumes:
        return _join_parts(profile.disk_anchor, f"总计 {_gb(profile.disk_total_gb)}", f"剩余 {_gb(profile.disk_free_gb)}")
    return "\n".join(
        f"- {_join_parts(volume.name, volume.file_system, f'总计 {_gb(volume.size_gb)}', f'剩余 {_gb(volume.free_gb)}')}"
        for volume in profile.disk_volumes
    )


def _print_items(title: str, values: list[str], empty_text: str) -> None:
    console.print(f"[bold]{title}[/bold]")
    if values:
        for value in values:
            console.print(f"- {value}")
    else:
        console.print(empty_text)


def _print_failed_checks(failed_checks: list) -> None:
    if not failed_checks:
        return
    table = Table(title="检测失败项")
    table.add_column("检测项")
    table.add_column("状态")
    table.add_column("影响")
    table.add_column("手动确认")
    for check in failed_checks:
        table.add_row(check.check_name, check.status, check.impact, check.manual_check)
    console.print(table)


def _goal_or_exit(goal: str | None) -> str:
    if goal:
        return goal
    console.print("[red]缺少 --goal。[/red]请先运行 `python -m stackpilot list-templates` 查看可用模板。")
    raise typer.Exit(code=1)


def _unknown_template(exc: UnknownTemplateError) -> None:
    console.print(f"[red]{exc}[/red]")
    raise typer.Exit(code=1) from exc


@app.command("scan")
def scan_command() -> None:
    """检测本机公开系统信息。"""

    profile = scan_system()
    gpu_list = (
        "\n".join(f"- {gpu.markdown_summary()}" for gpu in profile.gpus)
        if profile.gpus
        else "、".join(profile.gpu_names)
        if profile.gpu_names
        else "未检测到"
    )
    table = Table(title="电脑配置摘要")
    table.add_column("项目")
    table.add_column("检测结果")
    rows = {
        "系统": f"{_missing(profile.os_name)} {_missing(profile.os_version)}".strip(),
        "架构": _missing(profile.architecture),
        "平台类型": _platform_value(profile, "os_family"),
        "默认安装后端": _platform_value(profile, "default_installer_backend"),
        "整机型号": _computer_model(profile),
        "主板": _baseboard(profile),
        "BIOS": _bios(profile),
        "CPU": _cpu(profile),
        "CPU 核心数": _missing(profile.cpu_cores),
        "内存": _memory(profile),
        "检测到的 GPU": gpu_list,
        "主要性能判断 GPU": profile.primary_gpu.name if profile.primary_gpu else "未能可靠确认",
        "GPU 选择原因": profile.gpu_selection_reason or "未能可靠确认 GPU 选择原因",
        "兼容显存字段": _gb(profile.vram_gb),
        "物理磁盘": _disk_devices(profile),
        "磁盘卷": _disk_volumes(profile),
        "磁盘总容量": _gb(profile.disk_total_gb),
        "磁盘剩余空间": _gb(profile.disk_free_gb),
        "Python": profile.python_version if profile.python_installed and profile.python_version else "未检测到",
        "Node.js": profile.node_version if profile.node_installed and profile.node_version else "未检测到",
        "Git": profile.git_version if profile.git_installed and profile.git_version else "未检测到",
        "pnpm": profile.pnpm_version if profile.pnpm_installed and profile.pnpm_version else "未检测到",
        "Docker": profile.docker_version if profile.docker_installed and profile.docker_version else "未检测到",
        "WSL": "已检测到" if profile.wsl_installed else "未检测到",
        "NVIDIA 驱动": profile.nvidia_driver_version or "未检测到",
    }
    for key, value in rows.items():
        table.add_row(key, value)
    console.print(table)

    if profile.warnings:
        console.print("[yellow]检测提示[/yellow]")
        for warning in profile.warnings:
            console.print(f"- {warning}")
    _print_failed_checks(profile.failed_checks)


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

    goal = _goal_or_exit(goal)
    try:
        recommendation = recommend(goal)
    except UnknownTemplateError as exc:
        _unknown_template(exc)

    console.print(f"[bold]推荐结果：{recommendation.display_name}[/bold]\n")
    console.print(f"适配度评分：{recommendation.suitability_score:g} / 100\n")
    console.print("[bold]推荐应用：[/bold]")
    for item in recommendation.recommended_apps:
        required = "必装" if item.required else "可选"
        console.print(f"- {item.name}（{required}）：{item.reason}")
    console.print("")

    console.print("[bold]规则判断与风险提示：[/bold]")
    if recommendation.findings:
        level_names = {"critical": "严重", "warning": "提醒", "info": "信息"}
        for finding in recommendation.findings:
            console.print(f"- [{level_names[finding.level]}] {finding.title}：{finding.message}")
    else:
        console.print("暂无明显风险提示。")
    _print_failed_checks(recommendation.failed_checks)
    console.print("")

    tier = recommendation.capability_tier
    if tier is not None:
        console.print("[bold]能力分级：[/bold]")
        console.print(f"- 当前等级：{tier.tier}")
        _print_items("适合：", tier.suitable, "暂无适合项。")
        _print_items("不适合：", tier.not_suitable, "暂无不适合项。")
        _print_items("风险：", tier.risks, "暂无额外风险。")
        console.print("")

    disk = recommendation.disk_risk_analysis
    if disk is not None:
        console.print("[bold]磁盘风险分析：[/bold]")
        console.print(f"- 风险等级：{disk.risk_level}")
        console.print(f"- 剩余空间：{_gb(disk.disk_free_gb)}")
        _print_items("原因：", disk.reasons, "暂无额外原因。")
        _print_items("建议：", disk.recommendations, "暂无额外建议。")

    paths = recommendation.model_path_recommendation
    if paths is not None:
        console.print("[bold]模型路径建议：[/bold]")
        _print_items("推荐模型目录：", paths.recommended_model_paths, "暂无推荐模型目录。")
        _print_items("推荐缓存目录：", paths.recommended_cache_paths, "暂无推荐缓存目录。")
        _print_items("避免作为默认目录：", paths.avoid_paths, "暂无避免目录。")
    console.print("")

    _print_items("配置建议：", recommendation.config_recommendations, "暂无额外配置建议。")
    console.print("")
    _print_items("当前不推荐事项：", recommendation.not_recommended, "暂无明显不推荐事项。")
    console.print("")
    _print_items("下一步：", recommendation.next_steps, "暂无下一步建议。")


@app.command("report")
def report_command(goal: Optional[str] = typer.Option(None, "--goal", "-g", help="模板 ID。")) -> None:
    """生成 Markdown 和 JSON 推荐报告。"""

    goal = _goal_or_exit(goal)
    try:
        md_path, json_path, recommendation = generate_report(goal)
    except UnknownTemplateError as exc:
        _unknown_template(exc)
    console.print(f"报告已生成：{recommendation.display_name}")
    console.print(str(md_path))
    console.print(str(json_path))


@app.command("doctor")
def doctor_command(goal: Optional[str] = typer.Option(None, "--goal", "-g", help="模板 ID。")) -> None:
    """检测电脑配置，生成推荐和报告。"""

    goal = _goal_or_exit(goal)
    try:
        template = load_template(goal)
    except UnknownTemplateError as exc:
        _unknown_template(exc)

    console.print("正在检测电脑配置...")
    profile = scan_system()
    console.print(f"正在生成推荐：{template.display_name}...")
    md_path, json_path, _ = generate_report(goal, profile=profile)
    console.print("报告已生成：")
    console.print(str(md_path))
    console.print(str(json_path))


@app.command("plan")
def plan_command(
    goal: Optional[str] = typer.Option(None, "--goal", "-g", help="Template ID."),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Plan output directory."),
) -> None:
    """Generate auditable install-plan artifacts without installing anything."""

    goal = _goal_or_exit(goal)
    try:
        template = load_template(goal)
    except UnknownTemplateError as exc:
        _unknown_template(exc)

    console.print("正在检测电脑配置...")
    profile = scan_system()
    console.print(f"正在生成推荐：{template.display_name}...")
    recommendation = recommend(goal, profile=profile)

    console.print("正在生成可审查安装计划...")
    install_plan = build_install_plan(profile, recommendation)
    audit_report = audit_install_plan(install_plan)
    snapshot_plan = build_snapshot_plan(install_plan)
    rollback_plan = build_rollback_plan(install_plan)
    dry_run_result = DryRunExecutor().run(install_plan)
    paths = write_plan_artifacts(
        output_dir,
        install_plan,
        audit_report,
        snapshot_plan,
        rollback_plan,
        dry_run_result,
    )

    console.print("安装计划已生成：")
    console.print(str(paths["install_plan_md"]))
    console.print(str(paths["install_plan_json"]))
    console.print("")
    console.print("审计报告已生成：")
    console.print(str(paths["install_audit_md"]))
    console.print(str(paths["install_audit_json"]))
    console.print("")
    console.print("备份、回滚和 dry-run 预览已生成：")
    console.print(str(paths["snapshot_plan_md"]))
    console.print(str(paths["rollback_plan_md"]))
    console.print(str(paths["dry_run_md"]))
    console.print("")
    console.print("当前版本只生成计划，不会自动安装软件或修改系统设置。")


@app.command("dry-run")
def dry_run_command(
    plan: Path = typer.Option(..., "--plan", help="Path to install-plan.json."),
) -> None:
    """Regenerate dry-run preview files from an InstallPlan JSON file."""

    if not plan.exists():
        console.print(f"[red]未找到安装计划：{plan}[/red]")
        raise typer.Exit(code=1)

    payload = json.loads(plan.read_text(encoding="utf-8"))
    install_plan = parse_model(InstallPlan, payload)
    dry_run_result = DryRunExecutor().run(install_plan)

    dry_run_md = plan.parent / "dry-run.md"
    dry_run_json = plan.parent / "dry-run.json"
    dry_run_md.write_text(render_dry_run_markdown(dry_run_result), encoding="utf-8")
    dry_run_json.write_text(
        json.dumps(render_dry_run_json(dry_run_result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    console.print("dry-run 预览已生成：")
    console.print(str(dry_run_md))
    console.print(str(dry_run_json))
    console.print("当前版本只生成预览，不会执行安装命令。")


def main() -> None:
    app()
