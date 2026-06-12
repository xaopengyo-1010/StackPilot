from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal[
    "winget",
    "microsoft_store",
    "official_url",
    "github_release",
    "pypi",
    "npm",
    "docker_official",
    "manual",
    "unknown",
]
StepAction = Literal["install", "configure", "verify", "manual"]
RiskLevel = Literal["low", "medium", "high", "blocked"]
FindingLevel = Literal["info", "warning", "critical", "blocked"]


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp for generated plan artifacts."""

    return datetime.now(timezone.utc).isoformat()


def default_source_trust(source_type: str, url: str | None = None) -> bool:
    """Return the conservative default trust setting for an install source."""

    if source_type in {"winget", "microsoft_store"}:
        return True
    if source_type in {"official_url", "github_release"}:
        return bool(url and url.strip())
    if source_type in {"pypi", "npm", "docker_official"}:
        return True
    return False


class InstallSource(BaseModel):
    """Structured source metadata for a planned installation step."""

    type: SourceType = "unknown"
    name: str = "unknown"
    url: str | None = None
    package_id: str | None = None
    trusted: bool | None = None
    notes: list[str] = Field(default_factory=list)

    def __init__(self, **data):
        source_type = data.get("type") or "unknown"
        if data.get("trusted") is None:
            data["trusted"] = default_source_trust(source_type, data.get("url"))
        if source_type == "unknown":
            data["trusted"] = False
        super().__init__(**data)


class InstallStep(BaseModel):
    """A single auditable step in an install plan.

    Commands in this model are plan text only. They are rendered for review and
    dry-run output, but this package does not execute them.
    """

    id: str
    app_id: str
    app_name: str
    action: StepAction = "install"
    source: InstallSource = Field(default_factory=InstallSource)
    command: str | None = None
    requires_admin: bool = False
    risk_level: RiskLevel = "medium"
    reason: str = ""
    audit_note: str = ""
    estimated_disk_mb: int | None = None
    rollback_command: str | None = None
    verify_commands: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class InstallPlan(BaseModel):
    """A complete dry-run-only installation plan."""

    plan_id: str
    goal_id: str
    goal_name: str
    created_at: str = Field(default_factory=utc_now)
    hardware_summary: dict[str, object] = Field(default_factory=dict)
    steps: list[InstallStep] = Field(default_factory=list)
    blocked_steps: list[InstallStep] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    backup_recommendations: list[str] = Field(default_factory=list)
    rollback_summary: str = (
        "软件安装可能留下文件、注册表项、缓存或用户数据。"
        "StackPilot 可以规划回滚步骤，但不能保证 100% 完全恢复。"
    )
    dry_run_only: bool = True

    def __init__(self, **data):
        data["dry_run_only"] = True
        super().__init__(**data)


class AuditFinding(BaseModel):
    """A structured audit finding linked to a plan or step."""

    id: str
    level: FindingLevel
    title: str
    message: str
    related_step_id: str | None = None
    evidence: dict[str, object | None] = Field(default_factory=dict)


class InstallAuditReport(BaseModel):
    """Structured audit report for an ``InstallPlan``."""

    audit_id: str
    plan_id: str
    generated_at: str = Field(default_factory=utc_now)
    findings: list[AuditFinding] = Field(default_factory=list)
    blocked_step_ids: list[str] = Field(default_factory=list)
    medium_high_step_ids: list[str] = Field(default_factory=list)
    missing_rollback_step_ids: list[str] = Field(default_factory=list)
    unknown_source_step_ids: list[str] = Field(default_factory=list)
    policy_summary: list[str] = Field(default_factory=list)
