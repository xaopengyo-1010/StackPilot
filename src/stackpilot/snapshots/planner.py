from __future__ import annotations

from stackpilot.plans.models import InstallPlan, utc_now
from stackpilot.snapshots.models import SnapshotPlan


DEFAULT_SNAPSHOT_ITEMS = [
    "PATH 环境变量",
    "用户级环境变量",
    "系统级环境变量",
    "已安装软件列表",
    "StackPilot 安装计划",
    "StackPilot dry-run 和执行日志",
    "关键配置文件路径",
]


def build_snapshot_plan(install_plan: InstallPlan | None = None) -> SnapshotPlan:
    """Build a snapshot plan without creating a real restore point or backup."""

    notes = [
        "StackPilot v0.3 只生成备份 / 快照计划，不会创建真实系统还原点。",
        "在任何执行器修改电脑前，都应先人工审查快照计划。",
    ]
    if install_plan is not None:
        notes.append(f"Related install plan: {install_plan.plan_id}")
    return SnapshotPlan(
        snapshot_id=f"snapshot-{install_plan.plan_id if install_plan else utc_now()}",
        items=[*DEFAULT_SNAPSHOT_ITEMS],
        notes=notes,
    )
