from typer.testing import CliRunner

from stackpilot import cli
from stackpilot.cli import app
from tests.test_recommender import sample_profile


def test_list_templates_command_lists_eight_templates_in_chinese():
    result = CliRunner().invoke(app, ["list-templates"])

    assert result.exit_code == 0
    assert "模板 ID" in result.output
    assert "模板名称" in result.output
    assert "coding_starter" in result.output
    assert "office_productivity" in result.output
    assert "办公生产力" in result.output


def test_unknown_goal_cli_error_is_chinese():
    result = CliRunner().invoke(app, ["recommend", "--goal", "does_not_exist"])

    assert result.exit_code == 1
    assert "未知目标：does_not_exist" in result.output
    assert "可用模板" in result.output


def test_recommend_command_still_runs(monkeypatch):
    monkeypatch.setattr(cli, "scan_system", sample_profile)
    result = CliRunner().invoke(app, ["recommend", "--goal", "comfyui_starter"])

    assert result.exit_code == 0
    assert "推荐结果：AI 绘图入门" in result.output
    assert "规则判断与风险提示" in result.output


def test_doctor_command_generates_markdown_and_json(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "scan_system", sample_profile)
    monkeypatch.setattr("stackpilot.report.default_output_dir", lambda: tmp_path)

    result = CliRunner().invoke(app, ["doctor", "--goal", "comfyui_starter"])

    assert result.exit_code == 0
    assert "正在检测电脑配置" in result.output
    assert "报告已生成" in result.output
    assert (tmp_path / "stackpilot-report.md").exists()
    assert (tmp_path / "stackpilot-report.json").exists()
