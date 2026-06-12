from __future__ import annotations

from stackpilot.plans.models import InstallPlan, utc_now
from stackpilot.rollbacks.models import RollbackPlan


def build_rollback_plan(install_plan: InstallPlan | None = None) -> RollbackPlan:
    """Build rollback guidance without executing any uninstall or restore action."""

    steps = [
        "审查安装日志和 dry-run 输出。",
        "对有明确回滚命令的应用，按安装计划的相反顺序卸载。",
        "从已审查的快照中恢复 PATH。",
        "从已审查的快照中恢复用户级和系统级环境变量。",
        "按需恢复已经备份的配置文件。",
        "如果用户在 StackPilot 之外创建过系统还原点，再人工审查 Windows 系统还原选项。",
    ]
    if install_plan is not None:
        for step in reversed(install_plan.steps):
            if step.rollback_command:
                steps.append(f"{step.app_name}：计划中的回滚命令预览：{step.rollback_command}")
            else:
                steps.append(f"{step.app_name}：需要人工确认回滚方式；当前没有计划命令。")

    return RollbackPlan(
        rollback_id=f"rollback-{install_plan.plan_id if install_plan else utc_now()}",
        steps=steps,
        limitations=[
            "软件安装可能写入注册表项、用户数据、缓存、驱动和后台服务。",
            "StackPilot 可以规划回滚步骤，但不能保证 100% 完全恢复。",
            "缺少明确回滚元数据的应用必须人工确认。",
        ],
        notes=[
            "该回滚计划只提供审计指引。",
            "StackPilot v0.3 不会卸载软件、编辑 PATH、修改环境变量或恢复文件。",
        ],
    )
