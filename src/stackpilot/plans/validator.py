from __future__ import annotations

from stackpilot.plans.models import AuditFinding, InstallPlan


def validate_install_plan(plan: InstallPlan) -> list[AuditFinding]:
    """Validate plan-level invariants that must stay true in v0.3."""

    findings: list[AuditFinding] = []
    if not plan.dry_run_only:
        findings.append(
            AuditFinding(
                id="plan.dry_run_only_false",
                level="blocked",
                title="Plan is not dry-run only",
                message="InstallPlan.dry_run_only must be true in StackPilot v0.3.",
                evidence={"dry_run_only": plan.dry_run_only},
            )
        )
    for step in plan.steps:
        if not step.audit_note.strip():
            findings.append(
                AuditFinding(
                    id=f"{step.id}.missing_audit_note",
                    level="warning",
                    title="Missing audit note",
                    message="Each install step must include a transparency audit note.",
                    related_step_id=step.id,
                    evidence={"app_id": step.app_id},
                )
            )
    return findings

