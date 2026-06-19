# StackPilot 架构说明

StackPilot v0.5 Alpha 在可审查安装计划系统上新增环境检测失败降级、能力分级、磁盘风险和模型路径建议。项目仍然保持兼容式分层，不推倒原有 CLI、模板、扫描器、推荐器和报告生成器。

核心链路现在是：

```text
scanner -> rules -> recommender -> plan generator -> audit -> snapshot plan -> rollback plan -> dry-run executor
```

也可以从数据流角度理解为：

```text
硬件事实采集
-> 规则判断
-> 结构化推荐
-> 可审查安装计划
-> 安全策略审计
-> 备份计划
-> 回滚计划
-> dry-run executor
```

## 现有核心层

`src/stackpilot/scanner.py` 只采集本地公开系统事实，例如系统版本、CPU、内存、GPU 设备、显存置信度、磁盘空间，以及 Python、Node.js、Git、Docker、WSL 等工具状态。Scanner 不推荐应用，不写报告，也不修改系统。

`src/stackpilot/rules/engine.py` 集中处理规则判断。规则输入是硬件事实和目标模板，输出是结构化 `RuleFinding` 列表。规则层不渲染 Markdown，不打印 CLI，也不执行命令。

`src/stackpilot/recommender.py` 把目标模板、应用目录、硬件事实和规则 findings 组合成 `RecommendationResult`。推荐器不写文件、不渲染 Markdown、不直接打印终端输出。

`src/stackpilot/report.py` 负责把 `ReportData` 渲染为 Markdown 和 JSON 推荐报告。报告层不重新判断硬件，也不覆盖规则级别。

`src/stackpilot/llm/prompt_builder.py` 只生成可审查 prompt，不调用真实 LLM API，不要求 API Key，也不联网。

## GPU 检测基础

GPU 是图形处理器总称，不等于独立显卡。StackPilot 在模型层严格区分：

- `integrated`: 核显 / 集成 GPU，通常使用共享内存。
- `dedicated`: 独显 / 独立 GPU，可能有独立显存。
- `virtual`: 远程、虚拟或基础显示设备，不作为真实性能判断 GPU。
- `unknown`: 无法确认类型的 GPU，必须保守处理。

`src/stackpilot/models.py` 中的 `GpuDevice` 表示单个 GPU 设备，字段包含 `vendor`、`gpu_type`、`dedicated_vram_gb`、`shared_memory_gb`、`vram_confidence`、`driver_version`、`device_id`、`source` 和与类型一致的布尔 flag。

`vram_confidence` 是信任特性，不是单纯数值：

- `detected`: 相对可靠地检测到独立显存。
- `shared`: 共享内存，不等于独立显存。
- `estimated`: 根据设备名或规则估算，可能不准确。
- `unknown`: 未能确认显存。

`src/stackpilot/hardware/gpu_classifier.py` 负责厂商、类型和显存置信度分类。`src/stackpilot/hardware/windows_gpu.py` 提供 `parse_windows_gpu_controllers(raw_controllers)`，接收 Win32_VideoController 风格的原始字典，返回 `GpuDevice` 列表。parser 是纯函数，测试不依赖真实机器。

`src/stackpilot/hardware/gpu_selector.py` 提供 `select_primary_gpu(gpus)`。选择顺序是 dedicated > integrated > unknown，virtual-only 返回 `None` 并给出保守原因。多独显时优先选择更高 `vram_confidence` 和更高独立显存的设备。

报告和安装计划必须显示 GPU 列表、primary GPU、选择原因和显存置信度。旧字段 `gpu_name`、`gpu_names`、`vram_gb`、`gpu_vram_gb` 只作为兼容字段保留，不能继续作为主要推荐判断来源。

## 硬件 fixtures

GPU 检测质量由 `tests/fixtures/hardware/` 维护。新增 GPU 规则或修复误判时，应优先添加 fixture，至少包含：

- `raw_windows_video_controllers`
- `expected_gpus`
- `expected_primary_gpu`
- `expected_gpu_selection_reason_contains`
- `expected_findings`

fixtures 覆盖核显、独显、核显+独显、虚拟显卡、unknown、no GPU、shared/detected/estimated/unknown 显存置信度。这样可以避免只在当前开发机上“看起来正确”。

## 平台抽象

`src/stackpilot/platform/detector.py` 生成 `PlatformProfile`，包含 `os_family`、`architecture`、`package_managers` 和 `default_installer_backend`。当前实现 Windows-first；macOS 和 Linux 只保留 experimental 基础结构，不做深度安装支持。

Installer backend 预留值包括 `winget`、`brew`、`apt`、`manual` 和 `unknown`。StackPilot 不把 winget 写死为唯一路径。

## LLM 边界

LLM 只能做解释层，不能参与硬件事实判断。硬件事实必须来自 scanner、parser、classifier、selector 和可测试规则。架构原则是：别让 LLM 给错误硬件诊断写诗。

## v0.3 计划系统

`src/stackpilot/plans/models.py` 定义安装计划模型：

- `InstallSource`
- `InstallStep`
- `InstallPlan`
- `AuditFinding`
- `InstallAuditReport`

`src/stackpilot/plans/planner.py` 把 `RecommendationResult` 转成 `InstallPlan`。每个应用推荐会变成一个可审查步骤，包含结构化来源、命令预览、风险等级、审计说明、验证命令、回滚命令、前置条件和 warnings。

`src/stackpilot/security/` 提供三类安全策略：

- 来源策略：winget 和 Microsoft Store 默认低风险，unknown 来源直接 blocked。
- 命令策略：只允许少量命令预览出现在计划中，危险管道和注册表修改会 blocked。
- 风险策略：source、command、rollback、admin 等因素共同决定步骤风险。

`src/stackpilot/plans/audit.py` 对计划进行审计，列出 blocked、medium/high、缺少 rollback、unknown source 等步骤。审计报告用于降低风险，不表示风险已经被消除。

`src/stackpilot/snapshots/` 只生成备份 / 快照计划，不创建真实系统还原点。计划会提醒用户审查 PATH、环境变量、已安装软件列表、StackPilot 计划文件、dry-run 输出和关键配置路径。

`src/stackpilot/rollbacks/` 只生成回滚计划，不卸载软件、不恢复文件、不改环境变量。回滚计划明确说明软件安装可能写入注册表、用户目录或缓存，因此不能保证 100% 完全恢复。

`src/stackpilot/executors/dry_run.py` 是 v0.3 唯一 executor。它接收 `InstallPlan`，遍历步骤，生成 dry-run 结果，不调用 subprocess，不执行安装命令。blocked 步骤会被跳过，manual 步骤要求人工审查。

## 为什么先生成计划而不是直接安装

StackPilot 面向普通电脑用户，安装软件会带来系统级影响，例如 PATH 修改、后台服务、驱动、注册表、用户目录文件、缓存和启动项。直接执行安装命令会让用户失去审查机会，也会让回滚边界变得不透明。

v0.3 的目标是先把每一步变成结构化、可审查、可测试、可导出的计划文本。用户和后续 UI 都可以在执行前看到来源、风险、验证方式和回滚限制。

## 为什么 executor 默认 dry-run

dry-run 是当前安全边界。它证明 StackPilot 可以组织执行计划和预览，但不会实际执行。这样可以在不修改系统的前提下测试数据模型、策略、报告和 CLI 体验。

如果加入真实 executor，必须显式启用、逐步确认、复用同一套策略审计，并继续默认禁用真实执行。

## 不承诺绝对安全

StackPilot 可以降低风险，但不能承诺绝对无病毒。软件来源、安装器行为、上游供应链、用户配置和后续下载内容都可能变化。项目应使用“降低风险”“需要人工确认”等表述，不应写“绝对安全”。

## 不承诺 100% 完美回滚

软件安装可能写入注册表、服务、驱动、用户目录、缓存、浏览器配置、模型目录或云同步目录。StackPilot 可以规划卸载、PATH 恢复、环境变量恢复和配置备份恢复步骤，但不能保证 100% 完全恢复到安装前状态。

## 真实执行器接入原则

真实执行器如果出现，必须满足：

- 默认关闭，不能替代 dry-run 默认路径。
- 只能执行已审计、未 blocked、用户逐步确认的步骤。
- 不能执行未知来源脚本、危险 shell 管道或下载即执行命令。
- 必须记录日志，并在执行前要求用户审查 snapshot 和 rollback 计划。
- 必须保留清晰的人工中止路径。
