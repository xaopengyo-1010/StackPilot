from __future__ import annotations

import json
from pathlib import Path

from .models import AppCatalogItem, TemplateDefinition
from .utils import parse_model


class UnknownTemplateError(ValueError):
    def __init__(self, template_id: str, available: list[str]) -> None:
        self.template_id = template_id
        self.available = available
        message = f"Unknown goal '{template_id}'. Available templates: {', '.join(available)}"
        super().__init__(message)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config_dir(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)

    candidates = [
        Path.cwd() / "configs",
        project_root() / "configs",
    ]
    for candidate in candidates:
        if candidate.exists():
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
    return definitions


def available_template_ids(path: str | Path | None = None) -> list[str]:
    return [template.template_id for template in load_templates(path)]


def load_template(template_id: str, path: str | Path | None = None) -> TemplateDefinition:
    templates = load_templates(path)
    for template in templates:
        if template.template_id == template_id:
            return template
    raise UnknownTemplateError(template_id, [template.template_id for template in templates])
