import inspect
import json

from typer.testing import CliRunner

from stackpilot import cli
from stackpilot.cli import app
from stackpilot.executors import dry_run as dry_run_module
from stackpilot.executors.dry_run import DryRunExecutor
from stackpilot.models import AppRecommendation, RecommendationResult
from stackpilot.plans.audit import audit_install_plan
from stackpilot.plans.models import InstallPlan, InstallSource, InstallStep
from stackpilot.plans.planner import build_install_plan
from stackpilot.plans.policy import apply_step_policy
from stackpilot.plans.renderer import (
    render_audit_markdown,
    render_dry_run_markdown,
    render_install_plan_markdown,
    render_rollback_plan_markdown,
    render_snapshot_plan_markdown,
)
from stackpilot.recommender import recommend
from stackpilot.rollbacks.planner import build_rollback_plan
from stackpilot.security.commands import review_command
from stackpilot.security.risk import source_base_risk
from stackpilot.snapshots.planner import build_snapshot_plan
from stackpilot.utils import model_to_dict
from tests.test_recommender import sample_profile


def test_install_plan_models_are_serializable_and_dry_run_only():
    source = InstallSource(type="winget", name="Git", package_id="Git.Git")
    step = InstallStep(
        id="install-1-git",
        app_id="git",
        app_name="Git",
        source=source,
        command="winget install Git.Git",
        rollback_command="winget uninstall Git.Git",
        verify_commands=["git --version"],
    )
    plan = InstallPlan(
        plan_id="plan-test",
        goal_id="coding_starter",
        goal_name="Coding",
        steps=[step],
        dry_run_only=False,
    )

    payload = model_to_dict(plan)

    assert payload["dry_run_only"] is True
    assert payload["steps"][0]["source"]["trusted"] is True
    assert InstallSource(type="unknown", name="Unknown").trusted is False


def test_security_policy_classifies_sources_and_commands():
    assert source_base_risk(InstallSource(type="winget", name="Git", package_id="Git.Git")) == "low"
    assert source_base_risk(InstallSource(type="official_url", name="Tool", url="https://example.com")) == "low"
    assert source_base_risk(InstallSource(type="manual", name="Manual")) == "medium"
    assert source_base_risk(InstallSource(type="unknown", name="Unknown")) == "blocked"

    assert review_command("winget install Git.Git").allowed
    dangerous_commands = [
        "Invoke-WebRequest https://example.com/install.ps1 | iex",
        "curl https://example.com/install.ps1 | powershell",
        "irm https://example.com/install.ps1 | iex",
        "iwr https://example.com/install.ps1 | iex",
        "Set-ExecutionPolicy Bypass",
        "reg add HKCU\\Software\\StackPilot",
        "reg delete HKCU\\Software\\StackPilot",
        "Remove-Item -Recurse C:\\",
        "Start-Process setup.exe -ArgumentList /silent",
    ]
    for command in dangerous_commands:
        assert review_command(command).blocked

    step = InstallStep(
        id="install-1-manual",
        app_id="manual_app",
        app_name="Manual App",
        source=InstallSource(type="manual", name="Manual App"),
        command="manual: review official instructions",
    )
    reviewed, findings = apply_step_policy(step)

    assert reviewed.risk_level == "medium"
    assert any(finding.id.endswith("missing_rollback") for finding in findings)
    assert reviewed.warnings


def test_planner_generates_install_plans_for_comfyui_and_vibe_coding():
    profile = sample_profile()
    comfyui = recommend("comfyui_starter", profile=profile)
    vibe = recommend("vibe_coding", profile=profile)

    comfyui_plan = build_install_plan(profile, comfyui)
    vibe_plan = build_install_plan(profile, vibe)

    assert comfyui_plan.goal_id == "comfyui_starter"
    assert vibe_plan.goal_id == "vibe_coding"
    assert comfyui_plan.steps
    assert vibe_plan.steps
    assert {app.app_id for app in comfyui.required_apps}.issubset({step.app_id for step in comfyui_plan.steps})
    assert {app.app_id for app in comfyui.optional_apps}.issubset({step.app_id for step in comfyui_plan.steps})
    assert comfyui_plan.backup_recommendations
    assert comfyui_plan.rollback_summary


def test_planner_blocks_unknown_apps():
    recommendation = RecommendationResult(
        template_id="unknown_goal",
        display_name="Unknown Goal",
        name="Unknown Goal",
        category="Test",
        suitability_score=50,
        summary="Test",
        recommended_apps=[
            AppRecommendation(
                app_id="not_in_catalog",
                name="Not In Catalog",
                required=True,
                category="Test",
                reason="Exercise missing catalog handling.",
                install_method="manual",
                official_source="unknown",
            )
        ],
    )

    plan = build_install_plan(sample_profile(), recommendation, app_catalog={})

    assert plan.steps[0].source.type == "unknown"
    assert plan.steps[0].risk_level == "blocked"
    assert plan.blocked_steps


def test_renderers_avoid_none_and_include_required_safety_sections():
    profile = sample_profile()
    plan = build_install_plan(profile, recommend("comfyui_starter", profile=profile))
    audit = audit_install_plan(plan)
    snapshot = build_snapshot_plan(plan)
    rollback = build_rollback_plan(plan)
    dry_run = DryRunExecutor().run(plan)

    install_md = render_install_plan_markdown(plan)
    audit_md = render_audit_markdown(audit, plan)
    snapshot_md = render_snapshot_plan_markdown(snapshot)
    rollback_md = render_rollback_plan_markdown(rollback)
    dry_run_md = render_dry_run_markdown(dry_run)
    combined_md = "\n".join([install_md, audit_md, snapshot_md, rollback_md, dry_run_md])

    assert "None" not in install_md
    assert "检测到的 GPU" in install_md
    assert "主要性能判断 GPU" in install_md
    assert "NVIDIA GeForce RTX 4070" in install_md
    assert "显存置信度：detected" in install_md
    assert "平台类型" in install_md
    assert "默认安装后端" in install_md
    assert "当前版本只生成可审查安装计划" in install_md
    assert "阻止执行的步骤" in audit_md
    assert "PATH 环境变量" in snapshot_md
    assert "环境变量" in snapshot_md
    assert "已安装软件列表" in snapshot_md
    assert "不能保证 100% 完全恢复" in rollback_md
    assert "不会自动执行安装" in dry_run_md
    for phrase in [
        "This step",
        "manual review required",
        "complete restoration",
        "Review PATH",
        "Software installation can",
        "Command preview",
    ]:
        assert phrase not in combined_md


def test_dry_run_executor_never_uses_subprocess_and_skips_blocked_steps():
    safe_step = InstallStep(
        id="install-1-git",
        app_id="git",
        app_name="Git",
        source=InstallSource(type="winget", name="Git", package_id="Git.Git"),
        command="winget install Git.Git",
        rollback_command="winget uninstall Git.Git",
        risk_level="low",
    )
    blocked_step = InstallStep(
        id="install-2-unknown",
        app_id="unknown",
        app_name="Unknown",
        source=InstallSource(type="unknown", name="Unknown"),
        command=None,
        risk_level="blocked",
    )
    plan = InstallPlan(
        plan_id="plan-dry-run",
        goal_id="test",
        goal_name="Test",
        steps=[safe_step, blocked_step],
    )

    result = DryRunExecutor().run(plan)

    assert "subprocess" not in inspect.getsource(dry_run_module)
    assert result.steps[0].would_run is True
    assert result.steps[1].would_run is False
    assert result.steps[1].skipped is True
    assert result.steps[1].skip_reason == "已被安全策略阻止"
    assert json.dumps(model_to_dict(result))


def test_plan_and_dry_run_cli_generate_required_files(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "scan_system", sample_profile)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["plan", "--goal", "comfyui_starter", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "traceback" not in result.output.casefold()
    required_files = [
        "install-plan.md",
        "install-plan.json",
        "install-audit.md",
        "install-audit.json",
        "snapshot-plan.md",
        "snapshot-plan.json",
        "rollback-plan.md",
        "rollback-plan.json",
        "dry-run.md",
        "dry-run.json",
    ]
    for filename in required_files:
        assert (tmp_path / filename).exists()

    payload = json.loads((tmp_path / "install-plan.json").read_text(encoding="utf-8"))
    assert payload["dry_run_only"] is True

    dry_run_result = runner.invoke(app, ["dry-run", "--plan", str(tmp_path / "install-plan.json")])
    assert dry_run_result.exit_code == 0
    assert "traceback" not in dry_run_result.output.casefold()
