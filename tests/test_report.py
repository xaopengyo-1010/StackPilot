import json

from stackpilot.models import FailedCheck
from stackpilot.report import generate_report
from tests.test_recommender import sample_profile


def test_report_generates_chinese_markdown_and_structured_json(tmp_path):
    profile = sample_profile()
    profile.failed_checks = [
        FailedCheck(
            check_name="gpu_vram",
            status="unknown_error",
            reason="gpu_vram 检测失败：boom",
            impact="无法确认显存。",
            manual_check="任务管理器 -> 性能 -> GPU",
        )
    ]
    md_path, json_path, recommendation = generate_report(
        "ai_beginner",
        output_dir=tmp_path,
        profile=profile,
    )

    assert md_path.exists()
    assert json_path.exists()
    assert recommendation.template_id == "ai_beginner"

    markdown = md_path.read_text(encoding="utf-8")
    assert "# StackPilot 应用推荐报告" in markdown
    assert "电脑配置摘要" in markdown
    assert "适配度评分" in markdown
    assert "能力分级" in markdown
    assert "磁盘风险分析" in markdown
    assert "模型路径建议" in markdown
    assert "推荐应用" in markdown
    assert "规则判断与风险提示" in markdown
    assert "检测失败项" in markdown
    assert "gpu_vram" in markdown
    assert "检测到的 GPU" in markdown
    assert "主要性能判断 GPU" in markdown
    assert "NVIDIA GeForce RTX 4070" in markdown
    assert "显存置信度：detected" in markdown
    assert "StackPilot 当前版本只生成本地推荐报告" in markdown
    assert "None" not in markdown
    assert "traceback" not in markdown.casefold()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["hardware_profile"]["os_name"] == "Windows"
    assert payload["hardware_profile"]["gpus"][0]["gpu_type"] == "dedicated"
    assert payload["hardware_profile"]["primary_gpu"]["name"] == "NVIDIA GeForce RTX 4070"
    assert payload["goal"]["id"] == "ai_beginner"
    assert payload["goal"]["name"] == "AI 入门体验"
    assert isinstance(payload["suitability_score"], int | float)
    assert "required_apps" in payload
    assert "optional_apps" in payload
    assert "findings" in payload
    assert payload["failed_checks"][0]["check_name"] == "gpu_vram"
    assert payload["hardware_profile"]["failed_checks"][0]["status"] == "unknown_error"
    assert payload["recommendation"]["disk_risk_analysis"]["risk_level"] in {"low", "medium", "high"}
    assert payload["recommendation"]["model_path_recommendation"]["recommended_model_paths"]
    assert "warnings" in payload
    assert "not_recommended" in payload
    assert "next_steps" in payload
    assert payload["generated_at"]
