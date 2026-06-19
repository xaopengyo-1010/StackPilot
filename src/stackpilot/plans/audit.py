from __future__ import annotations

from stackpilot.plans.models import AuditFinding, InstallAuditReport, InstallPlan, utc_now
from stackpilot.plans.validator import validate_install_plan


def audit_install_plan(plan: InstallPlan) -> InstallAuditReport:
    """Generate a structured audit report for an install plan."""

    findings: list[AuditFinding] = [*validate_install_plan(plan)]
    blocked_step_ids: list[str] = []
    medium_high_step_ids: list[str] = []
    missing_rollback_step_ids: list[str] = []
    unknown_source_step_ids: list[str] = []

    for step in plan.steps:
        evidence = {
            "app_id": step.app_id,
            "source_type": step.source.type,
            "trusted": step.source.trusted,
            "risk_level": step.risk_level,
            "requires_admin": step.requires_admin,
        }
        if step.risk_level == "blocked":
            blocked_step_ids.append(step.id)
            findings.append(
                AuditFinding(
                    id=f"{step.id}.blocked",
                    level="blocked",
                    title="步骤被安全策略阻止",
                    message="该步骤被安全策略阻止，不能自动执行。",
                    related_step_id=step.id,
                    evidence=evidence,
                )
            )
        if step.risk_level in {"medium", "high", "blocked"}:
            medium_high_step_ids.append(step.id)
            findings.append(
                AuditFinding(
                    id=f"{step.id}.risk",
                    level="warning" if step.risk_level != "blocked" else "blocked",
                    title="步骤需要风险审查",
                    message="该步骤为 medium、high 或 blocked 风险，使用前必须先审查。",
                    related_step_id=step.id,
                    evidence=evidence,
                )
            )
        if not step.rollback_command:
            missing_rollback_step_ids.append(step.id)
            findings.append(
                AuditFinding(
                    id=f"{step.id}.rollback_missing",
                    level="warning",
                    title="缺少回滚命令",
                    message="该步骤没有明确的回滚命令。",
                    related_step_id=step.id,
                    evidence=evidence,
                )
            )
        if step.source.type == "unknown":
            unknown_source_step_ids.append(step.id)
            findings.append(
                AuditFinding(
                    id=f"{step.id}.source_unknown",
                    level="blocked",
                    title="未知来源",
                    message="未知来源会被阻止；执行前必须先补充应用目录元数据。",
                    related_step_id=step.id,
                    evidence=evidence,
                )
            )

    return InstallAuditReport(
        audit_id=f"audit-{plan.plan_id}-{utc_now()}",
        plan_id=plan.plan_id,
        findings=findings,
        blocked_step_ids=blocked_step_ids,
        medium_high_step_ids=medium_high_step_ids,
        missing_rollback_step_ids=missing_rollback_step_ids,
        unknown_source_step_ids=unknown_source_step_ids,
        policy_summary=[
            "v0.3 的所有 InstallPlan 都只能 dry-run。",
            "未知来源会被阻止。",
            "未标记可信的来源至少是 medium 风险。",
            "命中禁止 shell 模式的步骤会被阻止。",
            "缺少回滚命令会生成 warning。",
        ],
    )
