import json

from stackpilot.report import generate_report
from tests.test_recommender import sample_profile


def test_report_generates_markdown_and_json(tmp_path):
    md_path, json_path, recommendation = generate_report(
        "ai_beginner",
        output_dir=tmp_path,
        profile=sample_profile(),
    )

    assert md_path.exists()
    assert json_path.exists()
    assert recommendation.template_id == "ai_beginner"

    markdown = md_path.read_text(encoding="utf-8")
    assert "# StackPilot Environment Blueprint Report" in markdown
    assert "Display name: AI 入门体验" in markdown
    assert "## 10. Transparency Notice" in markdown
    assert "StackPilot v0.1 does not download" in markdown
    assert "不会自动下载" in markdown

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["recommendation"]["template_id"] == "ai_beginner"
    assert payload["recommendation"]["display_name"] == "AI 入门体验"
    assert payload["profile"]["os_name"] == "Windows"
