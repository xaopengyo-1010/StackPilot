from stackpilot.llm.prompt_builder import build_report_prompt
from stackpilot.recommender import recommend
from stackpilot.templates import load_template
from tests.test_recommender import sample_profile


def test_llm_prompt_builder_generates_chinese_constrained_prompt():
    profile = sample_profile()
    template = load_template("comfyui_starter")
    recommendation = recommend("comfyui_starter", profile=profile)

    prompt = build_report_prompt(
        hardware_profile=profile,
        goal="comfyui_starter",
        template=template,
        recommendation_result=recommendation,
    )

    assert "基于已提供事实" in prompt
    assert "不编造" in prompt
    assert "不自动安装" in prompt
    assert "事实" in prompt
    assert "判断" in prompt
    assert "建议" in prompt
    assert "AI 绘图入门" in prompt
