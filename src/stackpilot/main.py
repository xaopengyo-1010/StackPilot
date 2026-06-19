from __future__ import annotations

from typing import Any

from .detector import StackPilotDetector
from .recommender import StackPilotRecommender


def run_pipeline(goal: str = "comfyui_starter") -> dict[str, Any]:
    raw_specs = StackPilotDetector().scan_system()
    return StackPilotRecommender().evaluate(raw_specs, goal=goal)
