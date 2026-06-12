from __future__ import annotations

from stackpilot.plans.models import InstallSource, RiskLevel


RISK_ORDER: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "blocked": 3,
}


def max_risk(*levels: str) -> RiskLevel:
    """Return the highest risk level from the supplied values."""

    highest = "low"
    for level in levels:
        if RISK_ORDER.get(level, 1) > RISK_ORDER[highest]:
            highest = level
    return highest  # type: ignore[return-value]


def source_base_risk(source: InstallSource) -> RiskLevel:
    """Classify source risk according to StackPilot trusted-source policy."""

    if source.type in {"winget", "microsoft_store"}:
        risk: RiskLevel = "low"
    elif source.type == "official_url":
        risk = "low" if source.trusted else "medium"
    elif source.type in {"github_release", "pypi", "npm", "docker_official", "manual"}:
        risk = "medium"
    else:
        risk = "blocked"

    if source.type == "unknown":
        return "blocked"
    if not source.trusted:
        return max_risk(risk, "medium")
    return risk

