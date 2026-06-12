from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


GpuVendor = Literal["NVIDIA", "AMD", "Intel", "Microsoft", "Apple", "Unknown"]
GpuType = Literal["integrated", "dedicated", "virtual", "unknown"]
VramConfidence = Literal["detected", "estimated", "shared", "unknown"]
GpuSource = Literal["wmi", "powershell", "system_profiler", "lspci", "fixture", "unknown"]
OsFamily = Literal["windows", "macos", "linux", "unknown"]
Architecture = Literal["x86_64", "arm64", "unknown"]
InstallerBackend = Literal["winget", "brew", "apt", "manual", "unknown"]


def _safe_text(value: object | None, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _normalized_choice(value: object | None, allowed: set[str], fallback: str) -> str:
    text = _safe_text(value, fallback)
    for choice in allowed:
        if text.casefold() == choice.casefold():
            return choice
    return fallback


class GpuDevice(BaseModel):
    """A single graphics device detected or inferred from a hardware source."""

    name: str = "Unknown GPU"
    vendor: GpuVendor = "Unknown"
    gpu_type: GpuType = "unknown"
    dedicated_vram_gb: float | None = None
    shared_memory_gb: float | None = None
    vram_confidence: VramConfidence = "unknown"
    driver_version: str | None = None
    device_id: str | None = None
    source: GpuSource = "unknown"
    is_integrated: bool = False
    is_dedicated: bool = False
    is_virtual: bool = False
    notes: list[str] = Field(default_factory=list)

    def __init__(self, **data):
        gpu_type = _normalized_choice(
            data.get("gpu_type"),
            {"integrated", "dedicated", "virtual", "unknown"},
            "unknown",
        )
        data["name"] = _safe_text(data.get("name"), "Unknown GPU")
        data["vendor"] = _normalized_choice(
            data.get("vendor"),
            {"NVIDIA", "AMD", "Intel", "Microsoft", "Apple", "Unknown"},
            "Unknown",
        )
        data["gpu_type"] = gpu_type
        data["vram_confidence"] = _normalized_choice(
            data.get("vram_confidence"),
            {"detected", "estimated", "shared", "unknown"},
            "unknown",
        )
        data["source"] = _normalized_choice(
            data.get("source"),
            {"wmi", "powershell", "system_profiler", "lspci", "fixture", "unknown"},
            "unknown",
        )
        data["is_integrated"] = gpu_type == "integrated"
        data["is_dedicated"] = gpu_type == "dedicated"
        data["is_virtual"] = gpu_type == "virtual"
        super().__init__(**data)

    @property
    def type_label_zh(self) -> str:
        labels = {
            "integrated": "核显",
            "dedicated": "独显",
            "virtual": "虚拟显卡",
            "unknown": "未知显卡",
        }
        return labels[self.gpu_type]

    @property
    def vram_label_zh(self) -> str:
        if self.vram_confidence == "detected" and self.dedicated_vram_gb is not None:
            return f"{self.dedicated_vram_gb:g} GB 独立显存"
        if self.vram_confidence == "shared":
            if self.shared_memory_gb is not None:
                return f"{self.shared_memory_gb:g} GB 共享内存，不等于独立显存"
            return "共享内存，不等于独立显存"
        if self.vram_confidence == "estimated" and self.dedicated_vram_gb is not None:
            return f"{self.dedicated_vram_gb:g} GB 估算显存，可能不准确"
        return "未能确认显存"

    def markdown_summary(self) -> str:
        return f"{self.name}（{self.type_label_zh} / {self.vram_label_zh} / 显存置信度：{self.vram_confidence}）"


class PlatformProfile(BaseModel):
    """Cross-platform operating-system facts used by future installers."""

    os_family: OsFamily = "unknown"
    os_name: str = "未知"
    os_version: str = "未知"
    architecture: Architecture = "unknown"
    package_managers: list[str] = Field(default_factory=list)
    default_installer_backend: InstallerBackend = "unknown"
    notes: list[str] = Field(default_factory=list)

    def __init__(self, **data):
        data["os_family"] = _normalized_choice(
            data.get("os_family"),
            {"windows", "macos", "linux", "unknown"},
            "unknown",
        )
        data["os_name"] = _safe_text(data.get("os_name"), "未知")
        data["os_version"] = _safe_text(data.get("os_version"), "未知")
        data["architecture"] = _normalized_choice(
            data.get("architecture"),
            {"x86_64", "arm64", "unknown"},
            "unknown",
        )
        data["default_installer_backend"] = _normalized_choice(
            data.get("default_installer_backend"),
            {"winget", "brew", "apt", "manual", "unknown"},
            "unknown",
        )
        super().__init__(**data)


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
    gpus: list[GpuDevice] = Field(default_factory=list)
    primary_gpu: GpuDevice | None = None
    gpu_selection_reason: str | None = None
    vram_gb: float | None = None
    gpu_vram_gb: float | None = None
    platform_profile: PlatformProfile | None = None
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

        gpus = data.get("gpus") or []
        gpu_names = data.get("gpu_names") or []
        if not gpu_names and gpus:
            gpu_names = [
                gpu.name if isinstance(gpu, GpuDevice) else _safe_text(gpu.get("name") if isinstance(gpu, dict) else None, "")
                for gpu in gpus
            ]
            gpu_names = [name for name in gpu_names if name]
            data["gpu_names"] = gpu_names
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
    winget_id: str | None = None
    official_url: str | None = None
    install_source: str | None = None
    verify_commands: list[str] = Field(default_factory=list)
    rollback_command: str | None = None
    requires_admin: bool = False
    estimated_disk_mb: int | None = None
    risk_note: str | None = None
    notes: list[str] = Field(default_factory=list)


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
