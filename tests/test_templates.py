import pytest

from stackpilot.templates import UnknownTemplateError, load_app_catalog, load_template, load_templates


EXPECTED_TEMPLATE_DISPLAY_NAMES = {
    "coding_starter": "写代码入门",
    "vibe_coding": "AI 辅助写代码",
    "ai_beginner": "AI 入门体验",
    "comfyui_starter": "AI 绘图入门",
    "local_llm": "本地大模型",
    "gaming_setup": "游戏玩家常用软件",
    "creator_setup": "视频/内容创作",
    "office_productivity": "办公生产力",
}


def test_templates_can_load_eight_templates():
    templates = load_templates()
    ids = {template.template_id for template in templates}

    assert len(templates) == 8
    assert ids == set(EXPECTED_TEMPLATE_DISPLAY_NAMES)
    assert {
        template.template_id: template.display_name for template in templates
    } == EXPECTED_TEMPLATE_DISPLAY_NAMES


def test_app_catalog_can_load():
    catalog = load_app_catalog()
    required_app_ids = {
        "vscode",
        "git",
        "python",
        "nodejs",
        "pnpm",
        "docker_desktop",
        "wsl2_ubuntu",
        "windows_terminal",
        "cursor",
        "codex_cli",
        "continue",
        "github_copilot",
        "browser",
        "chatgpt",
        "claude",
        "gemini",
        "perplexity",
        "poe",
        "ollama",
        "lm_studio",
        "comfyui",
        "ffmpeg",
        "nvidia_app",
        "cuda_pytorch_note",
        "llama_cpp",
        "open_webui",
        "anythingllm",
        "steam",
        "epic_games_launcher",
        "msi_afterburner",
        "rtss",
        "capframex",
        "discord",
        "seven_zip",
        "obs_studio",
        "davinci_resolve",
        "audacity",
        "capcut_jianying",
        "handbrake",
        "krita",
        "blender",
        "google_chrome",
        "microsoft_edge",
        "office_suite_note",
        "obsidian",
        "notion",
        "zotero",
        "snipaste",
        "sharex",
        "sumatrapdf",
        "everything",
        "powertoys",
    }

    assert required_app_ids <= set(catalog)
    assert catalog["git"].install_methods[0] == "从官方网站或包管理器手动安装"


def test_all_template_apps_exist_in_catalog():
    catalog = load_app_catalog()
    missing = []
    for template in load_templates():
        for app in template.apps:
            if app.app_id not in catalog:
                missing.append((template.template_id, app.app_id))

    assert missing == []


def test_unknown_goal_reports_chinese_error():
    with pytest.raises(UnknownTemplateError) as exc_info:
        load_template("does_not_exist")

    message = str(exc_info.value)
    assert "未知目标：does_not_exist" in message
    assert "可用模板" in message
    assert "coding_starter" in message
