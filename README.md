# StackPilot v0.4.0-alpha is out

<div align="center">
  <img src="assets/stackpilot-logo.png" alt="StackPilot logo" width="152" />
  <h1>StackPilot</h1>
  <p><strong>开源、透明、可审计的电脑环境推荐与部署计划助手</strong></p>
  <p>检测你的电脑配置，生成应用推荐报告、风险提示和可审查安装计划。</p>
  <p><code>GPU Detection Hardening</code> / <code>Auditable Setup Plans</code> / <code>Dry-run First</code></p>
  <p>
    <img alt="Version" src="https://img.shields.io/badge/version-v0.4.0--alpha-2f6fef?style=flat-square" />
    <img alt="Python" src="https://img.shields.io/badge/python-%3E%3D3.11-2f6fef?style=flat-square" />
    <img alt="License" src="https://img.shields.io/badge/license-MIT-2f6fef?style=flat-square" />
    <img alt="Status" src="https://img.shields.io/badge/status-alpha-6b7280?style=flat-square" />
  </p>
  <h3>看得见每一步，装得明白，撤得回来。</h3>
</div>

<p align="center"><strong>15 秒看懂 StackPilot 如何检测电脑配置，并生成推荐报告与可审查安装计划。</strong></p>

https://github.com/user-attachments/assets/5a50b36c-ec9f-494f-af9f-0c6ae95452f6

## StackPilot 是什么？

StackPilot 是一个本地优先的 CLI 工具。它会读取电脑的公开硬件与环境信息，再用规则引擎和场景模板生成适合当前目标的建议。

它的产品边界很明确：先看清电脑配置，再判断适配风险，最后输出可以人工审查的安装计划。当前版本只生成报告和计划，不会自动安装软件，也不会直接修改系统。

## 产品预览

| 硬件扫描                                                                    | 推荐报告                                                                              | 安装计划                                                                            |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| ![StackPilot GPU detection scan](assets/screenshots/scan-gpu-detection.png) | ![StackPilot ComfyUI recommendation report](assets/screenshots/recommend-comfyui.png) | ![StackPilot generated install plan](assets/screenshots/install-plan-generated.png) |

## Highlights

| Step          | What StackPilot does                                                          |
| ------------- | ----------------------------------------------------------------------------- |
| **Detect**    | 读取系统、CPU、内存、磁盘、GPU，以及 Python、Git、Docker、WSL 等环境状态。    |
| **Recommend** | 基于规则引擎和场景模板生成应用推荐、适配评分和风险提示。                      |
| **Plan**      | 输出可审查安装计划、审计报告、备份 / 回滚计划和 dry-run 预览。                |
| **Trust**     | 区分核显、独显、虚拟显卡和未知显卡，并通过 `vram_confidence` 标记显存可信度。 |

## 新版本更新

### v0.4.0-alpha · 更准确地识别 GPU

v0.4 增强了 GPU 检测链路，可以区分核显、独显、虚拟显卡和未知显卡。

推荐报告会保留 `primary_gpu`、`gpu_selection_reason` 和 `vram_confidence`，帮助你理解 StackPilot 为什么这样判断显卡能力。

它不会把共享内存误当成独立显存。如果无法确认显存来源，就明确告诉你不确定，而不是假装知道。

![GPU Detection Preview](assets/screenshots/scan-gpu-detection.png)

![Recommendation Preview](assets/screenshots/recommend-comfyui.png)

![Install Plan Preview](assets/screenshots/install-plan-generated.png)

## 可审查安装计划

生成计划：

```bash
python -m stackpilot plan --goal comfyui_starter
```

该命令会输出：

- 安装计划；
- 安装审计报告；
- 备份 / 回滚计划；
- dry-run 预览；
- Markdown / JSON 文件。

当前版本不会真实执行安装。计划里的命令是供你审查的文本，不会由 StackPilot 自动运行。

## Quick Start

```bash
git clone https://github.com/xaopengyo-1010/StackPilot.git
cd StackPilot
pip install -e .
python -m stackpilot scan
python -m stackpilot doctor --goal comfyui_starter
python -m stackpilot plan --goal comfyui_starter
```

当前版本适合开发者、硬件爱好者，以及愿意试用 CLI 的普通用户。你可以先运行 `scan` 看看 StackPilot 能读到哪些本机信息，再用具体目标生成推荐和计划。

## 支持的模板

| 模板                  | 说明               |
| --------------------- | ------------------ |
| `coding_starter`      | 写代码入门         |
| `vibe_coding`         | AI 辅助写代码      |
| `ai_beginner`         | AI 入门体验        |
| `comfyui_starter`     | AI 绘图入门        |
| `local_llm`           | 本地大模型环境规划 |
| `gaming_setup`        | 游戏玩家常用软件   |
| `creator_setup`       | 视频 / 内容创作    |
| `office_productivity` | 办公生产力         |

## 使用指南

检测本机公开系统信息：

```bash
python -m stackpilot scan
```

查看当前可用模板：

```bash
python -m stackpilot list-templates
```

在终端生成推荐结果：

```bash
python -m stackpilot recommend --goal comfyui_starter
```

检测配置并生成 Markdown / JSON 推荐报告：

```bash
python -m stackpilot doctor --goal comfyui_starter
```

生成可审查安装计划、审计报告、备份 / 回滚计划和 dry-run 预览：

```bash
python -m stackpilot plan --goal comfyui_starter
```

## 安全边界

| 当前版本会做         | 当前版本不会做                   |
| -------------------- | -------------------------------- |
| 生成推荐报告         | 自动安装软件                     |
| 生成可审查安装计划   | 下载安装包                       |
| 生成安装审计说明     | 执行 `winget install`            |
| 生成 dry-run 预览    | 执行 PowerShell 安装脚本         |
| 生成备份 / 回滚计划  | 修改 PATH / 环境变量 / 注册表    |
| 标记风险和不确定信息 | 创建真实系统还原点或删除用户文件 |
| 保持本地 CLI 工作流  | 调用真实 LLM API                 |

StackPilot 的目标是降低风险，而不是假装风险不存在。

它会尽量给出可审查、可解释、可回退的计划，但不承诺 100% 安全，也不承诺 100% 回滚。

## 开发

安装开发依赖并运行测试：

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

常用验证命令：

```bash
python -m stackpilot scan
python -m stackpilot list-templates
python -m stackpilot recommend --goal comfyui_starter
python -m stackpilot doctor --goal comfyui_starter
python -m stackpilot plan --goal comfyui_starter
```

## 反馈与贡献

欢迎通过 Issue 或 Pull Request 参与改进。

适合反馈的内容包括：

- 硬件检测不准确；
- GPU / 核显 / 独显 / 虚拟显卡识别异常；
- 推荐结果不符合实际使用目标；
- 安装计划里有来源、风险或回滚信息需要补充；
- 模板、规则、文档或测试可以继续改进。

v0.4 尤其欢迎不同电脑的 GPU / 核显 / 独显 / 虚拟显卡检测反馈。

## License

StackPilot is released under the [MIT License](LICENSE).
