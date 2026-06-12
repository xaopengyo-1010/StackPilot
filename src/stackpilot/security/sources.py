from __future__ import annotations

from stackpilot.models import AppCatalogItem
from stackpilot.plans.models import InstallSource


VALID_SOURCE_TYPES = {
    "winget",
    "microsoft_store",
    "official_url",
    "github_release",
    "pypi",
    "npm",
    "docker_official",
    "manual",
    "unknown",
}


def normalize_source_type(value: str | None) -> str:
    """Normalize app-catalog source strings to an InstallSource type."""

    if not value:
        return "unknown"
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    if normalized in VALID_SOURCE_TYPES:
        return normalized
    if normalized in {"official", "official_website", "website"}:
        return "official_url"
    if normalized in {"store", "ms_store"}:
        return "microsoft_store"
    return "unknown"


def infer_source_type(item: AppCatalogItem) -> str:
    """Infer an install source from backward-compatible catalog fields."""

    explicit = normalize_source_type(item.install_source)
    if explicit != "unknown":
        return explicit
    if item.winget_id:
        return "winget"
    source = (item.official_url or item.official_source or "").casefold()
    methods = " ".join(item.install_methods).casefold()
    if "microsoft store" in methods or "microsoft.com/store" in source:
        return "microsoft_store"
    if "github.com" in source and ("release" in methods or "github release" in methods):
        return "github_release"
    if source.startswith("http://") or source.startswith("https://"):
        return "official_url"
    return "manual"


def install_source_from_catalog(item: AppCatalogItem) -> InstallSource:
    """Build structured InstallSource data from a catalog entry."""

    source_type = infer_source_type(item)
    url = item.official_url or (item.official_source if item.official_source.startswith("http") else None)
    package_id = item.winget_id if source_type == "winget" else None
    notes = [*item.notes]
    if item.risk_note:
        notes.append(item.risk_note)
    return InstallSource(
        type=source_type,
        name=item.name,
        url=url,
        package_id=package_id,
        notes=notes,
    )

