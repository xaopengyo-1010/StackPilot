from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .models import SystemProfile, TemplateRecommendation
from .recommender import recommend
from .report import generate_report
from .scanner import scan_system
from .templates import UnknownTemplateError, load_templates


app = typer.Typer(help="StackPilot environment blueprint generator.")
console = Console()


def _print_profile(profile: SystemProfile) -> None:
    table = Table(title="StackPilot System Scan")
    table.add_column("Field")
    table.add_column("Value")
    values = {
        "OS": f"{profile.os_name} {profile.os_version}",
        "Architecture": profile.architecture,
        "CPU": profile.cpu_name or "Not detected",
        "CPU cores": str(profile.cpu_cores) if profile.cpu_cores is not None else "Not detected",
        "RAM": f"{profile.total_ram_gb} GB" if profile.total_ram_gb is not None else "Not detected",
        "GPU": ", ".join(profile.gpu_names) if profile.gpu_names else "Not detected",
        "GPU VRAM": f"{profile.gpu_vram_gb} GB" if profile.gpu_vram_gb is not None else "Not detected",
        "Disk total": f"{profile.disk_total_gb} GB" if profile.disk_total_gb is not None else "Not detected",
        "Disk free": f"{profile.disk_free_gb} GB" if profile.disk_free_gb is not None else "Not detected",
        "Python": profile.python_version if profile.python_installed else "Not detected",
        "Node.js": profile.node_version if profile.node_installed else "Not detected",
        "Git": profile.git_version if profile.git_installed else "Not detected",
        "pnpm": profile.pnpm_version if profile.pnpm_installed else "Not detected",
        "Docker": profile.docker_version if profile.docker_installed else "Not detected",
        "WSL available": str(profile.wsl_available),
        "NVIDIA driver": profile.nvidia_driver_version or "Not detected",
    }
    for key, value in values.items():
        table.add_row(key, value)
    console.print(table)
    if profile.warnings:
        console.print("[yellow]Warnings[/yellow]")
        for warning in profile.warnings:
            console.print(f"- {warning}")


def _print_recommendation(recommendation: TemplateRecommendation) -> None:
    console.print(f"[bold]{recommendation.display_name}[/bold] ({recommendation.template_id})")
    console.print(f"Category: {recommendation.category}")
    console.print(f"Suitability score: {recommendation.suitability_score}/100")
    console.print(recommendation.summary)

    app_table = Table(title="Recommended Apps")
    app_table.add_column("App")
    app_table.add_column("Required")
    app_table.add_column("Reason")
    app_table.add_column("Source")
    for item in recommendation.recommended_apps:
        app_table.add_row(item.name, str(item.required), item.reason, item.official_source)
    console.print(app_table)

    sections = [
        ("Configuration Recommendations", recommendation.config_recommendations),
        ("Risk Warnings", recommendation.risk_warnings),
        ("Not Recommended", recommendation.not_recommended),
        ("Next Steps", recommendation.next_steps),
    ]
    for title, values in sections:
        console.print(f"[bold]{title}[/bold]")
        if values:
            for value in values:
                console.print(f"- {value}")
        else:
            console.print("- None")


def _available_template_text() -> str:
    return ", ".join(template.template_id for template in load_templates())


@app.command("scan")
def scan_command() -> None:
    """Scan public local system information."""
    _print_profile(scan_system())


@app.command("list-templates")
def list_templates_command() -> None:
    """List available recommendation templates."""
    table = Table(title="StackPilot Templates")
    table.add_column("Goal")
    table.add_column("Display name")
    table.add_column("Category")
    table.add_column("Description")
    for template in load_templates():
        table.add_row(template.template_id, template.display_name, template.category, template.description)
    console.print(table)


@app.command("recommend")
def recommend_command(goal: Optional[str] = typer.Option(None, "--goal", "-g", help="Template goal id.")) -> None:
    """Generate a recommendation for a selected goal."""
    if not goal:
        console.print("[red]Missing --goal.[/red] Run `python -m stackpilot list-templates` to see available goals.")
        raise typer.Exit(code=1)
    try:
        _print_recommendation(recommend(goal))
    except UnknownTemplateError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.command("report")
def report_command(goal: Optional[str] = typer.Option(None, "--goal", "-g", help="Template goal id.")) -> None:
    """Generate Markdown and JSON reports."""
    if not goal:
        console.print("[red]Missing --goal.[/red] Run `python -m stackpilot list-templates` to see available goals.")
        raise typer.Exit(code=1)
    try:
        md_path, json_path, recommendation = generate_report(goal)
    except UnknownTemplateError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"Generated report for [bold]{recommendation.template_id}[/bold]")
    console.print(f"- {md_path}")
    console.print(f"- {json_path}")


@app.command("doctor")
def doctor_command(goal: Optional[str] = typer.Option(None, "--goal", "-g", help="Template goal id.")) -> None:
    """Run scan, recommendation, and report generation."""
    if not goal:
        console.print("[red]Missing --goal.[/red] Run `python -m stackpilot list-templates` to see available goals.")
        raise typer.Exit(code=1)
    profile = scan_system()
    _print_profile(profile)
    try:
        recommendation = recommend(goal, profile=profile)
        _print_recommendation(recommendation)
        md_path, json_path, _ = generate_report(goal, profile=profile)
    except UnknownTemplateError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print("[bold]Report outputs[/bold]")
    console.print(f"- {md_path}")
    console.print(f"- {json_path}")


def main() -> None:
    app()
