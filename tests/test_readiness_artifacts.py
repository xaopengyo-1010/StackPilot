from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_required_examples_exist_and_explain_feedback_targets():
    required = [
        "examples/README.md",
        "examples/scan-example.md",
        "examples/recommend-comfyui-example.md",
        "examples/install-plan-example.md",
        "examples/gpu-detection-example.md",
    ]

    for relative_path in required:
        assert (PROJECT_ROOT / relative_path).exists(), relative_path

    for relative_path in required[1:]:
        text = read_text(relative_path)
        assert "命令" in text, relative_path
        assert "摘录" in text or "输出重点" in text, relative_path
        assert "适合反馈什么" in text, relative_path


def test_required_issue_forms_collect_external_feedback_without_private_data():
    required = [
        ".github/ISSUE_TEMPLATE/hardware-detection-feedback.yml",
        ".github/ISSUE_TEMPLATE/wrong-recommendation.yml",
        ".github/ISSUE_TEMPLATE/bug-report.yml",
        ".github/ISSUE_TEMPLATE/feature-request.yml",
    ]

    for relative_path in required:
        text = read_text(relative_path)
        assert "name:" in text, relative_path
        assert "body:" in text, relative_path
        assert "打码" in text or "隐私" in text, relative_path

    hardware_form = read_text(".github/ISSUE_TEMPLATE/hardware-detection-feedback.yml")
    for required_label in [
        "OS",
        "CPU",
        "RAM",
        "GPU 列表",
        "虚拟显卡",
        "python -m stackpilot scan",
        "期望识别结果",
        "实际识别结果",
        "是否愿意提供更多信息",
    ]:
        assert required_label in hardware_form


def test_promotion_pack_exists_and_requests_feedback_without_star_ask():
    required = [
        "docs/promotion/qq-group-message.md",
        "docs/promotion/short-project-intro.md",
        "docs/promotion/gpu-feedback-request.md",
        "docs/promotion/release-summary-v0.3-v0.4.md",
    ]

    for relative_path in required:
        text = read_text(relative_path)
        assert "反馈" in text or "测试" in text or "验证" in text, relative_path
        assert "Star" not in text, relative_path
        assert "自动安装" in text or "不会修改系统设置" in text, relative_path
