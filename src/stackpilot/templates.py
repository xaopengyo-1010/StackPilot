from __future__ import annotations

import json
import sys
from pathlib import Path

from .models import AppCatalogItem, TemplateDefinition
from .utils import parse_model


class UnknownTemplateError(ValueError):
    def __init__(self, template_id: str, available: list[str]) -> None:
        self.template_id = template_id
        self.available = available
        message = f"未知目标：{template_id}。可用模板：{', '.join(available)}"
        super().__init__(message)


TEMPLATE_AUDIENCES = {
    "coding_starter": "第一次配置编程环境的新手。",
    "vibe_coding": "想用 AI 辅助写代码，同时保留代码审查和测试习惯的用户。",
    "ai_beginner": "想先体验网页 AI 工具的普通用户。",
    "comfyui_starter": "想在本地尝试 AI 绘图和 ComfyUI 工作流的用户。",
    "local_llm": "想在本机运行 Ollama、LM Studio 等本地模型的用户。",
    "gaming_setup": "想整理游戏平台、驱动和性能监控工具的玩家。",
    "creator_setup": "想做录屏、剪辑、音频和素材处理的内容创作者。",
    "office_productivity": "想准备浏览器、文档、笔记、截图、PDF 等基础工具的办公用户。",
}

TEMPLATE_ORDER = {
    "coding_starter": 0,
    "vibe_coding": 1,
    "ai_beginner": 2,
    "comfyui_starter": 3,
    "local_llm": 4,
    "gaming_setup": 5,
    "creator_setup": 6,
    "office_productivity": 7,
}


def template_audience(template_id: str) -> str:
    return TEMPLATE_AUDIENCES.get(template_id, "适合需要该模板所描述工作流的用户。")


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config_dir(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)

    meipass = getattr(sys, "_MEIPASS", None)
    candidates = [
        Path(meipass) / "configs" if meipass else None,
        Path.cwd() / "configs",
        project_root() / "configs",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    return project_root() / "configs"


def load_app_catalog(path: str | Path | None = None) -> dict[str, AppCatalogItem]:
    catalog_path = config_dir(path) / "app_catalog.json"
    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    apps = raw.get("apps", raw)
    catalog: dict[str, AppCatalogItem] = {}
    for item in apps:
        app = parse_model(AppCatalogItem, item)
        catalog[app.app_id] = app
    return catalog


def load_scoring_rules(path: str | Path | None = None) -> dict:
    rules_path = config_dir(path) / "scoring_rules.json"
    return json.loads(rules_path.read_text(encoding="utf-8"))


def load_templates(path: str | Path | None = None) -> list[TemplateDefinition]:
    templates_path = config_dir(path) / "templates"
    definitions: list[TemplateDefinition] = []
    for template_file in sorted(templates_path.glob("*.json")):
        raw = json.loads(template_file.read_text(encoding="utf-8"))
        definitions.append(parse_model(TemplateDefinition, raw))
    return sorted(definitions, key=lambda template: (TEMPLATE_ORDER.get(template.template_id, 999), template.template_id))


def available_template_ids(path: str | Path | None = None) -> list[str]:
    return [template.template_id for template in load_templates(path)]


def load_template(template_id: str, path: str | Path | None = None) -> TemplateDefinition:
    templates = load_templates(path)
    for template in templates:
        if template.template_id == template_id:
            return template
    raise UnknownTemplateError(template_id, [template.template_id for template in templates])
