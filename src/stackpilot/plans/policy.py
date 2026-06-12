from __future__ import annotations

from stackpilot.plans.models import AuditFinding, InstallStep
from stackpilot.security.commands import review_command
from stackpilot.security.risk import max_risk, source_base_risk
from stackpilot.utils import unique_preserve_order


ROLLBACK_WARNING = (
    "该步骤没有明确的回滚命令。未来真实执行前，必须先人工确认回滚方式。"
)


def _sentence(value: str) -> str:
    """Return text with exactly one sentence-ending punctuation mark."""

    text = value.strip()
    if text.endswith(("。", "！", "？", ".", "!", "?")):
        return text
    return f"{text}。"


def build_audit_note(step: InstallStep) -> str:
    """Build the transparency note required for each install step."""

    source = step.source
    action_names = {
        "install": "安装",
        "configure": "配置",
        "verify": "验证",
        "manual": "人工处理",
    }
    verify = "、".join(step.verify_commands) if step.verify_commands else "需要人工验证"
    rollback = step.rollback_command or "需要人工确认回滚方式"
    admin = "需要管理员权限" if step.requires_admin else "不需要管理员权限"
    reason = _sentence(step.reason or "它属于当前选择的目标")
    return (
        f"计划{action_names.get(step.action, step.action)} {step.app_name}，原因：{reason}"
        f"来源：{source.type}（{source.name}）。该步骤{admin}。"
        f"验证方式：{verify}。回滚方式：{rollback}。"
        "这是计划文本，StackPilot v0.3 不会执行。"
    )


def apply_step_policy(step: InstallStep) -> tuple[InstallStep, list[AuditFinding]]:
    """Apply source, command, rollback, and transparency policy to a step."""

    findings: list[AuditFinding] = []
    step.risk_level = max_risk(step.risk_level, source_base_risk(step.source))

    if step.source.type == "unknown":
        step.risk_level = "blocked"
        findings.append(
            AuditFinding(
                id=f"{step.id}.unknown_source",
                level="blocked",
                title="未知安装来源",
                message="该来源未知，因此此步骤会被阻止，未来也不能自动执行。",
                related_step_id=step.id,
                evidence={"source_type": step.source.type, "trusted": step.source.trusted},
            )
        )
    elif step.source.trusted is False:
        step.risk_level = max_risk(step.risk_level, "medium")
        findings.append(
            AuditFinding(
                id=f"{step.id}.untrusted_source",
                level="warning",
                title="来源需要人工信任审查",
                message="该来源未标记为可信，风险等级至少提升到 medium。",
                related_step_id=step.id,
                evidence={"source_type": step.source.type, "trusted": step.source.trusted},
            )
        )

    reviewed_fields = [("command", step.command), ("rollback_command", step.rollback_command)]
    reviewed_fields.extend((f"verify_command:{index}", command) for index, command in enumerate(step.verify_commands))
    for field_name, command in reviewed_fields:
        review = review_command(command)
        if review.blocked:
            step.risk_level = "blocked"
            findings.append(
                AuditFinding(
                    id=f"{step.id}.{field_name}.blocked_command",
                    level="blocked",
                    title="命令包含禁止模式",
                    message=review.message,
                    related_step_id=step.id,
                    evidence={"field": field_name, "command": command},
                )
            )
        elif not review.allowed:
            step.risk_level = max_risk(step.risk_level, "medium")
            findings.append(
                AuditFinding(
                    id=f"{step.id}.{field_name}.manual_command_review",
                    level="warning",
                    title="命令需要人工审查",
                    message=review.message,
                    related_step_id=step.id,
                    evidence={"field": field_name, "command": command},
                )
            )

    if not step.rollback_command:
        step.risk_level = max_risk(step.risk_level, "medium")
        step.warnings = unique_preserve_order([*step.warnings, ROLLBACK_WARNING])
        findings.append(
            AuditFinding(
                id=f"{step.id}.missing_rollback",
                level="warning",
                title="缺少回滚命令",
                message=ROLLBACK_WARNING,
                related_step_id=step.id,
                evidence={"app_id": step.app_id},
            )
        )

    if not step.audit_note.strip():
        step.audit_note = build_audit_note(step)

    step.warnings = unique_preserve_order(step.warnings)
    return step, findings
