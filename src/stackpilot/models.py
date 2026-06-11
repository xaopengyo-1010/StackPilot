from __future__ import annotations

from pydantic import BaseModel, Field


class SystemProfile(BaseModel):
    os_name: str
    os_version: str
    architecture: str
    cpu_name: str | None = None
    cpu_cores: int | None = None
    total_ram_gb: float | None = None
    gpu_names: list[str] = Field(default_factory=list)
    gpu_vram_gb: float | None = None
    disk_total_gb: float | None = None
    disk_free_gb: float | None = None
    python_installed: bool
    python_version: str | None = None
    node_installed: bool
    node_version: str | None = None
    git_installed: bool
    git_version: str | None = None
    pnpm_installed: bool
    pnpm_version: str | None = None
    docker_installed: bool
    docker_version: str | None = None
    wsl_available: bool
    nvidia_driver_version: str | None = None
    warnings: list[str] = Field(default_factory=list)


class AppRecommendation(BaseModel):
    app_id: str
    name: str
    required: bool
    category: str
    reason: str
    install_method: str
    official_source: str
    config_notes: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)


class TemplateRecommendation(BaseModel):
    template_id: str
    display_name: str
    name: str
    category: str
    suitability_score: float
    summary: str
    recommended_apps: list[AppRecommendation] = Field(default_factory=list)
    config_recommendations: list[str] = Field(default_factory=list)
    risk_warnings: list[str] = Field(default_factory=list)
    not_recommended: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class AppCatalogItem(BaseModel):
    app_id: str
    name: str
    category: str
    official_source: str
    install_methods: list[str] = Field(default_factory=list)
    description: str
    config_notes: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)


class TemplateRequirements(BaseModel):
    min_ram_gb: float | None = None
    recommended_ram_gb: float | None = None
    min_vram_gb: float | None = None
    recommended_vram_gb: float | None = None
    min_disk_free_gb: float | None = None
    os: list[str] = Field(default_factory=list)


class TemplateApp(BaseModel):
    app_id: str
    required: bool = True
    reason: str


class TemplateDefinition(BaseModel):
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
        return self.display_name
