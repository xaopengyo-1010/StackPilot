from typer.testing import CliRunner

from stackpilot import cli
from stackpilot.cli import app
from stackpilot.models import FailedCheck, GpuDevice, HardwareProfile
from tests.test_recommender import sample_profile


def test_list_templates_command_lists_eight_templates_in_chinese():
    result = CliRunner().invoke(app, ["list-templates"])

    assert result.exit_code == 0
    assert "模板 ID" in result.output
    assert "模板名称" in result.output
    assert "coding_starter" in result.output
    assert "office_productivity" in result.output
    assert "办公生产力" in result.output


def test_unknown_goal_cli_error_is_chinese():
    result = CliRunner().invoke(app, ["recommend", "--goal", "does_not_exist"])

    assert result.exit_code == 1
    assert "未知目标：does_not_exist" in result.output
    assert "可用模板" in result.output


def test_recommend_command_still_runs(monkeypatch):
    monkeypatch.setattr(cli, "scan_system", sample_profile)
    result = CliRunner().invoke(app, ["recommend", "--goal", "comfyui_starter"])

    assert result.exit_code == 0
    assert "推荐结果：AI 绘图入门" in result.output
    assert "规则判断与风险提示" in result.output
    assert "能力分级" in result.output
    assert "磁盘风险分析" in result.output
    assert "模型路径建议" in result.output


def test_scan_command_shows_gpu_list_and_primary_gpu(monkeypatch):
    integrated = GpuDevice(name="AMD Radeon 780M", vendor="AMD", gpu_type="integrated", vram_confidence="shared")
    dedicated = GpuDevice(
        name="NVIDIA GeForce RTX 4060 Laptop GPU",
        vendor="NVIDIA",
        gpu_type="dedicated",
        dedicated_vram_gb=8,
        vram_confidence="detected",
    )
    profile = HardwareProfile(
        os_name="Windows",
        os_version="Windows 11",
        architecture="AMD64",
        ram_gb=32,
        gpus=[integrated, dedicated],
        primary_gpu=dedicated,
        gpu_selection_reason="检测到独立显卡，因此优先使用 NVIDIA GeForce RTX 4060 Laptop GPU 作为主要性能判断 GPU。",
        platform_profile={
            "os_family": "windows",
            "default_installer_backend": "winget",
        },
        python_installed=True,
        python_version="3.11.9",
        failed_checks=[
            FailedCheck(
                check_name="gpu_vram",
                status="unknown_error",
                reason="gpu_vram 检测失败：boom",
                impact="无法确认显存。",
                manual_check="任务管理器 -> 性能 -> GPU",
            )
        ],
    )
    monkeypatch.setattr(cli, "scan_system", lambda: profile)

    result = CliRunner().invoke(app, ["scan"])

    assert result.exit_code == 0
    assert "检测到的 GPU" in result.output
    assert "主要性能判断 GPU" in result.output
    assert "平台类型" in result.output
    assert "默认安装后端" in result.output
    assert "NVIDIA GeForce RTX 4060 Laptop GPU" in result.output
    assert "显存置信度：detected" in result.output
    assert "检测失败项" in result.output
    assert "gpu_vram" in result.output


def test_doctor_command_generates_markdown_and_json(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "scan_system", sample_profile)
    monkeypatch.setattr("stackpilot.report.default_output_dir", lambda: tmp_path)

    result = CliRunner().invoke(app, ["doctor", "--goal", "comfyui_starter"])

    assert result.exit_code == 0
    assert "正在检测电脑配置" in result.output
    assert "报告已生成" in result.output
    assert (tmp_path / "stackpilot-report.md").exists()
    assert (tmp_path / "stackpilot-report.json").exists()
