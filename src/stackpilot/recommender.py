from __future__ import annotations

from .models import AppRecommendation, HardwareProfile, RecommendationResult
from .rules.engine import evaluate_rules, findings_to_not_recommended, findings_to_warnings
from .scanner import scan_system
from .scorer import score_template
from .templates import load_app_catalog, load_template


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


def _is_nvidia_profile(profile: HardwareProfile) -> bool:
    return any("nvidia" in name.casefold() for name in profile.gpu_names)


def recommend(goal: str, profile: HardwareProfile | None = None) -> RecommendationResult:
    """Build a structured recommendation for a goal.

    Recommender combines template data, app catalog entries, hardware facts, and
    centralized rule findings. It does not print terminal output, write files,
    render Markdown, or scan the system directly unless no profile is supplied.
    """

    profile = profile or scan_system()
    template = load_template(goal)
    catalog = load_app_catalog()
    findings = evaluate_rules(profile, template)

    recommended_apps: list[AppRecommendation] = []
    for template_app in template.apps:
        required = template_app.required
        reason = template_app.reason
        if template_app.app_id == "nvidia_app" and not _is_nvidia_profile(profile):
            required = False
            reason = f"{reason} 未检测到 NVIDIA 显卡，因此这个项目可以跳过。"

        catalog_item = catalog.get(template_app.app_id)
        if catalog_item is None:
            recommended_apps.append(
                AppRecommendation(
                    app_id=template_app.app_id,
                    name=template_app.app_id,
                    required=required,
                    category="未知",
                    reason=reason,
                    install_method="从官方来源手动安装",
                    official_source="未知",
                    config_notes=[],
                    risk_notes=["模板引用了这个应用，但 app_catalog.json 中缺少对应条目。"],
                )
            )
            continue

        recommended_apps.append(
            AppRecommendation(
                app_id=catalog_item.app_id,
                name=catalog_item.name,
                required=required,
                category=catalog_item.category,
                reason=reason,
                install_method=catalog_item.install_methods[0] if catalog_item.install_methods else "手动安装",
                official_source=catalog_item.official_source,
                config_notes=catalog_item.config_notes,
                risk_notes=catalog_item.risk_notes,
            )
        )

    return RecommendationResult(
        template_id=template.template_id,
        display_name=template.display_name,
        name=template.display_name,
        category=template.category,
        suitability_score=score_template(profile, template, findings),
        summary=template.description,
        recommended_apps=recommended_apps,
        findings=findings,
        config_recommendations=_unique(template.config_recommendations),
        risk_warnings=_unique(findings_to_warnings(findings)),
        not_recommended=_unique([*template.not_recommended, *findings_to_not_recommended(findings)]),
        next_steps=_unique(template.next_steps),
    )
