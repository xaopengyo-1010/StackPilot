from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HardwareProfile(BaseModel):
    """Structured facts collected from the local machine.

    The v0.2 fields use compact hardware names such as ``ram_gb`` and
    ``vram_gb``. Older StackPilot code still reads names such as
    ``total_ram_gb`` and ``gpu_vram_gb``, so both sets are kept in sync during
    construction.
    """

    os_name: str = "未知"
    os_version: str = "未知"
    architecture: str = "未知"
    cpu_name: str | None = None
    cpu_cores: int | None = None
    ram_gb: float | None = None
    total_ram_gb: float | None = None
    gpu_name: str | None = None
    gpu_names: list[str] = Field(default_factory=list)
    vram_gb: float | None = None
    gpu_vram_gb: float | None = None
    disk_total_gb: float | None = None
    disk_free_gb: float | None = None
    python_installed: bool = False
    python_version: str | None = None
    node_installed: bool = False
    node_version: str | None = None
    git_installed: bool = False
    git_version: str | None = None
    pnpm_installed: bool = False
    pnpm_version: str | None = None
    docker_installed: bool = False
    docker_version: str | None = None
    wsl_installed: bool = False
    wsl_available: bool = False
    wsl_version: str | None = None
    nvidia_driver_version: str | None = None
    warnings: list[str] = Field(default_factory=list)

    def __init__(self, **data):
        if data.get("ram_gb") is None and data.get("total_ram_gb") is not None:
            data["ram_gb"] = data["total_ram_gb"]
        if data.get("total_ram_gb") is None and data.get("ram_gb") is not None:
            data["total_ram_gb"] = data["ram_gb"]

        if data.get("vram_gb") is None and data.get("gpu_vram_gb") is not None:
            data["vram_gb"] = data["gpu_vram_gb"]
        if data.get("gpu_vram_gb") is None and data.get("vram_gb") is not None:
            data["gpu_vram_gb"] = data["vram_gb"]

        gpu_names = data.get("gpu_names") or []
        if data.get("gpu_name") is None and gpu_names:
            data["gpu_name"] = gpu_names[0]
        if not gpu_names and data.get("gpu_name"):
            data["gpu_names"] = [data["gpu_name"]]

        if data.get("wsl_installed") is None and data.get("wsl_available") is not None:
            data["wsl_installed"] = data["wsl_available"]
        if data.get("wsl_available") is None and data.get("wsl_installed") is not None:
            data["wsl_available"] = data["wsl_installed"]
        if "wsl_available" in data and "wsl_installed" not in data:
            data["wsl_installed"] = data["wsl_available"]
        if "wsl_installed" in data and "wsl_available" not in data:
            data["wsl_available"] = data["wsl_installed"]

        super().__init__(**data)


SystemProfile = HardwareProfile


class EnvironmentStatus(BaseModel):
    """Detected status for a local developer or productivity tool."""

    name: str
    installed: bool
    version: str | None = None


class RuleFinding(BaseModel):
    """A structured rule result produced from hardware facts and a goal."""

    id: str
    level: Literal["info", "warning", "critical"]
    title: str
    message: str
    related_goal: str | None = None
    related_component: str | None = None
    evidence: dict[str, object | None] = Field(default_factory=dict)


class AppRecommendation(BaseModel):
    """An application recommendation with source and setup guidance."""

    app_id: str
    name: str
    required: bool
    category: str
    reason: str
    install_method: str
    official_source: str
    config_notes: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    """Structured recommendation output consumed by CLI and report renderers."""

    template_id: str
    display_name: str
    name: str
    category: str
    suitability_score: float
    summary: str
    recommended_apps: list[AppRecommendation] = Field(default_factory=list)
    findings: list[RuleFinding] = Field(default_factory=list)
    config_recommendations: list[str] = Field(default_factory=list)
    risk_warnings: list[str] = Field(default_factory=list)
    not_recommended: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)

    @property
    def goal_id(self) -> str:
        """Return the stable template id used as the recommendation goal."""
        return self.template_id

    @property
    def goal_name(self) -> str:
        """Return the Chinese display name for the goal."""
        return self.display_name

    @property
    def required_apps(self) -> list[AppRecommendation]:
        """Return apps marked as required by the selected template."""
        return [app for app in self.recommended_apps if app.required]

    @property
    def optional_apps(self) -> list[AppRecommendation]:
        """Return apps marked as optional by the selected template."""
        return [app for app in self.recommended_apps if not app.required]

    @property
    def warnings(self) -> list[str]:
        """Return user-visible warning and critical finding messages."""
        return [
            finding.message
            for finding in self.findings
            if finding.level in {"warning", "critical"}
        ]


TemplateRecommendation = RecommendationResult


class ReportData(BaseModel):
    """Serializable report payload shared by Markdown and JSON renderers."""

    hardware_profile: HardwareProfile
    recommendation: RecommendationResult
    generated_at: str


class AppCatalogItem(BaseModel):
    """Application catalog entry loaded from ``configs/app_catalog.json``."""

    app_id: str
    name: str
    category: str
    official_source: str
    install_methods: list[str] = Field(default_factory=list)
    description: str
    config_notes: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)


class TemplateRequirements(BaseModel):
    """Minimum and recommended hardware requirements for a goal template."""

    min_ram_gb: float | None = None
    recommended_ram_gb: float | None = None
    min_vram_gb: float | None = None
    recommended_vram_gb: float | None = None
    min_disk_free_gb: float | None = None
    os: list[str] = Field(default_factory=list)


class TemplateApp(BaseModel):
    """Application reference inside a recommendation template."""

    app_id: str
    required: bool = True
    reason: str


class TemplateDefinition(BaseModel):
    """Goal template loaded from ``configs/templates``."""

    template_id: str
    display_name: str
    category: str
    description: str
    requirements: TemplateRequirements = Field(default_factory=TemplateRequirements)
    apps: list[TemplateApp] = Field(default_factory=list)
    config_recommendations: list[str] = Field(default_factory=list)
    risk_warnings: list[str] = Field(default_factory=list)
    not_recommended: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)

    @property
    def name(self) -> str:
        """Return the human-facing template name."""
        return self.display_name
