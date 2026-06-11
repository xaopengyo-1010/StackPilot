import json

from stackpilot.report import generate_report
from tests.test_recommender import sample_profile


def test_report_generates_chinese_markdown_and_structured_json(tmp_path):
    md_path, json_path, recommendation = generate_report(
        "ai_beginner",
        output_dir=tmp_path,
        profile=sample_profile(),
    )

    assert md_path.exists()
    assert json_path.exists()
    assert recommendation.template_id == "ai_beginner"

    markdown = md_path.read_text(encoding="utf-8")
    assert "# StackPilot 应用推荐报告" in markdown
    assert "电脑配置摘要" in markdown
    assert "适配度评分" in markdown
    assert "推荐应用" in markdown
    assert "规则判断与风险提示" in markdown
    assert "StackPilot 当前版本只生成本地推荐报告" in markdown
    assert "None" not in markdown
    assert "traceback" not in markdown.casefold()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["hardware_profile"]["os_name"] == "Windows"
    assert payload["goal"]["id"] == "ai_beginner"
    assert payload["goal"]["name"] == "AI 入门体验"
    assert isinstance(payload["suitability_score"], int | float)
    assert "required_apps" in payload
    assert "optional_apps" in payload
    assert "findings" in payload
    assert "warnings" in payload
    assert "not_recommended" in payload
    assert "next_steps" in payload
    assert payload["generated_at"]
