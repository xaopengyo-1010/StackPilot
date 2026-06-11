from __future__ import annotations

from . import detector
from .models import SystemProfile, TemplateDefinition
from .utils import clamp


def _effective_vram(profile: SystemProfile) -> float | None:
    if profile.gpu_vram_gb is not None:
        return profile.gpu_vram_gb
    return detector.infer_vram_from_names(profile.gpu_names)


def _os_matches(profile: SystemProfile, allowed: list[str]) -> bool:
    if not allowed:
        return True
    current = f"{profile.os_name} {profile.os_version}".casefold()
    return any(item.casefold() in current or profile.os_name.casefold() in item.casefold() for item in allowed)


def score_template(profile: SystemProfile, template: TemplateDefinition) -> float:
    score = 100.0
    requirements = template.requirements

    if requirements.min_ram_gb is not None:
        if profile.total_ram_gb is None:
            score -= 8
        elif profile.total_ram_gb < requirements.min_ram_gb:
            score -= 35
        elif requirements.recommended_ram_gb and profile.total_ram_gb < requirements.recommended_ram_gb:
            score -= 12

    vram = _effective_vram(profile)
    needs_vram = (
        (requirements.min_vram_gb is not None and requirements.min_vram_gb > 0)
        or (requirements.recommended_vram_gb is not None and requirements.recommended_vram_gb > 0)
    )
    if needs_vram:
        if not profile.gpu_names:
            score -= 30
        elif vram is None:
            score -= 12
        elif requirements.min_vram_gb is not None and vram < requirements.min_vram_gb:
            score -= 35
        elif requirements.recommended_vram_gb and vram < requirements.recommended_vram_gb:
            score -= 14

    if requirements.min_disk_free_gb is not None:
        if profile.disk_free_gb is None:
            score -= 5
        elif profile.disk_free_gb < requirements.min_disk_free_gb:
            score -= 20

    if not _os_matches(profile, requirements.os):
        score -= 10

    return round(clamp(score), 1)
