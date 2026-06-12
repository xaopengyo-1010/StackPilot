from __future__ import annotations

from pydantic import BaseModel, Field

from stackpilot.plans.models import utc_now


class SnapshotPlan(BaseModel):
    """Plan-only description of what should be backed up before execution."""

    snapshot_id: str
    created_at: str = Field(default_factory=utc_now)
    items: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

