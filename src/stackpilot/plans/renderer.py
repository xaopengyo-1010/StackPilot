from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stackpilot.executors.dry_run import DryRunResult
from stackpilot.plans.models import InstallAuditReport, InstallPlan
from stackpilot.rollbacks.models import RollbackPlan
from stackpilot.snapshots.models import SnapshotPlan
from stackpilot.templates import project_root
from stackpilot.utils import model_to_dict


PLAN_NOTICE = "当前版本只生成可审查安装计划，不会自动安装软件或修改系统设置。"
DRY_RUN_NOTICE = "当前版本只生成可审查安装计划，不会自动执行安装。"
ROLLBACK_LIMIT_NOTICE = (
    "软件安装可能写入注册表、用户目录或缓存。StackPilot 可以规划回滚步骤，"
    "但不能保证 100% 完全恢复到安装前状态。"
)


def default_plan_output_dir() -> Path:
    """Return the default directory for v0.3 plan artifacts."""

    return project_root() / "outputs" / "plans"


def _safe(value: object | None) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, str) and not value.strip():
        return "未检测到"
    return str(value)


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "未检测到"
    return "是" if value else "否"


def _source_label(source_type: str) -> str:
    return {
        "winget": "winget",
        "microsoft_store": "Microsoft Store",
        "official_url": "官方网址",
        "github_release": "GitHub Release",
        "pypi": "PyPI",
        "npm": "npm",
        "docker_official": "Docker 官方镜像",
        "manual": "人工确认",
        "unknown": "未知来源",
    }.get(source_type, source_type)


def _list(values: list[Any], empty_text: str = "未检测到") -> str:
    if not values:
        return f"- {empty_text}"
    return "\n".join(f"- {_safe(value)}" for value in values)


def render_install_plan_markdown(plan: InstallPlan) -> str:
    """Render an install plan to Markdown."""

    hardware = "\n".join(f"- {key}: {_safe(value)}" for key, value in plan.hardware_summary.items())
    action_labels = {
        "install": "安装",
        "configure": "配置",
        "verify": "验证",
        "manual": "人工处理",
    }
    step_blocks = []
    for step in plan.steps:
        disk_mb = "未检测到" if step.estimated_disk_mb is None else f"{step.estimated_disk_mb} MB"
        step_blocks.append(
            f"""### {step.id} - {step.app_name}

- App ID: `{_safe(step.app_id)}`
- 操作: {action_labels.get(step.action, step.action)} (`{_safe(step.action)}`)
- 来源: {_source_label(step.source.type)} (`{_safe(step.source.type)}`) / {_safe(step.source.name)}
- 包 ID: `{_safe(step.source.package_id)}`
- 来源 URL: {_safe(step.source.url)}
- 来源可信: {_yes_no(step.source.trusted)}
- 风险等级: `{_safe(step.risk_level)}`
- 需要管理员权限: {_yes_no(step.requires_admin)}
- 预计磁盘占用: {disk_mb}
- 命令预览: `{_safe(step.command)}`
- 回滚命令预览: `{_safe(step.rollback_command)}`
- 验证命令: {_safe("、".join(step.verify_commands) if step.verify_commands else None)}
- 推荐原因: {_safe(step.reason)}
- 审计说明: {_safe(step.audit_note)}
- 前置确认:
{_list(step.preconditions)}
- 风险提醒:
{_list(step.warnings, "暂无额外提醒")}
"""
        )
    steps = "\n".join(step_blocks)
    blocked = "\n".join(f"- {step.id}: {step.app_name} (`{step.risk_level}`)" for step in plan.blocked_steps)
    return f"""# StackPilot 安装计划

## 总览

- 计划 ID: `{_safe(plan.plan_id)}`
- 目标: `{_safe(plan.goal_id)}` / {_safe(plan.goal_name)}
- 生成时间: {_safe(plan.created_at)}
- 仅 dry-run: `{_yes_no(plan.dry_run_only)}`

{PLAN_NOTICE}

## 硬件摘要

{hardware}

## 安装步骤

{steps if steps else "未检测到"}

## 阻止或高风险步骤

{blocked if blocked else "- 未检测到"}

## 备份建议

{_list(plan.backup_recommendations)}

## 回滚说明

{_safe(plan.rollback_summary)}

## 风险提醒

{_list(plan.warnings, "暂无额外提醒")}

## 说明

{DRY_RUN_NOTICE}
{ROLLBACK_LIMIT_NOTICE}
"""


def render_install_plan_json(plan: InstallPlan) -> dict[str, Any]:
    """Render an install plan to JSON-compatible data."""

    return model_to_dict(plan)


def render_audit_markdown(report: InstallAuditReport, plan: InstallPlan) -> str:
    """Render a plan audit report to Markdown."""

    blocked_steps = [step for step in plan.steps if step.id in report.blocked_step_ids]
    missing_rollback = [step for step in plan.steps if step.id in report.missing_rollback_step_ids]
    manual_steps = [
        step
        for step in plan.steps
        if step.action == "manual" or step.risk_level in {"medium", "high", "blocked"}
    ]
    finding_lines = [
        f"`{finding.level}` {finding.id}：{finding.title} - {finding.message}"
        for finding in report.findings
    ]
    step_audit = [
        f"{step.id} / {step.app_name}：来源={_source_label(step.source.type)}，风险={step.risk_level}，可信={_yes_no(step.source.trusted)}"
        for step in plan.steps
    ]
    return f"""# StackPilot 安装计划审计报告

## 总览

- 审计 ID: `{_safe(report.audit_id)}`
- 计划 ID: `{_safe(report.plan_id)}`
- 生成时间: {_safe(report.generated_at)}
- 步骤数: {len(plan.steps)}
- 阻止步骤数: {len(report.blocked_step_ids)}

## 安全策略

{_list(report.policy_summary)}

## 安装步骤审计

{_list(step_audit)}

## 阻止执行的步骤

{_list([f"{step.id}: {step.app_name}" for step in blocked_steps], "未检测到")}

## 缺少回滚信息的步骤

{_list([f"{step.id}: {step.app_name}" for step in missing_rollback], "未检测到")}

## 需要人工确认的步骤

{_list([f"{step.id}: {step.app_name} ({step.risk_level})" for step in manual_steps], "未检测到")}

## 备份建议

{_list(plan.backup_recommendations)}

## 回滚限制

{ROLLBACK_LIMIT_NOTICE}

## 发现列表

{_list(finding_lines, "未检测到")}

## 说明

{PLAN_NOTICE}
本报告用于降低风险，不表示风险已经被消除。
"""


def render_audit_json(report: InstallAuditReport) -> dict[str, Any]:
    """Render an audit report to JSON-compatible data."""

    return model_to_dict(report)


def render_snapshot_plan_markdown(plan: SnapshotPlan) -> str:
    """Render a snapshot plan to Markdown."""

    return f"""# StackPilot 备份 / 快照计划

## 建议备份内容

{_list(plan.items)}

## 为什么需要备份

- 安装和配置软件可能影响 PATH、环境变量、配置文件和软件列表。
- 备份记录可以帮助后续人工审查和回滚，降低风险。

## 当前版本说明

当前版本只生成备份计划，不会创建真实系统还原点。

## 备注

{_list(plan.notes)}
"""


def render_rollback_plan_markdown(plan: RollbackPlan) -> str:
    """Render a rollback plan to Markdown."""

    manual_steps = [step for step in plan.steps if "manual" in step.casefold() or "人工" in step]
    automatic_steps = [step for step in plan.steps if step not in manual_steps]
    return f"""# StackPilot 回滚计划

## 可自动规划的回滚步骤

{_list(automatic_steps)}

## 需要人工确认的回滚步骤

{_list(manual_steps, "未检测到")}

## 无法保证完全恢复的部分

{_list(plan.limitations)}

## 当前版本说明

{ROLLBACK_LIMIT_NOTICE}
StackPilot v0.3 只生成回滚计划，不执行真实回滚。

## 备注

{_list(plan.notes)}
"""


def render_dry_run_markdown(result: DryRunResult) -> str:
    """Render dry-run output to Markdown."""

    lines = [
        f"{step.step_id} / {step.app_name}：would_run={step.would_run}, "
        f"skipped={step.skipped}, skip_reason={_safe(step.skip_reason)}, "
        f"risk={step.risk_level}, command=`{_safe(step.planned_command)}`"
        for step in result.steps
    ]
    return f"""# StackPilot Dry-run 预览

## 总览

- 计划 ID: `{_safe(result.plan_id)}`
- 生成时间: {_safe(result.generated_at)}
- 仅 dry-run: `{_yes_no(result.dry_run_only)}`

{DRY_RUN_NOTICE}

## 步骤预览

{_list(lines, "未检测到")}
"""


def render_snapshot_plan_json(plan: SnapshotPlan) -> dict[str, Any]:
    return model_to_dict(plan)


def render_rollback_plan_json(plan: RollbackPlan) -> dict[str, Any]:
    return model_to_dict(plan)


def render_dry_run_json(result: DryRunResult) -> dict[str, Any]:
    return model_to_dict(result)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_plan_artifacts(
    output_dir: str | Path | None,
    plan: InstallPlan,
    audit_report: InstallAuditReport,
    snapshot_plan: SnapshotPlan,
    rollback_plan: RollbackPlan,
    dry_run_result: DryRunResult,
) -> dict[str, Path]:
    """Write all v0.3 plan artifacts and return their paths."""

    target_dir = Path(output_dir) if output_dir is not None else default_plan_output_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "install_plan_md": target_dir / "install-plan.md",
        "install_plan_json": target_dir / "install-plan.json",
        "install_audit_md": target_dir / "install-audit.md",
        "install_audit_json": target_dir / "install-audit.json",
        "snapshot_plan_md": target_dir / "snapshot-plan.md",
        "snapshot_plan_json": target_dir / "snapshot-plan.json",
        "rollback_plan_md": target_dir / "rollback-plan.md",
        "rollback_plan_json": target_dir / "rollback-plan.json",
        "dry_run_md": target_dir / "dry-run.md",
        "dry_run_json": target_dir / "dry-run.json",
    }

    paths["install_plan_md"].write_text(render_install_plan_markdown(plan), encoding="utf-8")
    _write_json(paths["install_plan_json"], render_install_plan_json(plan))
    paths["install_audit_md"].write_text(render_audit_markdown(audit_report, plan), encoding="utf-8")
    _write_json(paths["install_audit_json"], render_audit_json(audit_report))
    paths["snapshot_plan_md"].write_text(render_snapshot_plan_markdown(snapshot_plan), encoding="utf-8")
    _write_json(paths["snapshot_plan_json"], render_snapshot_plan_json(snapshot_plan))
    paths["rollback_plan_md"].write_text(render_rollback_plan_markdown(rollback_plan), encoding="utf-8")
    _write_json(paths["rollback_plan_json"], render_rollback_plan_json(rollback_plan))
    paths["dry_run_md"].write_text(render_dry_run_markdown(dry_run_result), encoding="utf-8")
    _write_json(paths["dry_run_json"], render_dry_run_json(dry_run_result))
    return paths
