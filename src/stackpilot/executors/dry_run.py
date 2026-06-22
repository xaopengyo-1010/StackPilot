from __future__ import annotations

from pydantic import BaseModel, Field

from stackpilot.executors.base import PlanExecutor
from stackpilot.plans.models import InstallPlan, utc_now
from stackpilot.security.commands import is_manual_plan_text, review_command
from stackpilot.security.risk import max_risk


class DryRunStepResult(BaseModel):
    """Dry-run result for one install step."""

    step_id: str
    app_name: str
    planned_command: str | None = None
    would_run: bool = False
    skipped: bool = False
    skip_reason: str | None = None
    risk_level: str


class DryRunResult(BaseModel):
    """Dry-run result for an install plan."""

    plan_id: str
    generated_at: str = Field(default_factory=utc_now)
    dry_run_only: bool = True
    steps: list[DryRunStepResult] = Field(default_factory=list)


class DryRunExecutor(PlanExecutor):
    """Executor safety shell that never executes planned commands."""

    def run(self, plan: InstallPlan) -> DryRunResult:
        """Return what would be considered for execution without running it."""

        results: list[DryRunStepResult] = []
        for step in plan.steps:
            reviewed_commands = [("command", step.command), ("rollback_command", step.rollback_command)]
            reviewed_commands.extend(
                (f"verify_command:{index}", command) for index, command in enumerate(step.verify_commands)
            )
            command_reviews = [(field, review_command(command)) for field, command in reviewed_commands]
            blocked_review = next((item for item in command_reviews if item[1].blocked), None)
            manual_review = next((item for item in command_reviews if not item[1].allowed), None)

            if step.risk_level == "blocked":
                results.append(
                    DryRunStepResult(
                        step_id=step.id,
                        app_name=step.app_name,
                        planned_command=step.command,
                        would_run=False,
                        skipped=True,
                        skip_reason="已被安全策略阻止",
                        risk_level=step.risk_level,
                    )
                )
                continue
            if blocked_review is not None:
                results.append(
                    DryRunStepResult(
                        step_id=step.id,
                        app_name=step.app_name,
                        planned_command=step.command,
                        would_run=False,
                        skipped=True,
                        skip_reason=f"{blocked_review[0]} blocked by command safety policy",
                        risk_level="blocked",
                    )
                )
                continue
            if manual_review is not None:
                results.append(
                    DryRunStepResult(
                        step_id=step.id,
                        app_name=step.app_name,
                        planned_command=step.command,
                        would_run=False,
                        skipped=True,
                        skip_reason=f"{manual_review[0]} requires manual command review",
                        risk_level=max_risk(step.risk_level, "medium"),
                    )
                )
                continue
            if is_manual_plan_text(step.command):
                results.append(
                    DryRunStepResult(
                        step_id=step.id,
                        app_name=step.app_name,
                        planned_command=step.command,
                        would_run=False,
                        skipped=True,
                        skip_reason="需要人工审查",
                        risk_level=step.risk_level,
                    )
                )
                continue
            results.append(
                DryRunStepResult(
                    step_id=step.id,
                    app_name=step.app_name,
                    planned_command=step.command,
                    would_run=bool(step.command),
                    skipped=not bool(step.command),
                    skip_reason=None if step.command else "没有计划命令",
                    risk_level=step.risk_level,
                )
            )
        return DryRunResult(plan_id=plan.plan_id, steps=results, dry_run_only=True)
