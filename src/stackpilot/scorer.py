from __future__ import annotations

from .models import HardwareProfile, RuleFinding, TemplateDefinition
from .rules.engine import evaluate_rules
from .utils import clamp


FINDING_DEDUCTIONS = {
    "critical": 25,
    "warning": 10,
    "info": 0,
}


def score_template(
    profile: HardwareProfile,
    template: TemplateDefinition,
    findings: list[RuleFinding] | None = None,
) -> float:
    """Calculate suitability from structured rule findings."""

    rule_findings = findings if findings is not None else evaluate_rules(profile, template)
    score = 100.0
    for finding in rule_findings:
        score -= FINDING_DEDUCTIONS[finding.level]
    return round(clamp(score), 1)
