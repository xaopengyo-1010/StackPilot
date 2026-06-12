from __future__ import annotations

from abc import ABC, abstractmethod

from stackpilot.plans.models import InstallPlan


class PlanExecutor(ABC):
    """Base class for plan executors.

    v0.3 ships only a dry-run implementation. Real executors must keep the same
    audit boundary and must not be wired as a default path.
    """

    @abstractmethod
    def run(self, plan: InstallPlan):
        """Run or simulate a plan."""

