from __future__ import annotations

import sys

import build
from stackpilot import main as tui
from stackpilot import reporter
from stackpilot.templates import config_dir


def sample_evaluation() -> dict:
    return {
        "hardware_summary": {
            "os": {"name": "Windows", "version": "11", "architecture": "x86_64"},
            "cpu": {"name": "Test CPU", "cores": 8},
            "memory": {"ram_gb": 32, "total_ram_gb": 32},
            "disk": {"anchor": "C:\\", "total_gb": 512, "free_gb": 128},
            "gpus": [
                {
                    "name": "NVIDIA GeForce RTX 4070",
                    "gpu_type": "dedicated",
                    "vram_confidence": "detected",
                }
            ],
            "primary_gpu": {
                "name": "NVIDIA GeForce RTX 4070",
                "gpu_type": "dedicated",
                "vram_confidence": "detected",
            },
            "tools": {
                "python": {"installed": True, "version": "3.11.9"},
                "git": {"installed": True, "version": "git version 2.45.0"},
                "docker": {"installed": False, "version": None},
                "wsl": {"installed": True, "available": True, "version": "2"},
            },
        },
        "scores": {"coding": 90, "gaming": 70, "ai": 80, "creator": 60},
        "risk_alerts": [
            {
                "level": "warning",
                "msg": "Docker is not available.",
                "id": "docker_missing",
                "component": "docker",
            }
        ],
        "recommendations": {
            "selected_goal": "ai",
            "goal_id": "comfyui_starter",
            "goal_name": "AI starter",
            "apps": [
                {
                    "name": "ComfyUI",
                    "required": True,
                    "reason": "Local workflow.",
                }
            ],
        },
    }


def test_reporter_renders_markdown_from_evaluation_data():
    markdown = reporter.render_markdown(sample_evaluation())

    assert "# StackPilot Report" in markdown
    assert "## Hardware Summary" in markdown
    assert "## Scores" in markdown
    assert "| Scenario | Score |" in markdown
    assert "| ai | [■■■■■■■■□□] 80/100 |" in markdown
    assert "## Risk Alerts" in markdown
    assert "| warning | Docker is not available. | docker |" in markdown
    assert "NVIDIA GeForce RTX 4070" in markdown


def test_reporter_writes_markdown_file_without_opening_notepad(tmp_path):
    path = reporter.export_report(sample_evaluation(), tmp_path, open_notepad=False)

    assert path.exists()
    assert path.parent == tmp_path
    assert path.name.startswith("report_")
    assert path.suffix == ".md"
    assert "ComfyUI" in path.read_text(encoding="utf-8")


def test_reporter_does_not_overwrite_reports_with_same_timestamp(tmp_path, monkeypatch):
    class FixedDateTime:
        @classmethod
        def now(cls):
            return cls()

        def strftime(self, fmt):
            return "20260622_101802"

    monkeypatch.setattr(reporter, "datetime", FixedDateTime)

    first = reporter.export_report(sample_evaluation(), tmp_path, open_notepad=False)
    second = reporter.export_report(sample_evaluation(), tmp_path, open_notepad=False)

    assert first.name == "report_20260622_101802.md"
    assert second.name == "report_20260622_101802_2.md"
    assert first.exists()
    assert second.exists()


def test_reporter_opens_notepad_with_nonblocking_popen(tmp_path, monkeypatch):
    calls = []

    class PopenSpy:
        def __init__(self, args, **kwargs):
            calls.append((args, kwargs))

    monkeypatch.setattr(reporter, "_should_open_notepad", lambda: True)
    monkeypatch.setattr(reporter.subprocess, "Popen", PopenSpy)
    monkeypatch.setattr(reporter.subprocess, "CREATE_NO_WINDOW", 0, raising=False)

    path = reporter.export_report(sample_evaluation(), tmp_path)

    assert path.exists()
    assert calls
    assert calls[0][0][:5] == ["cmd", "/c", "start", "", "notepad.exe"]
    assert str(path) in calls[0][0]


def test_run_pipeline_passes_short_goal_to_recommender(monkeypatch):
    seen = {}

    class Detector:
        def scan_system(self):
            return {"os_name": "Windows"}

    class Recommender:
        def evaluate(self, raw_specs, goal="ai"):
            seen["raw_specs"] = raw_specs
            seen["goal"] = goal
            return sample_evaluation()

    monkeypatch.setattr(tui, "StackPilotDetector", Detector)
    monkeypatch.setattr(tui, "StackPilotRecommender", Recommender)

    payload = tui.run_pipeline("gaming")

    assert seen == {"raw_specs": {"os_name": "Windows"}, "goal": "gaming"}
    assert payload["recommendations"]["goal_id"] == "comfyui_starter"


def test_tui_numeric_choice_reaches_pipeline(monkeypatch):
    selected = []
    output = []
    inputs = iter(["4", "3"])

    monkeypatch.setattr(tui, "enable_utf8_console", lambda: None)
    monkeypatch.setattr(tui, "clear_screen", lambda: None)

    def run_pipeline(goal):
        selected.append(goal)
        return sample_evaluation()

    monkeypatch.setattr(tui, "run_pipeline", run_pipeline)

    try:
        tui.run_tui(lambda prompt: next(inputs), output.append)
    except SystemExit as exc:
        assert exc.code == 0

    assert selected == ["creator"]
    assert any("场景评分" in line for line in output)


def test_config_dir_prefers_pyinstaller_meipass(tmp_path, monkeypatch):
    bundled_configs = tmp_path / "configs"
    bundled_configs.mkdir()
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert config_dir() == bundled_configs


def test_build_command_uses_onefile_clean_name_and_configs():
    command = build.build_command()

    assert "--onefile" in command
    assert "--clean" in command
    assert "--name=stackpilot" in command
    assert "--add-data" in command
    assert any("configs" in item for item in command)
