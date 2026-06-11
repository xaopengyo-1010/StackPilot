import pytest

from stackpilot.templates import UnknownTemplateError, load_app_catalog, load_template, load_templates


def test_templates_can_load():
    templates = load_templates()
    ids = {template.template_id for template in templates}
    assert len(templates) == 8
    assert "coding_starter" in ids
    assert "comfyui_starter" in ids
    assert "minecraft_realism" in ids


def test_app_catalog_can_load():
    catalog = load_app_catalog()
    assert "vscode" in catalog
    assert "comfyui" in catalog
    assert "steam" in catalog


def test_unknown_goal_reports_clear_error():
    with pytest.raises(UnknownTemplateError) as exc_info:
        load_template("does_not_exist")

    message = str(exc_info.value)
    assert "Unknown goal 'does_not_exist'" in message
    assert "coding_starter" in message
