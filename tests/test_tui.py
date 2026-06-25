from stackpilot import main as tui
from stackpilot.templates import UnknownTemplateError


def test_run_tui_exits_cleanly_when_input_closes(monkeypatch):
    output: list[str] = []

    monkeypatch.setattr(tui, "enable_utf8_console", lambda: None)
    monkeypatch.setattr(tui, "clear_screen", lambda: None)

    def read(_: str) -> str:
        raise EOFError

    tui.run_tui(read=read, write=output.append)

    assert any("输入已结束" in line for line in output)


def test_tui_shows_friendly_error_when_bundled_templates_are_missing(monkeypatch):
    output: list[str] = []
    responses = ["3"]

    monkeypatch.setattr(tui, "clear_screen", lambda: None)

    def read(_: str) -> str:
        if responses:
            return responses.pop(0)
        raise EOFError

    def run_pipeline(_: str):
        raise UnknownTemplateError("comfyui_starter", [])

    monkeypatch.setattr(tui, "run_pipeline", run_pipeline)

    tui.tui_loop(read=read, write=output.append)

    assert any("未找到内置配置模板" in line for line in output)
    assert any("程序没有修改系统" in line for line in output)
    assert any("输入已结束" in line for line in output)
