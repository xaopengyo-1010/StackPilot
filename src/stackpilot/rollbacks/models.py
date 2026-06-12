from __future__ import annotations

from pydantic import BaseModel, Field

from stackpilot.plans.models import utc_now


class RollbackPlan(BaseModel):
    """Plan-only rollback guidance for a generated install plan."""

    rollback_id: str
    created_at: str = Field(default_factory=utc_now)
    steps: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

