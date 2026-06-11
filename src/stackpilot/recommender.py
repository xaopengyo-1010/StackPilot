from __future__ import annotations

from . import detector
from .models import AppRecommendation, SystemProfile, TemplateRecommendation
from .scanner import scan_system
from .scorer import score_template
from .templates import load_app_catalog, load_template


TOOL_STATUS = {
    "python": ("python_installed", "Python"),
    "git": ("git_installed", "Git"),
    "nodejs": ("node_installed", "Node.js"),
    "pnpm": ("pnpm_installed", "pnpm"),
    "docker_desktop": ("docker_installed", "Docker"),
}


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = value.strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _effective_vram(profile: SystemProfile) -> tuple[float | None, bool]:
    if profile.gpu_vram_gb is not None:
        return profile.gpu_vram_gb, False
    inferred = detector.infer_vram_from_names(profile.gpu_names)
    return inferred, inferred is not None


def _ram_notes(profile: SystemProfile, template_id: str, category: str) -> tuple[list[str], list[str], list[str]]:
    config: list[str] = []
    risks: list[str] = []
    not_recommended: list[str] = []
    ram = profile.total_ram_gb
    heavy_ai = category == "AI" or template_id in {"comfyui_starter", "local_llm"}

    if ram is None:
        risks.append("RAM could not be detected, so memory suitability is estimated conservatively.")
    elif ram < 8:
        config.append("Use lightweight templates and close memory-heavy apps before setup work.")
        risks.append("This PC has less than 8GB RAM; AI, ComfyUI, local LLM, and creator workflows are likely constrained.")
        if heavy_ai:
            not_recommended.append("Heavy AI or ComfyUI workflows on systems with less than 8GB RAM.")
    elif ram < 16:
        config.append("This RAM level is best suited for coding, light gaming, and lightweight AI experiments.")
        if heavy_ai:
            risks.append("ComfyUI or local AI should use lightweight workflows at this RAM level.")
    elif ram < 32:
        config.append("This RAM level is suitable for coding, creator entry workflows, ComfyUI Starter, and local 7B model experiments.")
    elif ram < 64:
        config.append("This RAM level can support more complete AI, coding, creator, and multitasking workflows.")
    else:
        config.append("This RAM level is suitable for heavier multitasking, creator work, and AI workstation-style workflows.")

    return config, risks, not_recommended


def _gpu_notes(profile: SystemProfile, template_id: str, category: str) -> tuple[list[str], list[str], list[str]]:
    config: list[str] = []
    risks: list[str] = []
    not_recommended: list[str] = []
    gpu_names = profile.gpu_names
    vram, inferred = _effective_vram(profile)
    gpu_sensitive = category in {"AI", "Gaming"} or template_id == "minecraft_realism"

    if not gpu_names and gpu_sensitive:
        risks.append("No discrete GPU was detected; recommendations are limited to lightweight or basic configurations.")
        if category == "AI":
            not_recommended.append("GPU-heavy AI image generation or local LLM workloads.")
        if template_id == "minecraft_realism":
            config.append("Use Sodium + Iris with lightweight shader presets and avoid heavy Distant Horizons settings.")
        return config, risks, not_recommended

    if inferred:
        risks.append("VRAM could not be detected directly; StackPilot made a weak estimate from the GPU name.")
    elif gpu_names and vram is None:
        risks.append("VRAM could not be detected.")

    if any("nvidia" in name.casefold() for name in gpu_names) and not profile.nvidia_driver_version:
        risks.append("NVIDIA GPU detected, but the NVIDIA driver version could not be detected.")

    if category == "AI" or template_id in {"comfyui_starter", "local_llm"}:
        if vram is None:
            risks.append("AI suitability is uncertain because VRAM is unknown.")
        elif vram < 6:
            risks.append("Less than 6GB VRAM is not recommended for heavy ComfyUI or local LLM workloads.")
            not_recommended.append("Heavy image generation, video generation, or larger local models.")
        elif vram < 8:
            config.append("Use lightweight ComfyUI workflows and smaller models.")
        elif vram < 12:
            config.append("Standard ComfyUI workflows should be reasonable; avoid very large batches or high-resolution generation.")
        elif vram < 24:
            config.append("This GPU can support a more complete local AI workflow with careful model choices.")
        else:
            config.append("This VRAM level is suitable for advanced local AI workstation workflows.")

    if template_id == "minecraft_realism":
        if vram is None or vram < 4:
            config.append("Low preset: Sodium + Iris + Complementary Reimagined Lite, low or medium textures, no heavy Distant Horizons.")
        elif vram < 8:
            config.append("Medium preset: Photon or Complementary Reimagined, low or medium textures, conservative Distant Horizons settings.")
        elif vram < 16:
            config.append("High preset: Rethinking Voxels or Photon, Distant Horizons enabled carefully, medium or high textures.")
        else:
            config.append("Ultra preset: SEUS PTGI GFME, Photon, or Rethinking Voxels with high-resolution textures and carefully tuned Distant Horizons.")

    if category == "Gaming" and vram is not None and vram < 4:
        risks.append("Low VRAM limits modern gaming presets; prefer basic settings and performance overlays only when needed.")

    return config, risks, not_recommended


def _tool_notes(profile: SystemProfile, app_ids: list[str]) -> list[str]:
    risks: list[str] = []
    for app_id in app_ids:
        status = TOOL_STATUS.get(app_id)
        if status is None:
            continue
        attr, name = status
        if not getattr(profile, attr):
            risks.append(f"{name} was not detected; install it manually from its official source if this workflow requires it.")
    if "wsl2_ubuntu" in app_ids and not profile.wsl_available:
        risks.append("WSL was not detected; Windows Linux workflows may need manual WSL setup.")
    return risks


def recommend(goal: str, profile: SystemProfile | None = None) -> TemplateRecommendation:
    profile = profile or scan_system()
    template = load_template(goal)
    catalog = load_app_catalog()

    recommended_apps: list[AppRecommendation] = []
    app_ids: list[str] = []
    for template_app in template.apps:
        app_ids.append(template_app.app_id)
        catalog_item = catalog.get(template_app.app_id)
        if catalog_item is None:
            recommended_apps.append(
                AppRecommendation(
                    app_id=template_app.app_id,
                    name=template_app.app_id,
                    required=template_app.required,
                    category="Unknown",
                    reason=template_app.reason,
                    install_method="Manual install from official source",
                    official_source="Unknown",
                    config_notes=[],
                    risk_notes=["This app is referenced by a template but is missing from app_catalog.json."],
                )
            )
            continue

        recommended_apps.append(
            AppRecommendation(
                app_id=catalog_item.app_id,
                name=catalog_item.name,
                required=template_app.required,
                category=catalog_item.category,
                reason=template_app.reason,
                install_method=catalog_item.install_methods[0] if catalog_item.install_methods else "Manual install",
                official_source=catalog_item.official_source,
                config_notes=catalog_item.config_notes,
                risk_notes=catalog_item.risk_notes,
            )
        )

    ram_config, ram_risks, ram_not_recommended = _ram_notes(profile, template.template_id, template.category)
    gpu_config, gpu_risks, gpu_not_recommended = _gpu_notes(profile, template.template_id, template.category)
    tool_risks = _tool_notes(profile, app_ids)

    return TemplateRecommendation(
        template_id=template.template_id,
        name=template.name,
        category=template.category,
        suitability_score=score_template(profile, template),
        summary=template.description,
        recommended_apps=recommended_apps,
        config_recommendations=_unique([*template.config_recommendations, *ram_config, *gpu_config]),
        risk_warnings=_unique([*template.risk_warnings, *profile.warnings, *ram_risks, *gpu_risks, *tool_risks]),
        not_recommended=_unique([*template.not_recommended, *ram_not_recommended, *gpu_not_recommended]),
        next_steps=_unique(template.next_steps),
    )
