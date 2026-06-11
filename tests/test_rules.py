from stackpilot.models import HardwareProfile
from stackpilot.rules.engine import evaluate_rules
from stackpilot.templates import load_template


def profile_with(**overrides) -> HardwareProfile:
    data = {
        "os_name": "Windows",
        "os_version": "Windows 11",
        "architecture": "AMD64",
        "cpu_name": "Test CPU",
        "cpu_cores": 8,
        "ram_gb": 32,
        "gpu_names": ["NVIDIA GeForce RTX 4070"],
        "vram_gb": 12,
        "disk_total_gb": 1000,
        "disk_free_gb": 200,
        "python_installed": True,
        "python_version": "3.11.9",
        "node_installed": True,
        "node_version": "v22.0.0",
        "git_installed": True,
        "git_version": "git version 2.45.0",
        "pnpm_installed": True,
        "pnpm_version": "9.0.0",
        "docker_installed": True,
        "docker_version": "Docker version 27.0.0",
        "wsl_installed": True,
        "wsl_version": "2",
        "nvidia_driver_version": "555.85",
        "warnings": [],
    }
    data.update(overrides)
    return HardwareProfile(**data)


def finding_ids(goal_id: str, profile: HardwareProfile) -> set[str]:
    return {finding.id for finding in evaluate_rules(profile, load_template(goal_id))}


def test_comfyui_vram_below_6gb_generates_warning():
    profile = profile_with(vram_gb=4, gpu_vram_gb=4)
    findings = evaluate_rules(profile, load_template("comfyui_starter"))

    assert any(
        finding.id == "comfyui_vram_low" and finding.level == "warning"
        for finding in findings
    )


def test_local_llm_ram_below_16gb_generates_warning():
    profile = profile_with(ram_gb=8, total_ram_gb=8)
    findings = evaluate_rules(profile, load_template("local_llm"))

    assert any(
        finding.id == "local_llm_ram_low" and finding.level == "warning"
        for finding in findings
    )


def test_disk_free_below_30gb_generates_critical():
    profile = profile_with(disk_free_gb=12)
    findings = evaluate_rules(profile, load_template("office_productivity"))

    assert any(
        finding.id == "disk_free_low" and finding.level == "critical"
        for finding in findings
    )


def test_coding_starter_missing_git_generates_warning():
    profile = profile_with(git_installed=False, git_version=None)

    assert "git_missing" in finding_ids("coding_starter", profile)


def test_coding_starter_missing_docker_generates_info():
    profile = profile_with(docker_installed=False, docker_version=None)
    findings = evaluate_rules(profile, load_template("coding_starter"))

    assert any(
        finding.id == "docker_missing" and finding.level == "info"
        for finding in findings
    )


def test_coding_starter_missing_python_generates_warning():
    profile = profile_with(python_installed=False, python_version=None)

    assert "python_missing" in finding_ids("coding_starter", profile)
