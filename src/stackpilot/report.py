from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import SystemProfile, TemplateRecommendation
from .recommender import recommend
from .scanner import scan_system
from .templates import project_root
from .utils import model_to_dict


REPORT_MD = "stackpilot-report.md"
REPORT_JSON = "stackpilot-report.json"

TRANSPARENCY_EN = (
    "StackPilot v0.1 does not download, install, modify, clean, optimize, "
    "or monitor your system automatically.\n"
    "It only generates an environment blueprint and recommendation report."
)

TRANSPARENCY_ZH = (
    "StackPilot v0.1 不会自动下载、安装、修改、清理、优化或监控你的系统。\n"
    "它只生成环境蓝图和推荐报告。"
)


def default_output_dir() -> Path:
    return project_root() / "outputs" / "reports"


def _format_list(values: list[str]) -> str:
    if not values:
        return "- None"
    return "\n".join(f"- {value}" for value in values)


def _format_apps(recommendation: TemplateRecommendation) -> str:
    if not recommendation.recommended_apps:
        return "- None"
    lines: list[str] = []
    for app in recommendation.recommended_apps:
        required = "required" if app.required else "optional"
        lines.append(f"- **{app.name}** (`{app.app_id}`, {required}) - {app.reason}")
        lines.append(f"  - Source: {app.official_source}")
        lines.append(f"  - Install method: {app.install_method}")
        if app.config_notes:
            lines.append(f"  - Notes: {'; '.join(app.config_notes)}")
        if app.risk_notes:
            lines.append(f"  - Risks: {'; '.join(app.risk_notes)}")
    return "\n".join(lines)


def _markdown(profile: SystemProfile, recommendation: TemplateRecommendation) -> str:
    gpu_names = ", ".join(profile.gpu_names) if profile.gpu_names else "Not detected"
    return f"""# StackPilot Environment Blueprint Report

## 1. System Summary

- OS: {profile.os_name} {profile.os_version}
- Architecture: {profile.architecture}
- CPU: {profile.cpu_name or "Not detected"}
- CPU cores: {profile.cpu_cores if profile.cpu_cores is not None else "Not detected"}
- RAM: {profile.total_ram_gb if profile.total_ram_gb is not None else "Not detected"} GB
- GPU: {gpu_names}
- GPU VRAM: {profile.gpu_vram_gb if profile.gpu_vram_gb is not None else "Not detected"} GB
- Disk total: {profile.disk_total_gb if profile.disk_total_gb is not None else "Not detected"} GB
- Disk free: {profile.disk_free_gb if profile.disk_free_gb is not None else "Not detected"} GB
- Python: {profile.python_version if profile.python_installed else "Not detected"}
- Node.js: {profile.node_version if profile.node_installed else "Not detected"}
- Git: {profile.git_version if profile.git_installed else "Not detected"}
- pnpm: {profile.pnpm_version if profile.pnpm_installed else "Not detected"}
- Docker: {profile.docker_version if profile.docker_installed else "Not detected"}
- WSL available: {profile.wsl_available}
- NVIDIA driver: {profile.nvidia_driver_version or "Not detected"}

## 2. Selected Goal

- Goal: `{recommendation.template_id}`
- Display name: {recommendation.display_name}
- Category: {recommendation.category}

## 3. Suitability Score

{recommendation.suitability_score}/100

## 4. Recommended Template

{recommendation.summary}

## 5. Recommended Apps

{_format_apps(recommendation)}

## 6. Configuration Recommendations

{_format_list(recommendation.config_recommendations)}

## 7. Risk Warnings

{_format_list(recommendation.risk_warnings)}

## 8. Not Recommended For This PC

{_format_list(recommendation.not_recommended)}

## 9. Next Steps

{_format_list(recommendation.next_steps)}

## 10. Transparency Notice

{TRANSPARENCY_EN}

{TRANSPARENCY_ZH}
"""


def generate_report(
    goal: str,
    output_dir: str | Path | None = None,
    profile: SystemProfile | None = None,
) -> tuple[Path, Path, TemplateRecommendation]:
    profile = profile or scan_system()
    recommendation = recommend(goal, profile=profile)
    target_dir = Path(output_dir) if output_dir is not None else default_output_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    md_path = target_dir / REPORT_MD
    json_path = target_dir / REPORT_JSON

    md_path.write_text(_markdown(profile, recommendation), encoding="utf-8")
    json_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": model_to_dict(profile),
        "recommendation": model_to_dict(recommendation),
        "transparency_notice": {
            "en": TRANSPARENCY_EN,
            "zh": TRANSPARENCY_ZH,
        },
    }
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path, recommendation
