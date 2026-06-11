from typer.testing import CliRunner

from stackpilot.cli import app


def test_list_templates_command_lists_eight_templates():
    result = CliRunner().invoke(app, ["list-templates"])

    assert result.exit_code == 0
    assert "coding_starter" in result.output
    assert "office_productivity" in result.output
    assert "办公生产力" in result.output
